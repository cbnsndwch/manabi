from django.contrib import admin
from manabi.apps.usertagging.models import Tag, UserTaggedItem
from manabi.apps.usertagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

#TODO admin.site.register(UserTaggedItem)
#TODO admin.site.register(Tag, TagAdmin)




