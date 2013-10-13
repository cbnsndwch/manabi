from settings import JDIC_AUDIO_SERVER_URL, JDIC_AUDIO_SERVER_TIMEOUT
from manabi.apps.flashcards.views.decorators import flashcard_api as api
from manabi.apps.flashcards.views.decorators import ApiException
from django.views.decorators.http import require_POST
import httplib


@api
#@require_POST
def audio_file_exists(request):
    '''
    Returns true or false, depending on whether the given filename exists
    on the JDic audio server.

    `filename` must be in the POST parameters.
    '''
    filename = request.POST['filename']

    conn = httplib.HTTPConnection(
        JDIC_AUDIO_SERVER_URL.lstrip('http://').rstrip('/audio/'),
        timeout=JDIC_AUDIO_SERVER_TIMEOUT)

    url = ''.join(['/audio/', filename])
    print url

    conn.request('HEAD', url)
    res = conn.getresponse()
    conn.close()

    if res.status == 200:
        return True
    elif res.status == 404:
        return False
    else:
        raise ApiException('Error communicating with JDic audio server.'
                            ' (HTTP {})'.format(res.status))
    
