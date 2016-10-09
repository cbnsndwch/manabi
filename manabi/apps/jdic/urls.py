from django.conf.urls import *


urlpatterns = [
    url(r'^audio-file-exists/$',
        'manabi.apps.stats.views.audio_file_exists',
        name='jdic_audio_file_exists'),
]
