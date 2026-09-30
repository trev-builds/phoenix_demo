from agent import parse_final

def _num(s):
    try:
        return float(str(s).replace(",", ""))
    except (TypeError, ValueError):
        return None

def score_answer(answer_text: str, expected, tolerance: float, kind: str) -> dict:
    got = parse_final(answer_text)
    if got is None:
        return {"score": 0.0, "label": "no_final_line", "explanation": "no FINAL line found"}
    if kind == "yesno":
        ok = got == str(expected).lower()
        return {"score": float(ok), "label": "correct" if ok else "wrong", "explanation": f"got {got}, expected {expected}"}
    g, e = _num(got), float(expected)
    if g is None:
        return {"score": 0.0, "label": "unparseable", "explanation": f"got {got!r}"}
    ok = abs(g - e) <= max(tolerance, 0.005 * abs(e))
    return {"score": float(ok), "label": "correct" if ok else "wrong", "explanation": f"got {g}, expected {e}"}

# ---- Phoenix evaluators (parameter names are matched by Phoenix) ----
def answer_correct(output, expected) -> dict:
    # Phoenix's dataframe upload stores mixed-type columns as strings, so cast tolerance back to a number
    # Returns score + label + explanation so Phoenix shows *why* an answer is wrong, not just 0
    return score_answer(output["answer"], expected["expected"], float(expected["tolerance"]), expected["kind"])

def tool_calls_used(output) -> float:
    return float(output["tool_calls"])
