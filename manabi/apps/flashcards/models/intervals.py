import random

from constants import GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY

DEFAULT_INTERVALS = {
    GRADE_NONE: (20.0/(24.0*60.0), 25.0/(24.0*60.0)),
    #cards.GRADE_mature_unknown': (0.333, 0.333),
    GRADE_HARD: (0.333, 0.5),
    GRADE_GOOD: (3.0, 5.0),
    GRADE_EASY: (7.0, 9.0),
}


def _generate_interval(min_duration, max_duration):
    #TODO favor (random.triangular) conservatism
    return random.uniform(min_duration, max_duration) 

def initial_interval(deck, grade, do_fuzz=True):
    '''
    Generates an initial interval duration for a new card that's been reviewed.
    '''
    min_, max_ = DEFAULT_INTERVALS[grade]
    
    if do_fuzz:
        return _generate_interval(min_, max_)
    return (min_ + max_) / 2.0

