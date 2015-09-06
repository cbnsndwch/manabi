from django.contrib import admin

from pinax.apps.signup_codes.models import SignupCode


class SignupCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "max_uses", "use_count", "expiry", "created"]
    search_fields = ["code", "email"]
    list_filter = ["created"]


#TODO admin.site.register(SignupCode, SignupCodeAdmin)
