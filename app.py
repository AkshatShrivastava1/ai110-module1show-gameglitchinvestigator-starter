import random

import streamlit as st

from logic_utils import (
    check_guess,
    get_attempt_limit,
    get_range_for_difficulty,
    parse_guess,
    update_score,
)

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
    st.session_state.attempts = 0  # FIX: counts guesses made (was started at 1)
    st.session_state.score = 0
    st.session_state.status = "playing"
    st.session_state.history = []
    st.session_state.difficulty = difficulty


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

# FIX: the secret is created once per game and kept in session_state, and a
# difficulty change starts a fresh game so the secret matches the new range.
if st.session_state.get("difficulty") != difficulty or "secret" not in st.session_state:
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
        st.session_state.history.append(guess_int)

        # FIX: the secret used to be cast to str on even attempts, which made
        # check_guess compare strings ("9" > "50"). It is always an int now.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint and outcome != "Win":
            st.warning(message)

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            attempt_number=st.session_state.attempts,
        )

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
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
elif st.session_state.status == "lost":
    st.error(
        f"Out of attempts! The secret was {st.session_state.secret}. "
        f"Score: {st.session_state.score}. Press New Game to try again."
    )

with st.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

st.divider()
st.caption("Built by an AI, debugged by a human in the loop.")
