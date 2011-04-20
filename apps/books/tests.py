from django.test import TestCase
from models import Textbook


class SimpleTest(TestCase):
    def setUp(self):
        self.book = Textbook(isbn='4789011623') # Genki textbook

    def test_get_image_url(self):
        urls = self.book.get_image_urls()
        self.assertTrue(urls)
        self.assertTrue(urls['medium'])
        self.assertTrue('images-amazon.com/images' in urls['small'])

    def test_get_info(self):
        info = self.book.get_basic_info()
        self.assertTrue('Banno' in info['author'],
                        'Expected Banno in author, got ' + info['author'])
        self.assertTrue('Genki' in info['title'])


