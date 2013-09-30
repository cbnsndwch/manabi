from django.conf.urls.defaults import *

urlpatterns = patterns('jdic.views',
    url(r'^audio-file-exists/$',
        'audio_file_exists',
        name='jdic_audio_file_exists'),
)
