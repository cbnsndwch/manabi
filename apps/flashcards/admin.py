from flashcards.models import Deck, FactType, Fact, CardTemplate, \
    FieldType, Card, FieldContent, SchedulingOptions, \
    ReviewStatistics, CardHistory
from books.models import Textbook
from django.contrib import admin


class CardAdmin(admin.ModelAdmin):
    raw_id_fields = ('fact',)
    list_display = ('__unicode__', 'last_due_at', 'due_at', 'last_reviewed_at',)

class FactAdmin(admin.ModelAdmin):
    raw_id_fields = ('synchronized_with', 'parent_fact',)
    list_display = ('__unicode__', 'owner',)
    list_filter = ('deck',)
    readonly_fields = ('created_at', 'modified_at',)

class DeckAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'owner',)
    list_filter = ('owner',)
    readonly_fields = ('created_at', 'modified_at',)

class FactTypeAdmin(admin.ModelAdmin):
    pass

class FieldTypeAdmin(admin.ModelAdmin):
    exclude = ('choices',)

class TextbookAdmin(admin.ModelAdmin):
    pass


admin.site.register(Deck, DeckAdmin)
admin.site.register(CardHistory)
admin.site.register(ReviewStatistics)
admin.site.register(FactType, FactTypeAdmin)
admin.site.register(Fact, FactAdmin)
admin.site.register(CardTemplate)
admin.site.register(FieldType, FieldTypeAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(FieldContent)
admin.site.register(SchedulingOptions)
admin.site.register(Textbook)
