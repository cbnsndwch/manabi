from django.contrib import admin
from usertagging.models import Tag, TaggedItem
from usertagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

admin.site.register(TaggedItem)
admin.site.register(Tag, TagAdmin)




