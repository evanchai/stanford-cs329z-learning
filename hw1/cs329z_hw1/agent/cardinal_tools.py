"""Problem 8 (cardinal): the Cardinal toolset.

The four email tools wrap the Part 1 code. The other six are placeholders until
their problems (9, 10, 12, 13): they are listed for the model, and calling one
returns a tool_error that says it is not built yet.

Nothing here reads the email archive when a session is created: the archive and
its BM25 index load the first time an email tool runs (shared by all sessions).
"""
from __future__ import annotations

import threading

from cs329z_hw1.agent.terminal import DESCRIPTION as TERMINAL_DESCRIPTION, Terminal
from cs329z_hw1.cardinal import cardinal_spec
from cs329z_hw1.types import ToolSpec

_lock = threading.Lock()
_state: dict = {}


def _archive():
    """(emails, id -> email, BM25 index), built once on first use."""
    with _lock:
        if "index" not in _state:
            from cs329z_hw1.data import email_text, load_emails
            from cs329z_hw1.pipelines.bm25 import BM25Index

            emails = load_emails()
            _state["emails"] = emails
            _state["by_id"] = {e["id"]: e for e in emails}
            _state["index"] = BM25Index([email_text(e) for e in emails])
        return _state["emails"], _state["by_id"], _state["index"]


def _docs():
    """The document index (Problem 9), built once on first use."""
    with _lock:
        if "docs" not in _state:
            from cs329z_hw1.data import load_docs
            from cs329z_hw1.pipelines.docs import DocIndex

            _state["docs"] = DocIndex(load_docs())
        return _state["docs"]


def search_docs(query: str, k: int = 10) -> str:  # v2 (Ning): top 10 by default
    hits = _docs().search(query, k)
    if not hits:
        return "No documents match that query."
    return "\n\n".join(
        f"[{n}] {h['doc_id']} | {h['title']} | dated {h['date']} | section: {h['section']} | "
        f"lines {h['start_line']}-{h['end_line']} of {h['total_lines']}\n{h['snippet']}"
        for n, h in enumerate(hits, 1))


def read_doc(doc_id: str, start_line: int = 1) -> str:
    w = _docs().read(doc_id, start_line)
    more = (f"\n[continue with start_line={w['end_line'] + 1}]" if w["end_line"] < w["total_lines"] else "\n[end of document]")
    return (f"{doc_id} | dated {w['date']} | section: {w['section']} | "
            f"lines {w['start_line']}-{w['end_line']} of {w['total_lines']}\n{w['text']}{more}")


def _search(query: str, k: int = 5) -> list[dict]:
    emails, _, index = _archive()
    return [emails[d] for d, _ in index.search(query, k)]


def _line(e: dict) -> str:
    """Ning: id, sender, subject only (plus the date); read_email gives the full text."""
    return f"{e['id']} | {str(e.get('date'))[:10]} | from {e.get('from')} | {e.get('subject') or '(no subject)'}"


def _not_built(name: str):
    def fn(**_):
        raise NotImplementedError(f"{name} is not built yet.")
    return fn


def cardinal_toolset(config, lm) -> list[ToolSpec]:
    aux = config.aux_lm if config.aux_lm is not None else lm  # tools use aux_lm, not the agent's lm

    def search_emails(query: str, k: int = 5) -> str:
        hits = _search(query, k)
        if not hits:
            return "No emails match that query."
        return "\n".join(_line(e) for e in hits)

    def read_email(email_id: str) -> str:
        _, by_id, _ = _archive()
        e = by_id.get(email_id)
        if e is None:
            raise LookupError(f"No email with id {email_id}.")
        body = str(e.get("body") or "")
        if len(body) > 6000:
            body = body[:6000] + f"\n[... {len(body) - 6000} more characters]"
        return (f"id: {e['id']}\ndate: {e.get('date')}\nfrom: {e.get('from')}\nto: {', '.join(e.get('to') or [])}\n"
                f"subject: {e.get('subject')}\n\n{body}")

    def email_qa(question: str) -> str:
        from cs329z_hw1.pipelines.email_qa import run_email_qa

        r = run_email_qa(question, _search, aux)
        if not r["answer"]:
            return "No answer found in the archive."
        return f"Answer: {r['answer']}\nSupporting emails: {', '.join(r['support']) or '(none)'}"

    def daily_digest(date: str) -> str:
        from cs329z_hw1.data import emails_on
        from cs329z_hw1.pipelines.digest import run_daily_digest

        return run_daily_digest(emails_on(date), aux)

    specs = [
        cardinal_spec("search_emails", "Search the 2001 email archive by keywords (BM25: use names and "
                      "distinctive words). Returns one line per email: id, date, sender, subject. "
                      "Use read_email to read one in full.",
                      search_emails),
        cardinal_spec("read_email", "Read one email of the archive in full, by its id (e.g. em-01234).", read_email),
        cardinal_spec("email_qa", "Answer a factual question about the 2001 email archive; it searches and reads "
                      "emails itself (up to 3 searches) and returns the answer with supporting email ids.", email_qa),
        cardinal_spec("daily_digest", "Summarize the emails of one day of the archive (date YYYY-MM-DD): "
                      "the urgent items, by company, project or site.", daily_digest),
        cardinal_spec("search_docs", "Search the Cardinal Energy company documents (policies, handbook, org "
                      "chart, product and engineering docs, announcements). Returns the 10 best-matching short passages "
                      "(k=10 unless you pass another k) with their doc_id and line numbers; use read_doc to read around one.", search_docs),
        cardinal_spec("read_doc", "Read a short window of one Cardinal Energy document by doc_id, starting at "
                      "start_line (default 1). The result says which start_line continues it.", read_doc),
        cardinal_spec("run_terminal", TERMINAL_DESCRIPTION, Terminal(config)),
    ]
    return specs + session_tools(config, cardinal=True, aux=aux)


def session_tools(config, cardinal: bool = False, aux=None) -> list[ToolSpec]:
    """ask_user when there is a user; remember/recall when there is a memory dir (always listed for Cardinal)."""
    from cs329z_hw1.agent.memory import MemoryStore

    out = []
    store = MemoryStore(config.memory_dir, aux) if config.memory_dir is not None else None
    if cardinal or store is not None:
        def remember(fact: str) -> str:
            if store is None:
                raise RuntimeError("Memory is not enabled in this session, so nothing was saved.")
            return store.remember(fact)

        def recall(query: str) -> str:
            return store.recall(query) if store is not None else "Memory is not enabled in this session."

        out.append(cardinal_spec("remember", "Save one fact about the user (a full sentence) so later sessions "
                                 "know it. A corrected fact replaces the old one.", remember))
        out.append(cardinal_spec("recall", "Search the facts remembered about this user in earlier sessions.", recall))
    if cardinal or config.user is not None:
        def ask_user(question: str) -> str:  # Problem 13
            if config.user is None:
                raise RuntimeError("No user is available to answer questions in this session.")
            return str(config.user.ask(question))

        out.append(cardinal_spec("ask_user", "Ask the user a clarifying question and wait for the answer. Use it "
                                 "when a request is ambiguous and a wrong guess would matter (e.g. which of two "
                                 "documents, which date, which team), before acting.", ask_user))
    return out
