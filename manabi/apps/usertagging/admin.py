from django.contrib import admin
from manabi.apps.usertagging.models import Tag, UserTaggedItem
from manabi.apps.usertagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

admin.site.register(UserTaggedItem)
admin.site.register(Tag, TagAdmin)




