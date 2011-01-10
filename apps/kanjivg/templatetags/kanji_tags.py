from django import template
import settings

register = template.Library()

FILENAME_TEMPLATE = '{}_frames.json'

@register.inclusion_tag('kanjivg/stroke_diagram.html', takes_context=False)
def kanji_stroke_diagram(kanji):
    '''
    Renders a JDic audio player widget for the given kana and kanji.
    '''
    # get the integer representation of the kanji
    ordinal = ord(kanji)

    filename = FILENAME_TEMPLATE.format(ordinal)

    return {
        'filename': filename,
    }

        
