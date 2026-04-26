from datetime import datetime, timedelta, timezone


def sm2_algorithm(quality: int, repetitions: int, easiness: float, interval: int):
    """SuperMemo SM-2 algorithm for spaced repetition.
    
    quality: 0-5 (0=complete blackout, 5=perfect response)
    Returns: (repetitions, easiness, interval, next_review)
    """
    if quality >= 3:  # correct response
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness)
        repetitions += 1
    else:  # incorrect
        repetitions = 0
        interval = 1

    easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    next_review = datetime.now(timezone.utc) + timedelta(days=interval)
    return repetitions, easiness, interval, next_review
