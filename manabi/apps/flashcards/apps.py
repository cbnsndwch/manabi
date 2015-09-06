from django.apps import AppConfig


class FlashcardsConfig(AppConfig):
    name = 'flashcards'
    verbose_name = "Flashcards"

    def ready(self):
        import manabi.apps.flashcards.cacheinvalidators
        import manabi.apps.flashcards.signals
