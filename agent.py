import re
from anthropic import Anthropic
from config import TODAY, MODEL
from tools import DESIGNS

client = Anthropic()

SYSTEM = f"""You answer questions about the user's personal running history using the tools provided.
Today's date is {TODAY.isoformat()} ({TODAY.strftime('%A')}). Weeks run Monday to Sunday. "Last week" means the full Monday-Sunday week before the current week.
Average pace always means total time divided by total distance for the period.
Keep your answer short. End with one final line in exactly this form:
FINAL: <value>
where <value> is a bare number (no units, no commas) in the units the question asks for, or yes/no/june/july when asked for that."""

def run_agent(question: str, design: str = "B_computed", max_turns: int = 8) -> dict:
    d = DESIGNS[design]
    messages = [{"role": "user", "content": question}]
    n_calls = 0
    for _ in range(max_turns):
        resp = client.messages.create(model=MODEL, max_tokens=1024, system=SYSTEM,
                                      tools=d["tools"], messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            text = "".join(b.text for b in resp.content if b.type == "text")
            return {"answer": text, "tool_calls": n_calls}
        results = []
        for b in resp.content:
            if b.type == "tool_use":
                n_calls += 1
                try:
                    out = d["impl"][b.name](**b.input)
                except Exception as e:      # surface tool errors to the model, like a real agent would see them
                    out = f"ERROR: {e}"
                results.append({"type": "tool_result", "tool_use_id": b.id, "content": str(out)})
        messages.append({"role": "user", "content": results})
    return {"answer": "(max turns reached)", "tool_calls": n_calls}

def parse_final(text: str):
    m = re.findall(r"FINAL:\s*(.+)", text or "")
    return m[-1].strip().lower().rstrip(".") if m else None

if __name__ == "__main__":
    import sys
    from phoenix.otel import register
    register(project_name="garmin-run-agent", auto_instrument=True)   # send this run's trace to Phoenix
    design = sys.argv[1] if len(sys.argv) > 1 else "B_computed"
    print(run_agent("How many miles did I run last week? (answer in miles)", design))
