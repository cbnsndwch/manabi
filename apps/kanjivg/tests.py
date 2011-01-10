# -*- coding: utf-8 -*-

from django.test import Client, TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.contrib.auth.models import User
import urllib
import settings


class KanjiVGTest(TestCase):
    def setUp(self):
        pass
        #self.filename = urllib.quote(u'きょう - 今日.mp3'.encode('utf8'))

    def tearDown(self):
        pass
        #dojango_settings.DOJO_SECURE_JSON = True
    
        
    def test_xslt(self):
        o = ord(u'今')

        res = self.client.get(reverse('kanjivg_frames_json', ordinal=o))

        self.assertEqual(res.status_code, 200)
        
        json = simplejson.loads(res.content)


