# -*- coding: utf-8 -*-

from django.test import TestCase
from japanese import (
        generate_reading, _furiganaize, _furiganaize_complex_compound_word)


class ReadingGenerationTest(TestCase):

    def test_compound_word(self):
        word = u'曲がり角'
        reading = generate_reading(word)
        self.assertTrue(u'かど' in reading)
        self.assertEqual(u'曲[ま]がり　角[かど]', reading)

    def test_furiganaize(self):
        word = u'角'
        reading = u'かど'
        translit = _furiganaize(word, reading, False)
        self.assertTrue(u'かど' in translit)

    def test_complex_compound_word_furiganaize(self):
        word = u'曲がり角'
        reading = u'まがりかど'
        ret = _furiganaize_complex_compound_word(word, reading)
        self.assertEqual(u'曲[ま]がり　角[かど]', ret)



