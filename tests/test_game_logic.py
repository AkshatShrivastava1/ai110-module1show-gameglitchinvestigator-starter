from logic_utils import check_guess, get_range_for_difficulty, update_score


# Starter tests, updated: check_guess returns (outcome, message), so unpack it.
def test_winning_guess():
    # If the secret is 50 and guess is 50, it should be a win
    outcome, _ = check_guess(50, 50)
    assert outcome == "Win"


def test_guess_too_high():
    # If secret is 50 and guess is 60, hint should be "Too High"
    outcome, _ = check_guess(60, 50)
    assert outcome == "Too High"


def test_guess_too_low():
    # If secret is 50 and guess is 40, hint should be "Too Low"
    outcome, _ = check_guess(40, 50)
    assert outcome == "Too Low"


# Regression tests for the bugs logged in reflection.md section 1.
def test_too_high_hint_says_go_lower():
    # Bug 1: a guess above the secret used to say "Go HIGHER!"
    _, message = check_guess(60, 50)
    assert "LOWER" in message


def test_too_low_hint_says_go_higher():
    # Bug 1: a guess below the secret used to say "Go LOWER!"
    _, message = check_guess(40, 50)
    assert "HIGHER" in message


def test_single_digit_guess_is_too_low_not_string_compared():
    # Bug 2: "9" > "50" as strings, so 9 used to come back "Too High"
    outcome, _ = check_guess(9, 50)
    assert outcome == "Too Low"


def test_wrong_guess_never_adds_points():
    # Bug 3: "Too High" on an even attempt used to give +5
    for attempt in range(1, 9):
        assert update_score(0, "Too High", attempt) == -5
        assert update_score(0, "Too Low", attempt) == -5


def test_first_try_win_scores_100():
    # Bug 8: off-by-one meant a first-try win paid 80
    assert update_score(0, "Win", 1) == 100
    assert update_score(0, "Win", 2) == 90


def test_hard_range_is_wider_than_normal():
    # Bug 6: Hard was 1-50, narrower than Normal's 1-100
    _, normal_high = get_range_for_difficulty("Normal")
    _, hard_high = get_range_for_difficulty("Hard")
    assert hard_high > normal_high
