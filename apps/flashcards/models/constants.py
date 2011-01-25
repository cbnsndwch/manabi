
# Grade IDs (don't change these once they're set)
GRADE_NONE = 0
GRADE_HARD = 3
GRADE_GOOD = 4
GRADE_EASY = 5
ALL_GRADES = [GRADE_NONE, GRADE_HARD, GRADE_GOOD, GRADE_EASY]

GRADE_NAMES = {
    GRADE_NONE: 'Wrong',
    GRADE_HARD: 'Hard',
    GRADE_GOOD: 'Good',
    GRADE_EASY: 'Too Easy',
}


ISO_639_2_LANGUAGES = (
    ('eng', 'English',),
    ('jpn', 'Japanese',),
    
    ('ara', 'Arabic',),
    ('zho', 'Chinese',),
    ('dan', 'Danish',),
    ('nld', 'Dutch',),
    ('epo', 'Esperanto',),
    ('fra', 'French',),
    ('deu', 'German',),
    ('ell', 'Greek',),
    ('heb', 'Hebrew',),
    ('hin', 'Hindi',),
    ('hun', 'Hungarian',),
    ('isl', 'Icelandic',),
    ('ind', 'Indonesia',),
    ('ita', 'Italian',),
    ('kor', 'Korean',),
    ('lat', 'Latin',),
    ('jbo', 'Lojban',),
    ('mal', 'Malay',),
    ('nor', 'Norwegian',),
    ('pol', 'Polish',),
    ('por', 'Portuguese',),
    ('ron', 'Romanian',),
    ('srp', 'Seberian',),
    ('slv', 'Slovenian',),
    ('rus', 'Russian',),
    ('san', 'Sanskrit',),
    ('spa', 'Spanish',),
    ('swa', 'Swahili',),
    ('tgl', 'Tagalog',),
    ('tha', 'Thai',),
    ('tur', 'Turkish',),
    ('ukr', 'Ukranian',),
    ('urd', 'Urdu',),
    ('vie', 'Vietnamese',),
    ('cym', 'Welsh',),
    ('yid', 'Yiddish',),
)


# used for randomizing new card insertion
MAX_NEW_CARD_ORDINAL = 10000000
                      #4294967295 is the upper bound


#below is used in the EF equation, but we're going to precompute the EF factors
#GRADE_FACTORS = {GRADE_NONE: 0, GRADE_HARD: 3, GRADE_GOOD: 4, GRADE_EASY: 5}
#this is the EF algorithm from which the EF factors are computed:
#ease_factor = self.ease_factor + (0.1 - (max_grade - grade_factor) * (0.08 + (max_grade - grade_factor) * 0.02))

#MAX_EASE_FACTOR_STEP = 0.1

#these are the precomputed values, so that we can modify them independently later to test their effectiveness:
EASE_FACTOR_MODIFIERS = {GRADE_NONE: -0.3, GRADE_HARD: -0.1401, GRADE_GOOD: 0.0, GRADE_EASY: 0.1} #TODO accurate grade_none value


YOUNG_FAILURE_INTERVAL = (1.0 / (24.0 * 60.0)) * 10.0 #10 mins, expressed in days
#MATURE_FAILURE_INTERVAL = (1.0 / (24 * 60)) * 10 #10 mins, expressed in days
MATURE_FAILURE_INTERVAL = 1.0 #1 day#(1.0 / (24 * 60)) * 10 #10 mins, expressed in days
#TODO MATURE_FAILURE_INTERVAL should not be a constant value, but dependent on other factors of a given card
#TODO 'tomorrow' should also be dependent on the current time, instead of just 1 day from now

# Days an interval is required to meet or exceed for a card to be 
# considered mature.
MATURE_INTERVAL_MIN = 20.0

GRADE_EASY_BONUS_FACTOR = 0.2
DEFAULT_EASE_FACTOR = 2.5

#TODO make _next_interval/ease_factor into class methods?

# When intervals are set, they are fuzzed by at most this value, -/+
INTERVAL_FUZZ_MAX = 0.035

NEW_CARDS_PER_DAY = 200 #TODO this should at least be an option, but should also scale to use

#number of failed cards before failed cards are shown earlier than any due cards
#TODO MAX_FAILED_CARDS = 20 #TODO should be option.

# 1: mature due (-interval)
# 2: young due
# 3: failed, not due
#
#
