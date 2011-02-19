from account.forms import SignupForm as PinaxSignupForm

class PinaxLazyConvertForm(PinaxSignupForm):
    '''
    `PinaxSignupForm` is a subclass of forms.Form.
    django-lazysignup expects this form to behave like a ModelForm.
    So it will pass `instance` to __init__, which we will save to use 
    later when we create the user when the form is saved.
    '''
    def __init__(self, *args, **kwargs):
        self.instance = None
        if 'instance' in kwargs:
            # PinaxSignupForm breaks if we pass it this
            self.instance = kwargs.pop('instance')
        super(PinaxLazyConvertForm, self).__init__(*args, **kwargs)

    def create_user(self, username=None, commit=True):
        '''Gets called by PinaxSignupForm.save'''
        user = self.instance or User()
        if username is None:
            raise NotImplementedError("SignupForm.create_user does not handle "
                "username=None case. You must override this method.")
        user.username = username
        user.email = self.cleaned_data["email"].strip().lower()
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user

    def get_credentials(self):
        return {
            'username': self.cleaned_data['username'],
            'password': self.cleaned_data['password1']
        }



