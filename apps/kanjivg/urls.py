from django.conf.urls.defaults import *

# place app url patterns here
urlpatterns = patterns('kanjivg.views',
    url(r'^frames/(?P<ordinal>\d+).json$',
        'frames_json',
        name='kanjivg_frames_json'),
)
