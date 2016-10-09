# -*- coding: utf-8 -*-


NOUN = 'n'
VERB = 'v'
ADJECTIVE = 'adj'
ADVERB = 'adv'
PREPOSITION = 'prep'
PRONOUN = 'pn'
PROPER_NOUN = 'prpn'
PHRASE = 'phr'
ABBREVIATION = 'abbr'
CONJUNCTION = 'conj'
INTERROGATIVE = 'intr'
AUXILLIARY_VERB = 'auxv'
PARTICLE = 'prt'
EXPRESSION = 'expr'
IDIOMATIC_EXPRESSION = 'idio'

PHRASAL_VERB = 'phrv'
INTERJECTION = 'int'
VERBAL_NOUN = 'vn'
ADVERBIAL_NOUN = 'advn'
ADJECTIVAL_NOUN = 'adjn'
KANA = 'kana'
PREFIX = 'pref'
SUFFIX = 'suff'
DETERMINER = 'det' #?
NUMERIC = 'num'
COUNTER = 'cnt'

PART_OF_SPEECH_EXAMPLES = {
    NOUN: 'boat, 船'
}

BASIC_PART_OF_SPEECH_CHOICES = (
    (NOUN, 'Noun'),
    (VERB, 'Verb'),
    (ADJECTIVE, 'Adjective'),
    (ADVERB, 'Adverb'),
    (PREPOSITION, 'Preposition'),
    (PRONOUN, 'Pronoun'),
    (PROPER_NOUN, 'Proper Noun'),
    (PHRASE, 'Phrase'),
    (ABBREVIATION, 'Abbreviation'),
    (CONJUNCTION, 'Conjunction'),
    (INTERROGATIVE, 'Interrogative'),
    (AUXILLIARY_VERB, 'Auxilliary Verb'),
    (PARTICLE, 'Particle'),
    (EXPRESSION, 'Expression'),
    (KANA, 'Kana'),
)

MORE_PART_OF_SPEECH_CHOICES = (
    (PHRASAL_VERB, 'Phrasal Verb'),
    (INTERJECTION, 'Interjection'),
    (VERBAL_NOUN, 'Verbal Noun'),
    (ADVERBIAL_NOUN, 'Adverbial Noun'),
    (ADJECTIVAL_NOUN, 'Adjectival Noun'),
    (PREFIX, 'Prefix'),
    (SUFFIX, 'Suffix'),
    (DETERMINER, 'Determiner'),
    (IDIOMATIC_EXPRESSION, 'Idiomatic Expression'),
    (NUMERIC, 'Numeric'),
    (COUNTER, 'Counter'),
)

ALL_PART_OF_SPEECH_CHOICES = BASIC_PART_OF_SPEECH_CHOICES + MORE_PART_OF_SPEECH_CHOICES
