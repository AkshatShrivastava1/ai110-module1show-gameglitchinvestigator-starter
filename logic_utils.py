"""Pure game logic for the Glitchy Guesser number-guessing game.

Everything in this module is free of Streamlit so it can be unit tested
with pytest. ``app.py`` handles the UI and session state only.
"""

import json
import math
from pathlib import Path

# FIX: Hard used to be 1-50 (easier than Normal). Ranges and attempt limits
# now live in one table so the UI, New Game, and validation all agree.
DIFFICULTY_SETTINGS = {
    "Easy": {"range": (1, 20), "attempts": 6},
    "Normal": {"range": (1, 100), "attempts": 8},
    "Hard": {"range": (1, 200), "attempts": 5},
}
DEFAULT_DIFFICULTY = "Normal"


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive ``(low, high)`` guessing range for a difficulty.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"`` or ``"Hard"``. Unknown
            values fall back to Normal.

    Returns:
        A ``(low, high)`` tuple of ints, both inclusive.
    """
    settings = DIFFICULTY_SETTINGS.get(
        difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]
    )
    return settings["range"]


def get_attempt_limit(difficulty: str) -> int:
    """Return how many valid guesses the player gets for a difficulty.

    Args:
        difficulty: One of ``"Easy"``, ``"Normal"`` or ``"Hard"``. Unknown
            values fall back to Normal.

    Returns:
        The maximum number of guesses allowed.
    """
    settings = DIFFICULTY_SETTINGS.get(
        difficulty, DIFFICULTY_SETTINGS[DEFAULT_DIFFICULTY]
    )
    return settings["attempts"]


def parse_guess(raw, low=None, high=None):
    """Parse raw text input into a whole-number guess.

    Surrounding whitespace is ignored. Values like ``"42.0"`` are accepted,
    but fractional values (``"42.5"``), ``nan``/``inf`` and non-numeric text
    are rejected instead of being silently truncated. If ``low`` and
    ``high`` are given, the guess must fall inside that inclusive range.

    Args:
        raw: The text the player typed (may be ``None``).
        low: Optional inclusive lower bound.
        high: Optional inclusive upper bound.

    Returns:
        A tuple ``(ok, guess, error_message)``. On success ``ok`` is True,
        ``guess`` is an int and ``error_message`` is None. On failure ``ok``
        is False, ``guess`` is None and ``error_message`` explains why.
    """
    if raw is None:
        return False, None, "Enter a guess."

    text = str(raw).strip()
    if text == "":
        return False, None, "Enter a guess."

    try:
        value = int(text)
    except ValueError:
        # FIX: the starter code did int(float(raw)), so "3.9" became 3.
        # Only accept floats that are exact whole numbers.
        try:
            as_float = float(text)
        except ValueError:
            return False, None, "That is not a number."
        if not math.isfinite(as_float) or not as_float.is_integer():
            return False, None, "Please enter a whole number."
        value = int(as_float)

    # FIX: out-of-range guesses used to be accepted and burn an attempt.
    if low is not None and high is not None and not low <= value <= high:
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """Compare a guess with the secret number.

    Args:
        guess: The player's guess.
        secret: The secret number. Both values must be ints.

    Returns:
        A tuple ``(outcome, message)`` where ``outcome`` is ``"Win"``,
        ``"Too High"`` or ``"Too Low"`` and ``message`` is the hint to show.
    """
    # FIX: messages were swapped ("Too High" said "Go HIGHER"), and a
    # TypeError fallback compared strings ("9" > "50"). Ints only now.
    if guess == secret:
        return "Win", "🎉 Correct!"
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def update_score(current_score: int, outcome: str, attempt_number: int) -> int:
    """Return the new score after a guess.

    A win on attempt ``n`` (1-based) earns ``100 - 10 * (n - 1)`` points,
    never less than 10. Every wrong guess costs 5 points.

    Args:
        current_score: Score before this guess.
        outcome: ``"Win"``, ``"Too High"`` or ``"Too Low"``.
        attempt_number: 1-based number of the guess just made.

    Returns:
        The updated score.
    """
    if outcome == "Win":
        # FIX: was 100 - 10 * (attempt_number + 1), so a first-try win paid 80.
        points = max(10, 100 - 10 * (attempt_number - 1))
        return current_score + points

    # FIX: "Too High" on an even attempt used to ADD 5 points.
    if outcome in ("Too High", "Too Low"):
        return current_score - 5

    return current_score


def get_temperature(guess: int, secret: int, low: int, high: int):
    """Describe how close a guess is with a hot/cold label and emoji.

    Closeness is measured as a fraction of the difficulty's range, so the
    labels mean the same thing on Easy (1-20) and Hard (1-200).

    Args:
        guess: The player's guess.
        secret: The secret number.
        low: Inclusive lower bound of the range.
        high: Inclusive upper bound of the range.

    Returns:
        A tuple ``(label, emoji)``, e.g. ``("Hot", "🔥")``.
    """
    distance = abs(guess - secret)
    if distance == 0:
        return "Bullseye", "🎯"
    span = max(1, high - low)
    ratio = distance / span
    if ratio <= 0.05:
        return "Hot", "🔥"
    if ratio <= 0.15:
        return "Warm", "♨️"
    if ratio <= 0.30:
        return "Cool", "🌤️"
    return "Cold", "🧊"


def load_high_scores(path) -> dict:
    """Load saved high scores (one per difficulty) from a JSON file.

    A missing, unreadable or malformed file returns an empty dict instead
    of crashing the game.

    Args:
        path: Location of the JSON file.

    Returns:
        A dict mapping difficulty name to best score.
    """
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        key: value
        for key, value in data.items()
        if isinstance(value, int) and not isinstance(value, bool)
    }


def save_high_score(path, difficulty: str, score: int):
    """Record ``score`` for ``difficulty`` if it beats the saved best.

    Args:
        path: Location of the JSON file.
        difficulty: Difficulty the game was played on.
        score: Final score of a won game.

    Returns:
        A tuple ``(high_scores, is_new_record)`` with the up-to-date scores.
    """
    scores = load_high_scores(path)
    best = scores.get(difficulty)
    if best is not None and score <= best:
        return scores, False
    scores[difficulty] = score
    Path(path).write_text(json.dumps(scores, indent=2, sort_keys=True))
    return scores, True
