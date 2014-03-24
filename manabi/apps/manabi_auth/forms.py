from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext, ugettext_lazy as _


class UserCreationForm(forms.ModelForm):
    '''
    A form that creates a user, with no privileges, from the given username,
    email and password.
    '''
    error_messages = {
        'duplicate_username': _("A user with that username already exists."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    username = forms.RegexField(
        label=_("Username"),
        min_length=3,
        max_length=30,
        regex=r'^[\w]+$',
        help_text=_("Required. 3-30 characters. Letters, digits and "
                    "underscores only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "underscores.")})
    password = forms.CharField(
        min_length=5,
        label=_("Password"),
        widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email',)

    def clean_username(self):
        # Since User.username is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        username = self.cleaned_data['username']
        try:
            User._default_manager.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            self.error_messages['duplicate_username'],
            code='duplicate_username',
        )

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

