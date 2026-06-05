# evaluations/evaluate.py
"""Agent 评估脚本"""
import json
import time
from backend.src.agent.assistant import assistant


async def run_evaluation(test_dataset_path: str):
    """运行评估"""
    with open(test_dataset_path) as f:
        test_cases = json.load(f)

    results = []
    for i, case in enumerate(test_cases):
        print(f"\n评估 [{i+1}/{len(test_cases)}]: {case['query'][:50]}...")

        start = time.time()
        result = await assistant.chat(
            message=case["query"],
            thread_id=f"eval-{i}",
        )
        elapsed = time.time() - start

        # 检查关键词
        content_lower = result["content"].lower()
        keyword_hits = [
            kw for kw in case["expected_keywords"]
            if kw.lower() in content_lower
        ]

        score = len(keyword_hits) / len(case["expected_keywords"])
        results.append({
            "query": case["query"],
            "score": score,
            "keyword_hits": keyword_hits,
            "time": elapsed,
        })

        print(f"  得分: {score:.0%}, 命中关键词: {keyword_hits}, 耗时: {elapsed:.2f}s")

    # 汇总
    avg_score = sum(r["score"] for r in results) / len(results)
    avg_time = sum(r["time"] for r in results) / len(results)
    print(f"\n{'='*50}")
    print(f"评估完成: {len(results)} 个用例")
    print(f"平均得分: {avg_score:.1%}")
    print(f"平均耗时: {avg_time:.2f}s")
    print(f"{'='*50}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_evaluation("evaluations/test_dataset.json"))
