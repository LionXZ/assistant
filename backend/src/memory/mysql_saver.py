"""MySQL Checkpoint Saver — 替代 SQLite"""
import json
import threading
from contextlib import contextmanager
from typing import Iterator, cast

import pymysql
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    CheckpointMetadata,
    CheckpointTuple,
    SerializerProtocol,
    get_checkpoint_id,
)


class MySQLSaver(BaseCheckpointSaver[str]):
    """MySQL-based checkpoint saver for LangGraph."""

    def __init__(
        self,
        conn: pymysql.Connection,
        *,
        serde: SerializerProtocol | None = None,
    ) -> None:
        super().__init__(serde=serde)
        self.conn = conn
        self.is_setup = False
        self.lock = threading.Lock()

    @classmethod
    def from_config(cls, host: str, port: int, user: str, password: str, database: str, charset: str = "utf8mb4"):
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password or None,
            database=database, charset=charset, autocommit=True,
        )
        return cls(conn)

    def setup(self) -> None:
        if self.is_setup:
            return
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_checkpoints (
                    thread_id VARCHAR(100) NOT NULL,
                    checkpoint_ns VARCHAR(50) NOT NULL DEFAULT '',
                    checkpoint_id VARCHAR(50) NOT NULL,
                    parent_checkpoint_id VARCHAR(50),
                    type VARCHAR(50),
                    checkpoint LONGBLOB,
                    metadata LONGTEXT,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS langgraph_writes (
                    thread_id VARCHAR(100) NOT NULL,
                    checkpoint_ns VARCHAR(50) NOT NULL DEFAULT '',
                    checkpoint_id VARCHAR(50) NOT NULL,
                    task_id VARCHAR(50) NOT NULL,
                    idx INT NOT NULL,
                    channel VARCHAR(100) NOT NULL,
                    type VARCHAR(50),
                    value LONGBLOB,
                    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        self.is_setup = True

    @contextmanager
    def cursor(self, transaction: bool = True) -> Iterator[pymysql.cursors.Cursor]:
        with self.lock:
            self.setup()
            cur = self.conn.cursor()
            try:
                yield cur
            finally:
                if transaction:
                    self.conn.commit()
                cur.close()

    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        with self.cursor(transaction=False) as cur:
            if checkpoint_id := get_checkpoint_id(config):
                cur.execute(
                    "SELECT thread_id, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata "
                    "FROM langgraph_checkpoints "
                    "WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s",
                    (str(thread_id), checkpoint_ns, checkpoint_id),
                )
            else:
                cur.execute(
                    "SELECT thread_id, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata "
                    "FROM langgraph_checkpoints "
                    "WHERE thread_id = %s AND checkpoint_ns = %s ORDER BY checkpoint_id DESC LIMIT 1",
                    (str(thread_id), checkpoint_ns),
                )

            value = cur.fetchone()
            if not value:
                return None

            (
                t_id, ckpt_id, parent_ckpt_id,
                ckpt_type, ckpt_bytes, meta_json,
            ) = value

            if not get_checkpoint_id(config):
                config = {
                    "configurable": {
                        "thread_id": t_id,
                        "checkpoint_ns": checkpoint_ns,
                        "checkpoint_id": ckpt_id,
                    }
                }

            # pending writes
            cur.execute(
                "SELECT task_id, channel, type, value FROM langgraph_writes "
                "WHERE thread_id = %s AND checkpoint_ns = %s AND checkpoint_id = %s "
                "ORDER BY task_id, idx",
                (str(config["configurable"]["thread_id"]), checkpoint_ns, str(config["configurable"]["checkpoint_id"])),
            )
            writes_rows = cur.fetchall()

            return CheckpointTuple(
                config,
                self.serde.loads_typed((ckpt_type, ckpt_bytes)),
                cast(CheckpointMetadata, json.loads(meta_json) if meta_json else {}),
                (
                    {"configurable": {"thread_id": t_id, "checkpoint_ns": checkpoint_ns, "checkpoint_id": parent_ckpt_id}}
                    if parent_ckpt_id else None
                ),
                [
                    (task_id, channel, self.serde.loads_typed((wt, wv)))
                    for task_id, channel, wt, wv in writes_rows
                ],
            )

    def put(
        self,
        config: RunnableConfig,
        checkpoint,
        metadata,
        new_versions,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")

        ckpt_type, ckpt_bytes = self.serde.dumps_typed(checkpoint)
        meta_json = json.dumps(metadata, default=str, ensure_ascii=False) if metadata else None

        with self.cursor() as cur:
            cur.execute(
                "INSERT INTO langgraph_checkpoints "
                "(thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    str(thread_id),
                    checkpoint_ns,
                    checkpoint["id"],
                    config["configurable"].get("checkpoint_id"),
                    ckpt_type,
                    ckpt_bytes,
                    meta_json,
                ),
            )

        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": checkpoint_ns,
                "checkpoint_id": checkpoint["id"],
            }
        }

    def put_writes(
        self,
        config: RunnableConfig,
        writes,
        task_id: str,
    ) -> RunnableConfig:
        thread_id = config["configurable"]["thread_id"]
        checkpoint_ns = config["configurable"].get("checkpoint_ns", "")
        checkpoint_id = config["configurable"]["checkpoint_id"]

        with self.cursor() as cur:
            for idx, (channel, value) in enumerate(writes):
                wt, wb = self.serde.dumps_typed(value)
                cur.execute(
                    "INSERT INTO langgraph_writes "
                    "(thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (str(thread_id), checkpoint_ns, checkpoint_id, task_id, idx, channel, wt, wb),
                )

        return config

    def delete_thread(self, thread_id: str) -> None:
        with self.cursor() as cur:
            cur.execute("DELETE FROM langgraph_checkpoints WHERE thread_id = %s", (thread_id,))
            cur.execute("DELETE FROM langgraph_writes WHERE thread_id = %s", (thread_id,))

    # ── async 封装 (LangGraph 优先调 async 方法) ────
    async def aget_tuple(self, config: RunnableConfig):
        import asyncio
        return await asyncio.to_thread(self.get_tuple, config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        import asyncio
        return await asyncio.to_thread(self.put, config, checkpoint, metadata, new_versions)

    async def aput_writes(self, config, writes, task_id):
        import asyncio
        await asyncio.to_thread(self.put_writes, config, writes, task_id)

    async def adelete_thread(self, thread_id: str):
        import asyncio
        await asyncio.to_thread(self.delete_thread, thread_id)
