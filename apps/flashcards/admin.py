from flashcards.models import Deck, FactType, Fact, CardTemplate, FieldType, Card, FieldContent, SchedulingOptions, SharedDeck, ReviewStatistics, CardHistory
from django.contrib import admin


class CardAdmin(admin.ModelAdmin):
    exclude = ('synchronized_with',)
    list_display = ('__unicode__', 'last_due_at', 'due_at', 'last_reviewed_at',)

class FactTypeAdmin(admin.ModelAdmin):
    pass

class FieldTypeAdmin(admin.ModelAdmin):
    exclude = ('choices',)

admin.site.register(Deck)
admin.site.register(FactType, FactTypeAdmin)
admin.site.register(Fact)
admin.site.register(CardTemplate)
admin.site.register(FieldType, FieldTypeAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(FieldContent)
admin.site.register(SchedulingOptions)
