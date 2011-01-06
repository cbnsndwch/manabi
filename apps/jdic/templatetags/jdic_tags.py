from django import template
import settings

register = template.Library()

@register.inclusion_tag('jdic/audio_player.html', takes_context=False)
def jdic_audio_player(kanji, kana, autoplay=True):
    '''
    Renders a JDic audio player widget for the given kana and kanji.
    '''
    audio_server = settings.JDIC_AUDIO_SERVER_URL
    return {
        'audio_server': audio_server,
        'kana': kana,
        'kanji': kanji,
        'autoplay': str(autoplay).lower()
    }
        
