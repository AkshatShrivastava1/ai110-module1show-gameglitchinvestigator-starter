# AI Interactions Log

AI tool used: **Claude (Anthropic), agent mode**, working directly in this repo (reading files, editing code, running `pytest`, `flake8` and Streamlit's `AppTest`). I reviewed every diff before committing.

---

## Agent Workflow

**What task did you give the agent?**

I gave the agent the full project brief and grading rubric and asked it to finish the project: reproduce the bugs in the starter game, fix them by moving the logic into `logic_utils.py`, add tests, and implement a meaningful new feature. For the feature I chose a **High Score tracker** that saves the best score per difficulty to a file, plus the hot/cold UI from Challenge 4.

**What did the agent do?**

1. Ran the original `app.py` headlessly with `streamlit.testing.v1.AppTest` (`evidence/repro_original.py`) to capture each bug, then added `# FIXME` comments at each crime scene and filled in the bug log in `reflection.md`. *(commit: "docs: log reproduced bugs…")*
2. Rewrote `logic_utils.py` with fixed versions of `get_range_for_difficulty`, `parse_guess`, `check_guess`, `update_score`, plus a new `get_attempt_limit` and a `DIFFICULTY_SETTINGS` table.
3. Rewrote `app.py` to import from `logic_utils`, added `start_new_game()` to reset all state, removed the `str()` cast on the secret, moved the attempt counter after validation and used an `st.empty()` placeholder for the banner. Added `pytest.ini` so `tests/` can import `logic_utils`. *(commit: "fix: refactor game logic…")*
4. Added `get_temperature`, `load_high_scores` and `save_high_score` to `logic_utils.py`; added the High Scores sidebar, colour-coded hints and the guess history table to `app.py`; added `high_scores.json` to `.gitignore`. *(commit: "feat: add high score tracker…")*
5. Wrote `tests/test_edge_cases.py`, ran `pytest` (42 passing) and replayed every scenario in `evidence/verify_fixed.py`.

**Files modified:** `app.py`, `logic_utils.py`, `tests/test_game_logic.py`, `tests/test_edge_cases.py` (new), `pytest.ini` (new), `.gitignore`, `evidence/*` (new), `README.md`, `reflection.md`, `ai_interactions.md`, `test_results.txt` (new).

**What did you have to verify or fix manually?**

- The agent's first edge-case test claimed 3 away on Easy (1 to 20) should be "Warm". The test failed. I checked the math (3/19 ≈ 0.158, past the 0.15 Warm cutoff) and fixed the **test**, not the thresholds, changing it to 2 away.
- The original starter tests compared `check_guess(...)` to a plain string, but the function returns a `(outcome, message)` tuple. I kept the function's tuple return because `app.py` needs the message, and updated the tests to unpack it.
- I reviewed the high-score code path end to end in the app (win → JSON file written → sidebar shows "Normal: 55 ◀") and confirmed a corrupt file is ignored instead of crashing.
- I chose to keep Hard at 5 attempts after widening its range to 1 to 200. It is meant to be hard, and the hot/cold hints make it winnable.

---

## Test Generation

**Prompt used (to the agent):**

```
Identify edge-case inputs that could still break the game after the fixes
(e.g. negative numbers, decimals, extremely large values, empty input) and
generate a pytest suite in tests/test_edge_cases.py that checks parse_guess,
get_temperature and the high-score file handle them gracefully. Use
parametrize so each input is its own test case.
```

| Edge Case | Prompt Used | AI-Suggested Test | Did It Pass? | Your Reasoning |
|-----------|-------------|-------------------|--------------|----------------|
| Non-numeric strings (`abc`, `12abc`, `4 2`, `--5`) | Prompt above | `test_non_numeric_strings_are_rejected` | ✅ Yes | Players mistype; text must give a clear error, not crash or burn an attempt. |
| Empty / whitespace / `None` | Prompt above | `test_empty_or_whitespace_input_is_rejected` | ✅ Yes | Clicking Submit with an empty box is the most common accidental input. |
| Negative, zero and a 20-digit number | Prompt above | `test_negative_zero_and_huge_values_are_out_of_range` | ✅ Yes | The original game accepted any int, so `-5` or `500` wasted an attempt. A huge value checks there is no overflow. |
| Fractions and `nan` / `inf` | Prompt above | `test_fractional_and_non_finite_floats_are_rejected` | ✅ Yes | The original silently truncated `3.9` to `3`; `float("nan")` and `float("inf")` would crash `int()`. |
| Boundaries and `"42.0"`, `"  7  "` | Prompt above | `test_valid_inputs_including_boundaries` | ✅ Yes | Makes sure the stricter parsing did not start rejecting valid guesses like 1 and 100. |
| Hot/cold scaling across ranges | Prompt above | `test_temperature_scales_with_range` | ❌ First version failed, ✅ after fix | The AI expected 3 away on Easy to be "Warm"; it is 15.8% of the range, so "Cool" is correct. I fixed the test to use 2 away. |
| Missing / corrupt high-score file | Prompt above | `test_missing_high_score_file_returns_empty`, `test_corrupt_high_score_file_does_not_crash` | ✅ Yes | A hand-edited or half-written JSON file should never crash the game. |
| Equal or lower score than the record | Prompt above | `test_high_score_only_saved_when_beaten` | ✅ Yes | Ties and lower scores must not overwrite the record. |

---

## Linting & Style

**Prompt used:**

```
Add professional Google-style docstrings to every function in logic_utils.py
(args, returns, edge-case behaviour). Then run flake8 on app.py,
logic_utils.py, tests/ and evidence/, and fix every PEP 8 issue it reports
without changing behaviour. Re-run pytest afterwards.
```

**Linting output before** (`evidence/lint_before.txt`):

```
app.py:39:80: E501 line too long (80 > 79 characters)
app.py:71:80: E501 line too long (81 > 79 characters)
app.py:75:80: E501 line too long (88 > 79 characters)
evidence/repro_original.py:58:80: E501 line too long (80 > 79 characters)
evidence/verify_fixed.py:79:1: E402 module level import not at top of file
logic_utils.py:193:80: E501 line too long (80 > 79 characters)
tests/test_edge_cases.py:1:80: E501 line too long (80 > 79 characters)
tests/test_edge_cases.py:44:80: E501 line too long (107 > 79 characters)
tests/test_edge_cases.py:54:80: E501 line too long (87 > 79 characters)
tests/test_edge_cases.py:62:80: E501 line too long (98 > 79 characters)
```

**Linting output after** (`evidence/lint_after.txt`):

```
flake8: 0 issues
```

**Changes applied:**

- Docstrings (Args/Returns) added to all 9 functions in `logic_utils.py`, plus a module docstring. Type hints added to the core functions.
- E501: long lines split. In `app.py` the AI introduced named variables (`difficulty_changed`, `shown`) instead of just wrapping lines, which I kept because it reads better. Long `parametrize` lists in the tests were split one case per line.
- E402: moved `import json` to the top of `evidence/verify_fixed.py`.
- Naming: renamed the `k, v` loop variables in `load_high_scores` to `key, value`. I also dropped the AI's `isinstance(k, str)` check there, since JSON keys are always strings.
- Re-ran `pytest` after the cleanup: still 42 passed.
