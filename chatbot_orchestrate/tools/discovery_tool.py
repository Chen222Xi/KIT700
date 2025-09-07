# tools/discovery_tool.py
import os
from typing import List, Optional, Dict, Any
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

# —— 不在导入时抛错；延迟初始化 —— #
_CLIENT = None
_PROJECT = os.getenv("DISCOVERY_PROJECT_ID")

def _get_client() -> DiscoveryV2:
    global _CLIENT
    if _CLIENT is None:
        api = os.getenv("DISCOVERY_API_KEY")
        url = os.getenv("DISCOVERY_URL")  # 只用 https://api.<region>.discovery.watson.cloud.ibm.com
        if not (api and url and _PROJECT):
            # 在被调用时再报错，避免导入阶段失败
            raise ValueError("Missing DISCOVERY_API_KEY / DISCOVERY_URL / DISCOVERY_PROJECT_ID")
        c = DiscoveryV2(version="2023-03-31", authenticator=IAMAuthenticator(api))
        c.set_service_url(url)
        _CLIENT = c
    return _CLIENT

def wd_query(query: str, count: int = 5, collections: Optional[List[str]] = None) -> Dict[str, Any]:
    """Query IBM Watson Discovery and return plain JSON."""
    cli = _get_client()
    kwargs = {
        "project_id": _PROJECT,
        "natural_language_query": query,
        "count": count,
        "passages": {"enabled": True, "count": count},
    }
    if collections:
        kwargs["collection_ids"] = collections

    res = cli.query(**kwargs).get_result()

    snippets: List[Dict[str, Any]] = []
    for p in res.get("passages", []):
        t = p.get("passage_text")
        if t:
            snippets.append({"text": t, "document_id": p.get("document_id")})
    if not snippets:
        for r in res.get("results", []):
            t = (r.get("document_passages") or [{}])[0].get("passage_text") \
                or r.get("text") \
                or r.get("extracted_metadata", {}).get("title", "")
            if t:
                snippets.append({"text": t, "collection_id": r.get("collection_id")})

    return {"snippets": snippets, "total": res.get("matching_results", 0)}

# 可选：本地调试入口，不影响作为 tool 导入
if __name__ == "__main__":
    import sys, json
    q = " ".join(sys.argv[1:]) or "timetable exam dates"
    print(json.dumps(wd_query(q, count=5), ensure_ascii=False, indent=2))
