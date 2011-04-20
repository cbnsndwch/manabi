from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail



urlpatterns = patterns('books.views',
    url(r'^$', 'book_list',
        name='book_list'),
    
    url(r'^(?P<object_id>\d+)/$', 'book_detail',
        name='book_detail_without_slug'),
    url(r'^(?P<object_id>\d+)/(?P<slug>[-\w]+)/$', 'book_detail',
        name='book_detail_with_slug'),
)


