# 🎮 Game Glitch Investigator: The Impossible Guesser

## 🎯 Game Purpose

Glitchy Guesser is a Streamlit number-guessing game. The app picks a secret number inside a range set by the difficulty (Easy 1 to 20, Normal 1 to 100, Hard 1 to 200). You get a limited number of guesses, each guess tells you whether to go higher or lower, and your score rewards winning in fewer attempts. The starter version was written by an AI and was broken in several ways. This repo documents how I found, fixed and tested those bugs with an AI assistant as a teammate.

## 🛠️ Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py   # play the game
python -m pytest                 # run the tests
```

## 🐞 Bugs Found

Full reproduction log with inputs, expected vs actual behavior and captured output: [`reflection.md`](reflection.md) section 1 and [`evidence/repro_original_output.txt`](evidence/repro_original_output.txt).

| # | Bug | Root cause |
|---|-----|-----------|
| 1 | Hints point the wrong way ("Too High" says "Go HIGHER") | `check_guess` messages swapped |
| 2 | Hints and outcomes randomly wrong on every 2nd guess (9 vs 50 = "Too High") | `app.py` cast the secret to `str` on even attempts; `check_guess` fell back to string comparison |
| 3 | Wrong guesses sometimes **add** points | `update_score` gave +5 for "Too High" on even attempts |
| 4 | "Attempts left" starts one short and lags a turn behind | counter started at 1; banner drawn before the guess was processed |
| 5 | New Game does nothing after a win/loss | New Game never reset `status`, `score` or `history` |
| 6 | Hard is easier than Normal; banner always says "1 and 100" | Hard returned `(1, 50)`; range text and New Game `randint(1, 100)` hardcoded |
| 7 | Invalid input (`abc`, blank) burns an attempt and pollutes history | attempt counted before validation |
| 8 | First-try win only worth 80 points | off-by-one in the win formula |
| 9 | Out-of-range guesses (`-5`, `500`) accepted | no range check in `parse_guess` |

## 🔧 Fixes Applied

All game logic now lives in [`logic_utils.py`](logic_utils.py) (pure functions, no Streamlit) and [`app.py`](app.py) only handles UI and `st.session_state`. Each fix is marked with a `# FIX:` comment in the code.

- **`check_guess`**: correct messages (too high → "Go LOWER"), ints only, no `TypeError` string fallback. The `str()` cast in `app.py` is gone.
- **`update_score`**: every wrong guess costs 5; a win on attempt *n* earns `100 - 10 * (n - 1)` (min 10), so a first-try win is 100.
- **`start_new_game()`** in `app.py`: one function resets secret, attempts, score, status and history, using the selected difficulty's range. Changing difficulty also starts a fresh game.
- **Attempt counter** starts at 0 and only counts valid guesses. The banner is reserved with `st.empty()` and filled after the guess is processed, so it is never stale.
- **`DIFFICULTY_SETTINGS`** table: Easy 1–20 / 6 tries, Normal 1–100 / 8 tries, Hard 1–200 / 5 tries. The banner shows the real range.
- **`parse_guess(raw, low, high)`**: strips whitespace, rejects text, fractions, `nan`/`inf` and out-of-range values with a clear message instead of silently truncating `3.9` to `3`.

## 📸 Demo Walkthrough

A Normal game, replayed in the real app with the secret set to 50 (captured in [`evidence/verify_fixed_output.txt`](evidence/verify_fixed_output.txt), sessions C, D and G):

1. The game loads on Normal. The banner says "Guess a number between 1 and 100. Attempts left: 8" and the sidebar shows the 🏆 High Scores panel.
2. User types `abc` and submits. The game shows "That is not a number." and attempts left stays at 8.
3. User enters a guess of 90. The game shows "📉 Go LOWER! 🧊 Cold" in blue. Attempts left drops to 7 and the score goes to -5.
4. User enters 60. The hint is "📉 Go LOWER! ♨️ Warm", now in orange because the guess is close. Attempts left: 6, score -10.
5. User enters 52. The hint is "📉 Go LOWER! 🔥 Hot". Attempts left: 5, score -15.
6. User enters 50. Balloons appear, "You won! The secret was 50. Final score: 55." and "🏆 New Normal high score!"
7. The 📋 Guess history table lists all four guesses with their result (⬆️ Too high / 🎉 Correct) and closeness (🧊 Cold → ♨️ Warm → 🔥 Hot → 🎯 Bullseye). The sidebar now shows "Normal: 55 ◀".
8. User clicks New Game. Status, score, attempts and history reset, a new secret is drawn from 1 to 100, and the high score is kept.

## 🧪 Test Results

42 tests: the starter tests (updated to unpack `(outcome, message)`), one regression test per fixed bug in `tests/test_game_logic.py`, and edge cases in `tests/test_edge_cases.py`. Also saved in [`test_results.txt`](test_results.txt).

```
$ python -m pytest -v
collecting ... collected 42 items

tests/test_edge_cases.py::test_non_numeric_strings_are_rejected[abc] PASSED [  2%]
tests/test_edge_cases.py::test_non_numeric_strings_are_rejected[12abc] PASSED [  4%]
tests/test_edge_cases.py::test_non_numeric_strings_are_rejected[one] PASSED [  7%]
tests/test_edge_cases.py::test_non_numeric_strings_are_rejected[4 2] PASSED [  9%]
tests/test_edge_cases.py::test_non_numeric_strings_are_rejected[--5] PASSED [ 11%]
tests/test_edge_cases.py::test_empty_or_whitespace_input_is_rejected[None] PASSED [ 14%]
tests/test_edge_cases.py::test_empty_or_whitespace_input_is_rejected[] PASSED [ 16%]
tests/test_edge_cases.py::test_empty_or_whitespace_input_is_rejected[   ] PASSED [ 19%]
tests/test_edge_cases.py::test_negative_zero_and_huge_values_are_out_of_range[-5] PASSED [ 21%]
tests/test_edge_cases.py::test_negative_zero_and_huge_values_are_out_of_range[0] PASSED [ 23%]
tests/test_edge_cases.py::test_negative_zero_and_huge_values_are_out_of_range[101] PASSED [ 26%]
tests/test_edge_cases.py::test_negative_zero_and_huge_values_are_out_of_range[99999999999999999999] PASSED [ 28%]
tests/test_edge_cases.py::test_fractional_and_non_finite_floats_are_rejected[3.5] PASSED [ 30%]
tests/test_edge_cases.py::test_fractional_and_non_finite_floats_are_rejected[99.9] PASSED [ 33%]
tests/test_edge_cases.py::test_fractional_and_non_finite_floats_are_rejected[nan] PASSED [ 35%]
tests/test_edge_cases.py::test_fractional_and_non_finite_floats_are_rejected[inf] PASSED [ 38%]
tests/test_edge_cases.py::test_fractional_and_non_finite_floats_are_rejected[-inf] PASSED [ 40%]
tests/test_edge_cases.py::test_valid_inputs_including_boundaries[42-42] PASSED [ 42%]
tests/test_edge_cases.py::test_valid_inputs_including_boundaries[  7  -7] PASSED [ 45%]
tests/test_edge_cases.py::test_valid_inputs_including_boundaries[42.0-42] PASSED [ 47%]
tests/test_edge_cases.py::test_valid_inputs_including_boundaries[1-1] PASSED [ 50%]
tests/test_edge_cases.py::test_valid_inputs_including_boundaries[100-100] PASSED [ 52%]
tests/test_edge_cases.py::test_range_check_is_skipped_without_bounds PASSED [ 54%]
tests/test_edge_cases.py::test_unknown_difficulty_falls_back_to_normal PASSED [ 57%]
tests/test_edge_cases.py::test_temperature_labels[50-50-Bullseye] PASSED [ 59%]
tests/test_edge_cases.py::test_temperature_labels[53-50-Hot] PASSED      [ 61%]
tests/test_edge_cases.py::test_temperature_labels[60-50-Warm] PASSED     [ 64%]
tests/test_edge_cases.py::test_temperature_labels[75-50-Cool] PASSED     [ 66%]
tests/test_edge_cases.py::test_temperature_labels[1-100-Cold] PASSED     [ 69%]
tests/test_edge_cases.py::test_temperature_scales_with_range PASSED      [ 71%]
tests/test_edge_cases.py::test_missing_high_score_file_returns_empty PASSED [ 73%]
tests/test_edge_cases.py::test_corrupt_high_score_file_does_not_crash PASSED [ 76%]
tests/test_edge_cases.py::test_high_score_only_saved_when_beaten PASSED  [ 78%]
tests/test_game_logic.py::test_winning_guess PASSED                      [ 80%]
tests/test_game_logic.py::test_guess_too_high PASSED                     [ 83%]
tests/test_game_logic.py::test_guess_too_low PASSED                      [ 85%]
tests/test_game_logic.py::test_too_high_hint_says_go_lower PASSED        [ 88%]
tests/test_game_logic.py::test_too_low_hint_says_go_higher PASSED        [ 90%]
tests/test_game_logic.py::test_single_digit_guess_is_too_low_not_string_compared PASSED [ 92%]
tests/test_game_logic.py::test_wrong_guess_never_adds_points PASSED      [ 95%]
tests/test_game_logic.py::test_first_try_win_scores_100 PASSED           [ 97%]
tests/test_game_logic.py::test_hard_range_is_wider_than_normal PASSED    [100%]

============================== 42 passed in 0.03s ==============================
```

## 🚀 Stretch Features

- [x] **Challenge 1: Advanced edge-case testing.** `tests/test_edge_cases.py` covers non-numeric strings, empty/whitespace input, negatives, zero, a 20-digit number, fractions, `nan`/`inf`, boundaries, an unknown difficulty, and missing/corrupt high-score files. Prompts and rationale are in [`ai_interactions.md`](ai_interactions.md).
- [x] **Challenge 2: Feature expansion (High Score tracker).** The best winning score per difficulty is saved to `high_scores.json` via `save_high_score()` / `load_high_scores()` in `logic_utils.py` and shown in the sidebar. A corrupt or missing file never crashes the game. The agent workflow is in [`ai_interactions.md`](ai_interactions.md).
- [x] **Challenge 3: Docstrings and PEP 8.** Every function in `logic_utils.py` has a Google-style docstring. `flake8` went from 10 issues to 0 ([`evidence/lint_before.txt`](evidence/lint_before.txt), [`evidence/lint_after.txt`](evidence/lint_after.txt)).
- [x] **Challenge 4: Enhanced UI.**
  - **Hot/Cold hints**: new `get_temperature(guess, secret, low, high)` in `logic_utils.py` returns 🎯 Bullseye / 🔥 Hot / ♨️ Warm / 🌤️ Cool / 🧊 Cold based on distance as a fraction of the range, so it means the same on Easy and Hard.
  - **Color-coded hints**: the submit handler in `app.py` shows Hot/Warm hints with `st.warning` (orange) and Cool/Cold hints with `st.info` (blue), with the emoji appended to the "Go HIGHER/LOWER" message.
  - **Session summary table**: `st.session_state.history` now stores `{guess, outcome, temperature}` and `app.py` renders it as a "📋 Guess history" `st.table`, using `OUTCOME_STYLE` to label each row ⬆️ Too high / ⬇️ Too low / 🎉 Correct.
  - **High score sidebar** with a ◀ marker next to the current difficulty, and a "🏆 New high score!" banner on a record win.
- [ ] Challenge 5: Model comparison (not attempted).

## 📁 Evidence Files

- `evidence/repro_original.py` / `repro_original_output.txt`: the original game driven headlessly, showing each bug.
- `evidence/verify_fixed.py` / `verify_fixed_output.txt`: the same scenarios replayed after the fixes, plus the new features.
- `evidence/lint_before.txt` / `lint_after.txt`: flake8 output.
