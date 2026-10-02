"""Replay the bug scenarios against the FIXED app.py and log the results.

Run: python evidence/verify_fixed.py
"""
import json
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

APP = "app.py"


def fresh(secret, difficulty=None):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    if difficulty:
        at.selectbox[0].set_value(difficulty)
        at.run()
    at.session_state.secret = secret
    return at


def guess(at, value):
    at.text_input[0].set_value(str(value))
    at.button[0].click()   # "Submit Guess"
    at.run()
    print(f"  guess={value!r:6} attempts={at.session_state.attempts} "
          f"score={at.session_state.score} status={at.session_state.status} "
          f"hint={[w.value for w in at.warning]} "
          f"errors={[e.value for e in at.error]}")
    print(f"      info banner -> {[i.value for i in at.info]}")
    return at


print("=== Session A: secret=50, Normal (bugs 1, 2, 3, 4) ===")
at = fresh(50)
print("  on load:", [i.value for i in at.info])
guess(at, 60)
guess(at, 40)
guess(at, 9)

print("\n=== Session B: first-try win (bug 8) ===")
at = fresh(50)
guess(at, 50)
print("  success:", [s.value for s in at.success])

print("\n=== Session C: invalid / out-of-range input (bugs 7, 9) ===")
at = fresh(50)
for bad in ["abc", "", "3.5", "-5", "500"]:
    guess(at, bad)
print("  history:", at.session_state.history)

print("\n=== Session D: win, then press New Game (bug 5) ===")
at = fresh(50)
guess(at, 50)
at.button[1].click()  # "New Game"
at.run()
print(f"  after New Game: status={at.session_state.status} "
      f"attempts={at.session_state.attempts} score={at.session_state.score} "
      f"history={at.session_state.history}")
print("  banner:", [i.value for i in at.info])
guess(at, at.session_state.secret)

print("\n=== Session E: Hard difficulty (bug 6) ===")
at = fresh(150, "Hard")
print("  sidebar:", [c.value for c in at.sidebar.caption])
print("  main banner:", [i.value for i in at.info])
print("  secret in range:", 1 <= at.session_state.secret <= 200)

print("\n=== Session F: run out of attempts on Easy ===")
at = fresh(10, "Easy")
for g in [1, 2, 3, 4, 5, 6]:
    guess(at, g)
print("  end message:", [e.value for e in at.error])

print("\n=== Session G: hot/cold hints, history table, high score ===")
hs = Path(__file__).resolve().parent.parent / "high_scores.json"
hs.unlink(missing_ok=True)
at = fresh(50)
for g in [90, 60, 52, 50]:
    guess(at, g)
print("  history table:", at.table[0].value.to_dict("records"))
print("  success:", [s.value for s in at.success])
print("  high_scores.json:", json.loads(hs.read_text()))
at.run()
print("  sidebar high scores:", [m.value for m in at.sidebar.markdown])
hs.unlink(missing_ok=True)
