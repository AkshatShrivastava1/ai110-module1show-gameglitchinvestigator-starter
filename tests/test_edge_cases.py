"""Edge-case tests for parsing, hot/cold hints and the high-score file."""

import pytest

from logic_utils import (
    get_attempt_limit,
    get_range_for_difficulty,
    get_temperature,
    load_high_scores,
    parse_guess,
    save_high_score,
)


# ---- parse_guess edge cases -------------------------------------------------

@pytest.mark.parametrize("raw", ["abc", "12abc", "one", "4 2", "--5"])
def test_non_numeric_strings_are_rejected(raw):
    ok, value, err = parse_guess(raw, 1, 100)
    assert not ok and value is None
    assert err == "That is not a number."


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_empty_or_whitespace_input_is_rejected(raw):
    ok, value, err = parse_guess(raw, 1, 100)
    assert (ok, value, err) == (False, None, "Enter a guess.")


@pytest.mark.parametrize("raw", ["-5", "0", "101", "99999999999999999999"])
def test_negative_zero_and_huge_values_are_out_of_range(raw):
    ok, value, err = parse_guess(raw, 1, 100)
    assert not ok and value is None
    assert err == "Guess must be between 1 and 100."


@pytest.mark.parametrize("raw", ["3.5", "99.9", "nan", "inf", "-inf"])
def test_fractional_and_non_finite_floats_are_rejected(raw):
    ok, value, err = parse_guess(raw, 1, 100)
    assert not ok and value is None
    assert err == "Please enter a whole number."


@pytest.mark.parametrize(
    "raw, expected",
    [("42", 42), ("  7  ", 7), ("42.0", 42), ("1", 1), ("100", 100)],
)
def test_valid_inputs_including_boundaries(raw, expected):
    assert parse_guess(raw, 1, 100) == (True, expected, None)


def test_range_check_is_skipped_without_bounds():
    assert parse_guess("-5") == (True, -5, None)


def test_unknown_difficulty_falls_back_to_normal():
    normal_range = get_range_for_difficulty("Normal")
    assert get_range_for_difficulty("Impossible") == normal_range
    assert get_attempt_limit("Impossible") == get_attempt_limit("Normal")


# ---- hot / cold hints -------------------------------------------------------

@pytest.mark.parametrize(
    "guess, secret, label",
    [
        (50, 50, "Bullseye"),
        (53, 50, "Hot"),
        (60, 50, "Warm"),
        (75, 50, "Cool"),
        (1, 100, "Cold"),
    ],
)
def test_temperature_labels(guess, secret, label):
    assert get_temperature(guess, secret, 1, 100)[0] == label


def test_temperature_scales_with_range():
    # 2 away is Hot on Normal (1-100) but only Warm on Easy (1-20)
    assert get_temperature(12, 10, 1, 100)[0] == "Hot"
    assert get_temperature(12, 10, 1, 20)[0] == "Warm"


# ---- high score file --------------------------------------------------------

def test_missing_high_score_file_returns_empty(tmp_path):
    assert load_high_scores(tmp_path / "nope.json") == {}


def test_corrupt_high_score_file_does_not_crash(tmp_path):
    path = tmp_path / "scores.json"
    path.write_text("{not json")
    assert load_high_scores(path) == {}
    path.write_text('["a list"]')
    assert load_high_scores(path) == {}


def test_high_score_only_saved_when_beaten(tmp_path):
    path = tmp_path / "scores.json"
    assert save_high_score(path, "Normal", 80) == ({"Normal": 80}, True)
    assert save_high_score(path, "Normal", 70) == ({"Normal": 80}, False)
    assert save_high_score(path, "Normal", 80) == ({"Normal": 80}, False)
    assert save_high_score(path, "Easy", 50)[1] is True
    assert load_high_scores(path) == {"Easy": 50, "Normal": 80}
