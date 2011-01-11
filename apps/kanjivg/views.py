from flashcards.views.decorators import flashcard_api as api
from flashcards.views.decorators import ApiException
from django.views.decorators.http import require_GET
from django.http import HttpResponse
import settings

from lxml import etree
from StringIO import StringIO


@require_GET
def frames_json(request, ordinal):
    '''
    `ordinal` is the kanji's unicode ordinal.
    '''
    def bounding_box(svg_doc):
        '''Returns (x,y,) bounding box.'''
        attribs = svg_doc.getroot().attrib
        width, height = attribs['width'], attribs['height']
        return tuple(int(e.rstrip('px')) for e in (width, height,))

    xslt = open(settings.KANJI_SVG_XSLT_PATH, 'r').read()
    xslt_tree = etree.XML(xslt)

    file_path = ''.join([
        settings.KANJI_SVGS_PATH.rstrip('/') +
        '/' + str(ordinal) + '_frames.svg'])

    svg = open(file_path, 'r').read()
    doc = etree.parse(StringIO(svg))

    bounds = bounding_box(doc)

    svg_json = unicode(doc.xslt(xslt_tree))

    json = '{{width:{0},height:{1},data:{2}}}'.format(
        bounds[0], bounds[1], svg_json)

    # Aesthetic mods
    ################

    # Shorter dashes
    # Thinner, lighter grid lines
    # The thinner width makes the length much shorter too.
    #json = json.replace('Dash', 'ShortDot')
    json = json.replace(
        'color:"#ddd",width:"2",style:"Dash",',
        'color:"#ccc",width:"1",style:"Dash",')

    # Make the red circles semi-transparent
    json = json.replace('#FF2A00', 'rgba(255,42,0,.7)')
    

    return HttpResponse(json.encode('utf8'), mimetype='application/json')

