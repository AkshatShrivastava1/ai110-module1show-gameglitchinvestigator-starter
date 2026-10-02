"""Drive the ORIGINAL starter app headlessly and log what happens.

Run against the starter code (commit e931e66):
    git stash; git checkout e931e66 -- app.py
    python evidence/repro_original.py
    git checkout HEAD -- app.py; git stash pop
Uses streamlit.testing.v1.AppTest so the real app.py runs end to end.
"""
from streamlit.testing.v1 import AppTest

APP = "app.py"


def fresh(secret):
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    at.session_state.secret = secret
    return at


def guess(at, value):
    at.text_input[0].set_value(str(value))
    at.button[0].click()   # "Submit Guess"
    at.run()
    hints = [w.value for w in at.warning]
    errs = [e.value for e in at.error]
    info = [i.value for i in at.info]
    print(f"  guess={value!r:6} attempts={at.session_state.attempts} "
          f"score={at.session_state.score} status={at.session_state.status} "
          f"hint={hints} errors={errs}")
    print(f"      info banner -> {info}")
    return at


print("=== Session A: secret=50, Normal ===")
at = fresh(50)
print("  on load:", [i.value for i in at.info])
guess(at, 60)      # attempt counter goes 1 -> 2
guess(at, 40)
guess(at, 9)

print("\n=== Session B: secret=50, guess exactly 50 on an even attempt ===")
at = fresh(50)
guess(at, 50)

print("\n=== Session C: invalid input ===")
at = fresh(50)
guess(at, "abc")
guess(at, "")
print("  history:", at.session_state.history)

print("\n=== Session D: win, then press New Game ===")
at = fresh(50)
at.session_state.attempts = 2  # make next attempt odd (int compare)
guess(at, 50)
at.button[1].click()  # "New Game"
at.run()
print(f"  after New Game: status={at.session_state.status} "
      f"attempts={at.session_state.attempts} score={at.session_state.score} "
      f"history={at.session_state.history}")
print("  messages:", [s.value for s in at.success],
      [e.value for e in at.error])

print("\n=== Session E: Hard difficulty ===")
at = AppTest.from_file(APP, default_timeout=30)
at.run()
at.selectbox[0].set_value("Hard")
at.run()
print("  sidebar:", [c.value for c in at.sidebar.caption])
print("  main banner:", [i.value for i in at.info])
