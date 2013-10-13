from django.conf.urls import *
from django.conf import settings

from manabi.apps.utils.views import direct_to_template


urlpatterns = patterns('manabi.apps.books.views',
    url(r'^$', 'book_list',
        name='book_list'),
    
    url(r'^(?P<object_id>\d+)/$', 'book_detail',
        name='book_detail_without_slug'),
    url(r'^(?P<object_id>\d+)/(?P<slug>[-\w]+)/$', 'book_detail',
        name='book_detail_with_slug'),
)

