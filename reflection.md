# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

The first time I ran the game it looked fine (title, sidebar, input box, debug expander) but it was not actually playable. With the secret pinned to 50, a guess of 60 told me to "Go HIGHER" and a guess of 40 told me to "Go LOWER", so the hints pointed the wrong way. The "Attempts left" banner started at 7 on Normal even though the sidebar said 8, and it did not change after my first guess. After winning, the New Game button did nothing: the game stayed stuck on "You already won." Hard mode used a range of 1 to 50, which is easier than Normal, while the banner still said "between 1 and 100".

I drove the original `app.py` headlessly with Streamlit's `AppTest` (`evidence/repro_original.py`), so every row below comes from a real run. Full output is in `evidence/repro_original_output.txt`:

```
=== Session A: secret=50, Normal ===
  on load: ['Guess a number between 1 and 100. Attempts left: 7']
  guess=60     attempts=2 score=5 status=playing hint=['📈 Go HIGHER!'] errors=[]
      info banner -> ['Guess a number between 1 and 100. Attempts left: 7']
  guess=40     attempts=3 score=0 status=playing hint=['📉 Go LOWER!'] errors=[]
      info banner -> ['Guess a number between 1 and 100. Attempts left: 6']
  guess=9      attempts=4 score=5 status=playing hint=['📈 Go HIGHER!'] errors=[]
=== Session C: invalid input ===
  guess='abc'  attempts=2 score=0 status=playing hint=[] errors=['That is not a number.']
  guess=''     attempts=3 score=0 status=playing hint=[] errors=['Enter a guess.']
  history: ['abc', '']
=== Session D: win, then press New Game ===
  guess=50     attempts=3 score=60 status=won hint=['🎉 Correct!'] errors=[]
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

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?
- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).
- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?
- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.
- Did AI help you design or understand any tests? How?

---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.
- What is one thing you would do differently next time you work with AI on a coding task?
- In one or two sentences, describe how this project changed the way you think about AI generated code.
