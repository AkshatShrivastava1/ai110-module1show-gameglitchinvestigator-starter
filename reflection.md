# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first time I ran the game it looked fine (title, sidebar, input box, debug expander) but it was not actually playable. With the secret pinned to 50, a guess of 60 told me to "Go HIGHER" and a guess of 40 told me to "Go LOWER", so the hints pointed the wrong way. The "Attempts left" banner started at 7 on Normal even though the sidebar said 8, and it did not change after my first guess. After winning, the New Game button did nothing: the game stayed stuck on "You already won." Hard mode used a range of 1 to 50, which is easier than Normal, while the banner still said "between 1 and 100".

I drove the original `app.py` headlessly with Streamlit's `AppTest` (`evidence/repro_original.py`), so every row below comes from a real run. Full output is in `evidence/repro_original_output.txt`:

```
=== Session A: secret=50, Normal ===
  on load: ['Guess a number between 1 and 100. Attempts left: 7']
  guess=60     attempts=2 score=5 status=playing hint=['Go HIGHER!'] errors=[]
      info banner -> ['Guess a number between 1 and 100. Attempts left: 7']
  guess=40     attempts=3 score=0 status=playing hint=['Go LOWER!'] errors=[]
      info banner -> ['Guess a number between 1 and 100. Attempts left: 6']
  guess=9      attempts=4 score=5 status=playing hint=['Go HIGHER!'] errors=[]
=== Session C: invalid input ===
  guess='abc'  attempts=2 score=0 status=playing hint=[] errors=['That is not a number.']
  guess=''     attempts=3 score=0 status=playing hint=[] errors=['Enter a guess.']
  history: ['abc', '']
=== Session D: win, then press New Game ===
  guess=50     attempts=3 score=60 status=won hint=['Correct!'] errors=[]
  after New Game: status=won attempts=0 score=60 history=[50]
  messages: ['You already won. Start a new game to play again.'] []
=== Session E: Hard difficulty ===
  sidebar: ['Range: 1 to 50', 'Attempts allowed: 5']
  main banner: ['Guess a number between 1 and 100. Attempts left: 4']
```

**Bug Reproduction Log**

| # | Input | Expected Behavior | Actual Behavior | Console Output / Error | Code-level cause |
|---|-------|-------------------|-----------------|------------------------|------------------|
| 1 | Secret 50, guess 60 (or 40) | "Too High" → hint says go **lower** (40 → go **higher**) | 60 shows "📈 Go HIGHER!", 40 shows "📉 Go LOWER!" | `hint=['📈 Go HIGHER!']` | `check_guess` returns the wrong message string for each branch (messages swapped) |
| 2 | Secret 50, guess 9 on the 2nd guess (even attempt) | Outcome "Too Low" | Outcome "Too High" (score goes **up** by 5) | `guess=9 ... score=5` | `app.py` casts the secret to `str` on every even attempt, so `check_guess` hits `TypeError` and falls back to string comparison, where `"9" > "50"` |
| 3 | Secret 50, guess 60 on an even attempt | Wrong guess never adds points | Score goes from 0 to +5 | `guess=60 attempts=2 score=5` | `update_score` adds 5 for "Too High" when `attempt_number % 2 == 0` |
| 4 | Fresh game on Normal (8 attempts) | Banner shows 8 attempts left, drops to 7 after one guess | Shows 7 on load and still 7 after the first guess | `on load: ... Attempts left: 7` | `attempts` initialised to 1, and the `st.info` banner is drawn **before** the submit handler updates the counter |
| 5 | Win, then click "New Game" | Fresh round: status playing, score 0, empty history | Still stuck: "You already won", score 60, history `[50]` | `after New Game: status=won attempts=0` | New Game handler only resets `attempts` and `secret`, never `status`/`score`/`history` |
| 6 | Select "Hard" difficulty | Harder than Normal (wider range); banner shows the real range | Range is 1 to 50 (easier than Normal), banner still says 1 to 100; New Game always draws from 1 to 100 | `sidebar: ['Range: 1 to 50' ...]`, `main banner: ['... between 1 and 100 ...']` | `get_range_for_difficulty` returns `(1, 50)` for Hard; banner text and New Game `randint(1, 100)` are hardcoded |
| 7 | Type `abc` or leave blank, click Submit | Error shown, attempt **not** consumed, not added to history | Attempt consumed and junk added to history | `attempts=2 ... errors=['That is not a number.']`, `history: ['abc', '']` | `attempts += 1` and `history.append(raw_guess)` run before the input is validated |
| 8 | Win on the first try | 100 points for a first-try win (score should reward fewer attempts) | Only 80 points max, because the counter already starts at 1 and the formula adds 1 again | `guess=50 attempts=2 score=70` | `update_score` uses `100 - 10 * (attempt_number + 1)` on top of the off-by-one counter |
| 9 | Guess `-5` or `500` on Normal | Rejected as out of range, attempt not used | Accepted as a normal guess and burns an attempt | (no message) | `parse_guess` never checks the guess against the difficulty range |

-------|-------------------|-----------------|------------------------|
| | | | |
| | | | |
| | | | |

---

## 2. How did you use AI as a teammate?

I used Claude (Anthropic) in agent mode as my main assistant. I gave it the assignment and rubric, and it worked directly in my repo: running the original game headlessly to reproduce bugs, proposing fixes, refactoring into `logic_utils.py`, writing tests and running `pytest` and `flake8`. I reviewed each diff before committing and kept the work split into separate commits (bug log, fixes, features/tests, docs).

**A suggestion that was correct: remove the string-secret path entirely.** The AI explained that the "random wrong hints" were not random at all: on every even attempt `app.py` did `secret = str(st.session_state.secret)`, so `guess > secret` raised `TypeError` and `check_guess` fell back to comparing strings. As strings, `"9" > "50"` is true, so a guess of 9 against 50 came back "Too High" (and earned +5 points because of the scoring bug). It suggested deleting both the `str()` cast in `app.py` and the `except TypeError` fallback in `check_guess`, so the function only ever compares ints. This was correct because the fallback only existed to hide the bad cast. Keeping it would have left a code path that silently gives wrong answers. I verified it with `test_single_digit_guess_is_too_low_not_string_compared` (9 vs 50 must be "Too Low") and by replaying the game in `evidence/verify_fixed.py`, where guesses 60, 40, 9 against 50 now show "Go LOWER", "Go HIGHER", "Go HIGHER" with the score dropping 5 each time.

**A suggestion I did not accept as written: the AI's own test expectation for the hot/cold hint.** When the AI generated edge-case tests for `get_temperature`, it wrote `assert get_temperature(13, 10, 1, 20)[0] == "Warm"`, claiming 3 away on Easy should be "Warm". The test failed. The tempting move was to loosen the thresholds in the code until the test passed, but I checked the math first: 3 away on a range of 1 to 20 is 3/19 ≈ 0.158 of the span, which is past the 0.15 "Warm" cutoff, so "Cool" was the right answer and the test was wrong, not the code. I changed the test to use 2 away (2/19 ≈ 0.105 → Warm on Easy, 2/99 ≈ 0.02 → Hot on Normal), which still proves the point that closeness scales with the range. I re-ran `pytest` and all 42 tests passed. This was a good reminder that AI-written tests can be confidently wrong too, so a failing test is a question, not an automatic order to change the code.

A smaller revision: the AI's first version of `load_high_scores` filtered out entries whose keys were not strings. JSON object keys are always strings, so that check could never fail. I dropped it during the PEP 8 pass because it made the line longer without protecting against anything.

---

## 3. Debugging and testing your fixes

I counted a bug as fixed only when two things were true: a pytest case that targets that exact bug passed, and replaying the same scenario in the real app produced the expected behavior. For the app side I used Streamlit's `AppTest`, which runs `app.py` exactly as `streamlit run` does and lets me click buttons and read the widgets. `evidence/repro_original.py` captured the broken behavior before any fix, and `evidence/verify_fixed.py` replays the same sessions afterwards:

```
=== Session A: secret=50, Normal (bugs 1, 2, 3, 4) ===
  on load: ['Guess a number between 1 and 100. Attempts left: 8']
  guess=60     attempts=1 score=-5 status=playing hint=['Go LOWER!'] errors=[]
      info banner -> ['Guess a number between 1 and 100. Attempts left: 7']
=== Session B: first-try win (bug 8) ===
  guess=50     attempts=1 score=100 status=won hint=[] errors=[]
=== Session C: invalid / out-of-range input (bugs 7, 9) ===
  guess='abc'  attempts=0 ... errors=['That is not a number.']
  guess='-5'   attempts=0 ... errors=['Guess must be between 1 and 100.']
  history: []
=== Session D: win, then press New Game (bug 5) ===
  after New Game: status=playing attempts=0 score=0 history=[]
=== Session E: Hard difficulty (bug 6) ===
  sidebar: ['Range: 1 to 200', 'Attempts allowed: 5']
  main banner: ['Guess a number between 1 and 200. Attempts left: 5']
```

One pytest case I relied on is `test_wrong_guess_never_adds_points`, which loops over attempts 1 to 8 and asserts that both "Too High" and "Too Low" always cost exactly 5 points. That test showed me the old parity check (`attempt_number % 2 == 0`) was the only reason a wrong guess could increase the score, so removing it fully fixed bug 3. The full suite (42 tests across `tests/test_game_logic.py` and `tests/test_edge_cases.py`) passes; the output is in `test_results.txt` and the README. AI helped by proposing the edge-case inputs (whitespace, `nan`, `inf`, `"42.0"`, a 20-digit number, a corrupt JSON file) that I would not have thought of on my own, and by suggesting `pytest.mark.parametrize` so each input shows up as its own test line.

---

## 4. What did you learn about Streamlit and state?

Streamlit reruns the entire script from top to bottom every time you interact with anything, like clicking a button or typing in a box. That means a normal Python variable is rebuilt on every click, so anything that has to survive between clicks (the secret, attempts, score, history) must live in `st.session_state`, which is a dictionary that persists for the browser session. The order of the script also matters: the original banner was drawn before the submit handler ran, so it always showed last turn's attempt count. I fixed that by reserving a slot with `st.empty()` at the top and filling it after the guess was processed. I also learned that state has to be reset as a whole: the original New Game button reset two keys and forgot the `status` key, which left the game permanently stuck after a win.

---

## 5. Looking ahead: your developer habits

- The habit I want to keep is reproducing a bug with a script before touching the code, then replaying the same script after the fix. Having a before and after log made it obvious which bugs were really gone and gave me evidence I could paste straight into my docs.
- Next time I would ask the AI for one bug at a time and review smaller diffs. Letting an agent do a lot in one pass is fast, but it means more code to read carefully before I can trust it, and I caught one wrong AI-written test only because it failed.
- This project changed how I think about AI-generated code: it can look clean and "production-ready" while hiding bugs that cancel each other out (the swapped hint messages plus string comparison sometimes gave the right advice by accident). I now treat AI code as a first draft that needs tests and a human in the loop before it is done.
