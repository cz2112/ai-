"""Unit tests for the SM-2 spaced repetition algorithm."""

from datetime import datetime, timezone, timedelta
from app.services.spaced_repetition import sm2_algorithm


class TestSM2Algorithm:
    """Verify SM-2 algorithm behaviour for various quality ratings."""

    def test_perfect_response(self):
        """Quality 5 (perfect) on a fresh card should set interval=1, reps=1."""
        reps, ease, interval, next_review = sm2_algorithm(
            quality=5, repetitions=0, easiness=2.5, interval=0
        )
        assert reps == 1
        assert interval == 1
        # Easiness should increase for a perfect answer
        assert ease > 2.5
        assert isinstance(next_review, datetime)
        # next_review should be roughly 1 day from now
        expected = datetime.now(timezone.utc) + timedelta(days=1)
        assert abs((next_review - expected).total_seconds()) < 5

    def test_failed_response(self):
        """Quality 1 (failure) should reset repetitions to 0 and interval to 1."""
        reps, ease, interval, next_review = sm2_algorithm(
            quality=1, repetitions=5, easiness=2.5, interval=30
        )
        assert reps == 0
        assert interval == 1
        # Easiness should decrease for a bad answer but stay >= 1.3
        assert ease >= 1.3

    def test_borderline_response(self):
        """Quality 3 (barely correct) should still count as correct."""
        reps, ease, interval, next_review = sm2_algorithm(
            quality=3, repetitions=0, easiness=2.5, interval=0
        )
        # Quality >= 3 is correct, so reps should increment
        assert reps == 1
        assert interval == 1
        # Easiness should decrease slightly for quality=3
        assert ease < 2.5

    def test_easiness_factor_minimum(self):
        """Easiness factor must never drop below 1.3, even with repeated failures."""
        ease = 1.3
        for _ in range(10):
            _reps, ease, _interval, _next = sm2_algorithm(
                quality=0, repetitions=0, easiness=ease, interval=1
            )
        assert ease >= 1.3
