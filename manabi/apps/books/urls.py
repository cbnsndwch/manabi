from django.conf.urls import *
from django.conf import settings

from manabi.apps.utils.views import direct_to_template


urlpatterns = [
    url(r'^$', 'manabi.apps.books.views.book_list',
        name='book_list'),

    url(r'^(?P<object_id>\d+)/$', 'manabi.apps.books.views.book_detail',
        name='book_detail_without_slug'),
    url(r'^(?P<object_id>\d+)/(?P<slug>[-\w]+)/$', 'manabi.apps.books.views.book_detail',
        name='book_detail_with_slug'),
]
