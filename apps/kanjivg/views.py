# Create your views here.

from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import ApiException
from django.views.decorators.http import require_GET
from django.http import HttpResponse
import settings

from lxml import etree


@require_GET
def frames_json(request, ordinal):
    '''
    `ordinal` is the kanji's unicode ordinal.
    '''
    xslt = open(settings.KANJI_SVG_XSLT_PATH, 'r').read()
    xslt_tree = etree.XML(xslt)

    file_path = ''.join([
        settings.KANJI_SVGS_PATH.rstrip('/') +
        '/' + str(ordinal) + '.svg'])

    svg = open(file_path, 'r').read()

    doc = etree.parse(StringIO(svg))

    json = unicode(doc.xslt(xslt_tree))
    
    return HttpResponse(json, mimetype='application/json')

