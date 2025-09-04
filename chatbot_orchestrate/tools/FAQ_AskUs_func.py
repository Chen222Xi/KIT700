from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

@tool(
  name="FAQ_AskUs_func",
  description=(
    "Search AskUs/FAQ Milvus entries and return the most relevant Q&A items for a user query. "
    "Each entry may include {filename, link, course_code, course_name, sections:{Question, Answer}}. "
    "Inputs: {query: string, top_k: int=5, threshold: float=0.6}. "
    "Output: ranked list with fields {question, answer, link, score}. "
    "Use sections.Question for intent matching and sections.Answer for the final answer span."
  ), 
  permission=ToolPermission.ADMIN
)

def FAQ_AskUs_func(
    query: str,
    passages: list,         # 必须是严格结构的列表（见下方示例）
    top_k: int = 5,
    threshold: float = 0.6
) -> list:
    """
    仅基于给定 passages 重排，返回若干 {question, answer, link, score, filename}。
    期望的 passage 结构示例：
      {
        "filename": "app_answers_detail_a_id_2481_kw_timetable.html",
        "link": "https://askus.utas.edu.au/app/answers/detail/a_id/2481/kw/timetable",
        "course_name": "How do I register for class and see my timetable?",
        "sections": {
          "Question": "How do I register for class and see my timetable?",
          "Answer":   "In MyTimetable, you can plan, preference and register ..."
        }
      }
    """
    import re
    from difflib import SequenceMatcher

    def _norm(s: str) -> str:
        # 统一空白、去特殊空格/零宽字符、转小写
        s = (s or "")
        s = s.replace("\u00A0", " ").replace("\u200B", "")
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    def _dedup_sentences(text: str) -> str:
        # 句级去重，避免 Answer 里重复段落（保持原顺序）
        parts = re.split(r"(?<=[.!?;])\s+|\n+", text or "")
        seen, out = set(), []
        for p in parts:
            t = re.sub(r"\s+", " ", p).strip()
            key = t.lower()
            if t and key not in seen:
                seen.add(key)
                out.append(t)
        return " ".join(out) if out else (text or "")

    def _score_question_answer(q_norm: str, question: str, answer: str) -> float:
        # 主要看 Question 的相似度，加一点 Answer 的覆盖率
        qn = _norm(question)
        an = _norm(answer)
        ratio_q = SequenceMatcher(None, q_norm, qn).ratio()
        q_tokens = set(q_norm.split())
        cover = len(q_tokens & set((qn + " " + an).split())) / max(1, len(q_tokens))
        return 0.8 * ratio_q + 0.2 * cover

    if not isinstance(passages, list) or not passages:
        return []

    q_norm = _norm(query)
    ranked = []

    for p in passages:
        # 严格取字段（缺就当空）
        filename = (p.get("filename") if isinstance(p, dict) else "") or ""
        link = (p.get("link") if isinstance(p, dict) else "") or ""
        sections = (p.get("sections") if isinstance(p, dict) else {}) or {}
        question = (sections.get("Question") or "").strip()
        raw_answer = (sections.get("Answer") or "").strip()

        # 清理重复句
        answer = _dedup_sentences(raw_answer)

        sc = _score_question_answer(q_norm, question, answer)
        ranked.append({
            "question": question,
            "answer": answer,
            "link": link,
            "filename": filename,
            "score": round(sc, 4)
        })

    # 排序、去重（按 link+question），阈值&截断
    ranked.sort(key=lambda x: x["score"], reverse=True)
    seen, out = set(), []
    for r in ranked:
        key = (r["link"], r["question"].lower())
        if key in seen:
            continue
        seen.add(key)
        if r["score"] >= float(threshold):
            out.append(r)
        if len(out) >= max(1, int(top_k)):
            break

    return out
