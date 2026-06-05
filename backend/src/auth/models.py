"""MySQL 用户/会话/消息模型"""
import pymysql
import bcrypt
from backend.src.config.settings import settings


def get_db():
    return pymysql.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD or None,
        database=settings.DB_NAME,
        charset=settings.DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _init_tables():
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                username    VARCHAR(30) UNIQUE NOT NULL,
                email       VARCHAR(100) UNIQUE NOT NULL,
                password    VARCHAR(255) NOT NULL,
                is_admin    TINYINT DEFAULT 0,
                email_verified TINYINT DEFAULT 0,
                verification_code VARCHAR(6),
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                thread_id   VARCHAR(100) NOT NULL,
                title       VARCHAR(50) DEFAULT '新会话',
                updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_user_thread (user_id, thread_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                user_id     INT NOT NULL,
                thread_id   VARCHAR(100) NOT NULL,
                role        VARCHAR(20) NOT NULL,
                content     TEXT NOT NULL,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_thread (user_id, thread_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    conn.close()


_init_tables()


# ---- 用户 ----

def create_user(username: str, email: str, password: str) -> dict | None:
    """创建用户，admin 为系统保留用户名"""
    if username.lower() == "admin":
        return None  # admin 是系统保留账户
    conn = get_db()
    try:
        import random
        code = str(random.randint(100000, 999999))
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (username, email, password, verification_code) VALUES (%s, %s, %s, %s)",
                (username, email, hashed, code),
            )
            return {"id": cur.lastrowid, "username": username, "email": email, "verification_code": code}
    except pymysql.IntegrityError:
        return None
    finally:
        conn.close()


def verify_user(username: str, password: str) -> dict | None:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row["password"].encode()):
        if not row.get("email_verified") and username.lower() != "admin":
            return None  # 邮箱未验证
        return row
    return None


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    conn.close()
    return row


# ---- 会话 ----

def list_user_sessions(user_id: int) -> list[dict]:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT thread_id, title, updated_at FROM sessions WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,),
        )
        rows = cur.fetchall()
    conn.close()
    return rows


def upsert_session(user_id: int, thread_id: str, title: str = None):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO sessions (user_id, thread_id, title) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE title = COALESCE(%s, title), updated_at = NOW()",
            (user_id, thread_id, title, title),
        )
    conn.close()


def delete_session(user_id: int, thread_id: str):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sessions WHERE user_id = %s AND thread_id = %s", (user_id, thread_id))
        cur.execute("DELETE FROM messages WHERE user_id = %s AND thread_id = %s", (user_id, thread_id))
    conn.close()


# ---- 消息 ----

def save_message(user_id: int, thread_id: str, role: str, content: str):
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO messages (user_id, thread_id, role, content) VALUES (%s, %s, %s, %s)",
            (user_id, thread_id, role, content),
        )
    conn.close()


def get_session_messages(user_id: int, thread_id: str) -> list[dict]:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT role, content FROM messages WHERE user_id = %s AND thread_id = %s ORDER BY id ASC",
            (user_id, thread_id),
        )
        rows = cur.fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


# ---- 邮箱验证 ----

def verify_email(user_id: int, code: str) -> bool:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT verification_code FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    if row and row["verification_code"] == code:
        conn.cursor().execute("UPDATE users SET email_verified=1, verification_code=NULL WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_user_verification_code(user_id: int) -> str | None:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT email, verification_code FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    conn.close()
    return row if row else None


def is_admin_user(user_id: int) -> bool:
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT is_admin FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
    conn.close()
    return bool(row and row["is_admin"])


# ---- 密码重置 ----

def set_reset_token(email: str) -> dict | None:
    """生成重置码，返回用户信息或 None"""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, email FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
    if not row:
        conn.close()
        return None
    import random
    code = str(random.randint(100000, 999999))
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET reset_token = %s WHERE id = %s", (code, row["id"]))
    conn.commit()
    conn.close()
    return {"id": row["id"], "email": row["email"], "reset_token": code}


def reset_password(email: str, code: str, new_password: str) -> bool:
    """验证重置码并更新密码"""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT id, reset_token FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
    if not row or row["reset_token"] != code:
        conn.close()
        return False
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET password = %s, reset_token = NULL, email_verified = 1 WHERE id = %s", (hashed, row["id"]))
    conn.commit()
    conn.close()
    return True
