from flashcards.models import Deck, FactType, Fact, CardTemplate, FieldType, Card, FieldContent, SchedulingOptions
from django.contrib import admin


class CardAdmin(admin.ModelAdmin):
    exclude = ('synchronized_with',)


admin.site.register(Deck)
admin.site.register(FactType)
admin.site.register(Fact)
admin.site.register(CardTemplate)
admin.site.register(FieldType)
admin.site.register(Card, CardAdmin)
admin.site.register(FieldContent)
admin.site.register(SchedulingOptions)
