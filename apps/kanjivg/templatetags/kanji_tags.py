from django import template
import settings

register = template.Library()

@register.inclusion_tag('kanjivg/stroke_diagram.html', takes_context=False)
def kanji_stroke_diagram(kanji):
    '''
    Renders a stroke diagram widget for the given kanji.
    '''
    # get the integer representation of the kanji
    ordinal = ord(kanji)

    return {
        'ordinal': ordinal,
    }

        
