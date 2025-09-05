# djv3.py 
# sentinel: djv3 2025-09-04 12:35

import re, requests
from typing import Dict, Any, List
from requests.auth import HTTPBasicAuth
from ibm_watsonx_orchestrate.agent_builder.tools import tool
from ibm_watsonx_orchestrate.run import connections
from ibm_watsonx_orchestrate.agent_builder.connections import ExpectedCredentials, ConnectionType

UNIT_RE = re.compile(r"\b([A-Z]{3}\d{3})\b", re.I)
SEM_RE = re.compile(r"\b(?:semester|sem|s)\s*([12])\b", re.I)

def _find_unit_semester(text: str):
    unit = sem = None
    if text:
        m = UNIT_RE.search(text); unit = m.group(1).upper() if m else None
        s = SEM_RE.search(text); sem = s.group(1) if s else None
    return unit, sem

def _trim(s: str, n: int = 400) -> str:
    if not s: return ""
    s = s.strip()
    return s if len(s) <= n else s[:n].rstrip() + " …"

@tool(
    name="discovery_json_v3_clean",
    description="Query Discovery JSON project (clean v3) using secure connection credentials.",
    expected_credentials=[ExpectedCredentials(
        app_id="discovery_cfg", 
        type=ConnectionType.KEY_VALUE
    )]
)
def discovery_json_v3_clean(userQuery: str = "", unit: str = "", semester: str = "",
                           top_k: int = 2, passage_len: int = 400) -> Dict[str, Any]:
    hdr = "tool=discovery_json_v3_clean; sentinel=djv3 2025-09-04 12:35"
    
    #尝试从连接读取配置，如果失败则使用环境变量
    cfg = {}
    connection_error = None
    
    try:
        #通过连接读取所有配置（安全方式）
        cfg = connections.key_value("discovery_cfg")
        debug_info = f"Connection keys: {list(cfg.keys()) if cfg else 'None'}"
        
    except Exception as e:
        connection_error = str(e)
        #不行就试试使用环境变量，但好像也不行
        import os
        cfg = {
            "DISCOVERY_URL": os.getenv("DISCOVERY_URL", ""),
            "DISCOVERY_APIKEY": os.getenv("DISCOVERY_APIKEY", ""),
            "DISCOVERY_VERSION": os.getenv("DISCOVERY_VERSION", ""),
            "DISCOVERY_PROJECT_ID_JSON": os.getenv("DISCOVERY_PROJECT_ID_JSON", ""),
            "DISCOVERY_COLLECTION_ID_JSON": os.getenv("DISCOVERY_COLLECTION_ID_JSON", "")
        }
        debug_info = f"Using env variables. Connection error: {connection_error}"
    
    need = ["DISCOVERY_URL","DISCOVERY_APIKEY","DISCOVERY_VERSION",
            "DISCOVERY_PROJECT_ID_JSON","DISCOVERY_COLLECTION_ID_JSON"]
    miss = [k for k in need if not cfg.get(k)]
    if miss:
        return {"answer": f"{hdr}\nConfiguration error: Missing env: {', '.join(miss)}\nDebug: {debug_info}"}
    
    if not unit or not semester:
        u2, s2 = _find_unit_semester(userQuery)
        unit = (unit or u2 or "").upper()
        semester = (semester or s2 or "")
    
    url = f"{cfg['DISCOVERY_URL']}/v2/projects/{cfg['DISCOVERY_PROJECT_ID_JSON']}/query?version={cfg['DISCOVERY_VERSION']}"
    body: Dict[str, Any] = {
        "collection_ids": [cfg["DISCOVERY_COLLECTION_ID_JSON"]],
        "count": int(top_k) if top_k else 2,
        "return": ["document_id","document_passages","unit","semester","section","subsection"],
        "passages": {"enabled": True, "per_document": True, "max_per_document": 1,
                    "characters": int(passage_len) if passage_len else 400},
        "spelling_suggestions": False,
        "table_results": {"enabled": False, "count": 0}
    }
    if unit:
        body["filter"] = f'unit:"{unit}"'
    nlq: List[str] = []
    if userQuery: nlq.append(userQuery)
    if semester in ("1","2"):
        nlq += [f"Semester{semester}", f"Semester {semester}"]
    body["natural_language_query"] = " ".join(nlq) or "unit outline"
    
    try:
        r = requests.post(url, json=body,
                         auth=HTTPBasicAuth("apikey", cfg["DISCOVERY_APIKEY"]),
                         headers={"Content-Type":"application/json"}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"answer": f"{hdr}\nDiscovery request failed: {e}"}
    
    results = data.get("results", [])
    if not results:
        cond = ", ".join([f"unit={unit}" if unit else "", f"semester={semester}" if semester else ""]).strip(", ")
        return {"answer": f"{hdr}\nNo results found for {cond or 'your query'}."}
    
    items = []
    for res in results:
        head = " / ".join([v for v in [res.get("unit"),res.get("semester"),
                          res.get("section"),res.get("subsection")] if v])
        passage = next((p.get("passage_text") for p in res.get("document_passages", [])
                       if p.get("passage_text")), "(No passage excerpt returned.)")
        items.append(f"{head}\n{_trim(passage, int(passage_len) if passage_len else 400)}")
    
    return {"answer": f"{hdr}\n" + "\n\n---\n\n".join(items)}