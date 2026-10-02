import random
from pathlib import Path

import streamlit as st

from logic_utils import (
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    get_temperature,
    load_high_scores,
    parse_guess,
    save_high_score,
    update_score,
)

# FEATURE: High Score tracker. Best winning score per difficulty is saved
# next to app.py so it survives browser refreshes and app restarts.
HIGH_SCORE_FILE = Path(__file__).with_name("high_scores.json")

OUTCOME_STYLE = {
    "Win": "🎉 Correct",
    "Too High": "⬆️ Too high",
    "Too Low": "⬇️ Too low",
}

# FIX: All game logic (range, parsing, hint, scoring) was moved out of this
# file into logic_utils.py with AI agent help so it can be unit tested.
# app.py now only handles UI and st.session_state.


def start_new_game(difficulty: str) -> None:
    """Reset every piece of per-game state for the chosen difficulty."""
    # FIX: New Game used to reset only attempts (to 0) and draw the secret
    # from 1-100. Status, score and history stayed, so after a win/loss the
    # game was stuck. Now everything resets and the range matches difficulty.
    low, high = get_range_for_difficulty(difficulty)
    st.session_state.secret = random.randint(low, high)
    # FIX: counts guesses actually made (the starter code started it at 1)
    st.session_state.attempts = 0
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.difficulty = difficulty
    st.session_state.new_record = False


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game, now debugged.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit = get_attempt_limit(difficulty)
low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

st.sidebar.header("🏆 High Scores")
high_scores = load_high_scores(HIGH_SCORE_FILE)
for level in ["Easy", "Normal", "Hard"]:
    best = high_scores.get(level)
    marker = " ◀" if level == difficulty else ""
    shown = best if best is not None else "—"
    st.sidebar.write(f"**{level}:** {shown}{marker}")

# FIX: the secret is created once per game and kept in session_state, and a
# difficulty change starts a fresh game so the secret matches the new range.
difficulty_changed = st.session_state.get("difficulty") != difficulty
if difficulty_changed or "secret" not in st.session_state:
    start_new_game(difficulty)

st.subheader("Make a guess")

# FIX: the banner used to be drawn before the guess was processed, so the
# count lagged one guess behind. Reserve its slot now and fill it at the end.
banner = st.empty()

raw_guess = st.text_input(
    "Enter your guess:",
    key=f"guess_input_{difficulty}"
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

if new_game:
    start_new_game(difficulty)
    st.success("New game started.")

if submit and st.session_state.status == "playing":
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        # FIX: invalid input no longer burns an attempt or pollutes history.
        st.error(err)
    else:
        st.session_state.attempts += 1

        # FIX: the secret used to be cast to str on even attempts, which made
        # check_guess compare strings ("9" > "50"). It is always an int now.
        outcome, message = check_guess(guess_int, st.session_state.secret)
        temp_label, temp_emoji = get_temperature(
            guess_int, st.session_state.secret, low, high
        )
        st.session_state.history.append(
            {
                "guess": guess_int,
                "outcome": outcome,
                "temperature": f"{temp_emoji} {temp_label}",
            }
        )

        if show_hint and outcome != "Win":
            # UI: colour-coded hint. Hot/Warm guesses show in orange (warning),
            # Cool/Cold guesses in blue (info), each with a temperature emoji.
            hint_text = f"{message}  {temp_emoji} {temp_label}"
            if temp_label in ("Hot", "Warm"):
                st.warning(hint_text)
            else:
                st.info(hint_text)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            _, st.session_state.new_record = save_high_score(
                HIGH_SCORE_FILE, difficulty, st.session_state.score
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"

attempts_left = attempt_limit - st.session_state.attempts
banner.info(
    f"Guess a number between {low} and {high}. "
    f"Attempts left: {attempts_left}"
)

if st.session_state.status == "won":
    st.success(
        f"You won! The secret was {st.session_state.secret}. "
        f"Final score: {st.session_state.score}. Press New Game to play again."
    )
    if st.session_state.get("new_record"):
        st.success(f"🏆 New {difficulty} high score!")
elif st.session_state.status == "lost":
    st.error(
        f"Out of attempts! The secret was {st.session_state.secret}. "
        f"Score: {st.session_state.score}. Press New Game to try again."
    )

# UI: session summary table, one row per valid guess.
if st.session_state.history:
    st.subheader("📋 Guess history")
    st.table(
        [
            {
                "#": i,
                "Guess": row["guess"],
                "Result": OUTCOME_STYLE[row["outcome"]],
                "Closeness": row["temperature"],
            }
            for i, row in enumerate(st.session_state.history, start=1)
        ]
    )

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI, debugged by a human in the loop.")
