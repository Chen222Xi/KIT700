# app.py
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from dotenv import load_dotenv
import os, sys

# 1) 读取 .env
load_dotenv()

API_KEY = os.getenv("DISCOVERY_API_KEY")
URL = os.getenv("DISCOVERY_URL")  # 形如：https://api.eu-gb.discovery.watson.cloud.ibm.com/instances/xxxx
PROJECT_ID = os.getenv("DISCOVERY_PROJECT_ID")
# 可选：如果你只想查某个 collection，就填；不填则查项目下所有可用集合
COLLECTION_ID = os.getenv("DISCOVERY_COLLECTION_ID")

if not (API_KEY and URL and PROJECT_ID):
    raise RuntimeError("Missing env: DISCOVERY_API_KEY / DISCOVERY_URL / DISCOVERY_PROJECT_ID")

# 2) 初始化客户端
authenticator = IAMAuthenticator(API_KEY)
discovery = DiscoveryV2(version="2023-03-31", authenticator=authenticator)
discovery.set_service_url(URL)

# 3) 查询函数
def run_wd_query(query: str, num_results: int = 3):
    kwargs = dict(
        project_id=PROJECT_ID,
        natural_language_query=query,
        count=num_results,
        passages={"enabled": True, "count": num_results},  # 打开 passages
    )
    if COLLECTION_ID:
        kwargs["collection_ids"] = [COLLECTION_ID]

    result = discovery.query(**kwargs).get_result()

    # 尝试优先拿 passages；没有就退回到文档 text/标题
    snippets = []
    for r in result.get("results", []):
        if r.get("document_passages"):
            snippets.append(r["document_passages"][0].get("passage_text", ""))
        else:
            snippets.append(r.get("text") or r.get("extracted_metadata", {}).get("title", ""))

    return snippets, result

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "tell me about Tasmania courses"
    snippets, _raw = run_wd_query(q, num_results=3)
    print("\n".join(f"- {s}" for s in snippets if s))
