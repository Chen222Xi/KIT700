# app.py — Minimal Discovery V2 query script
import os, sys, json
from dotenv import load_dotenv
from ibm_watson import DiscoveryV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

load_dotenv()  # Load .env if present

# Prefer environment variables; fall back logic can be added if needed
API_KEY  = os.getenv("DISCOVERY_API_KEY")
URL      = os.getenv("DISCOVERY_URL")               # e.g., https://api.au-syd.discovery.watson.cloud.ibm.com
PROJECT  = os.getenv("DISCOVERY_PROJECT_ID")
COLS_RAW = os.getenv("DISCOVERY_COLLECTION_IDS", "")  # Comma-separated list; empty = search the whole project
COL_IDS  = [s.strip() for s in COLS_RAW.split(",") if s.strip()]

# Initialize Discovery client
auth = IAMAuthenticator(API_KEY)
discovery = DiscoveryV2(version="2023-03-31", authenticator=auth)
discovery.set_service_url(URL)

def run_wd_query(query: str, count: int = 5, passages_count: int = 5) -> dict:
    """Query Discovery V2 and return a compact JSON-friendly result."""
    kwargs = dict(
        project_id=PROJECT,
        natural_language_query=query,
        count=count,
        passages={"enabled": True, "count": passages_count},
    )
    if COL_IDS:
        kwargs["collection_ids"] = COL_IDS

    res = discovery.query(**kwargs).get_result()

    # Prefer top-level 'passages' (official structure); fall back to result text/title if missing
    snippets = []
    for p in res.get("passages", []):
        if p.get("passage_text"):
            snippets.append({"text": p["passage_text"], "document_id": p.get("document_id")})

    if not snippets:
        for r in res.get("results", []):
            txt = ""
            # Some responses include per-result 'document_passages'; use the first passage if available
            dp = r.get("document_passages") or []
            if dp and isinstance(dp, list):
                txt = dp[0].get("passage_text", "") or ""
            if not txt:
                # Otherwise fall back to the fulltext or extracted title
                txt = r.get("text") or r.get("extracted_metadata", {}).get("title", "")
            if txt:
                snippets.append({"text": txt, "collection_id": r.get("collection_id")})

    return {"snippets": snippets, "total": res.get("matching_results", 0)}

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "timetable exam dates"
    out = run_wd_query(q, count=5, passages_count=5)
    print(json.dumps(out, ensure_ascii=False, indent=2))
