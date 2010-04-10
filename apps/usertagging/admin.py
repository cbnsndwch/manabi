from django.contrib import admin
from usertagging.models import Tag, UserTaggedItem
from usertagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

admin.site.register(UserTaggedItem)
admin.site.register(Tag, TagAdmin)




