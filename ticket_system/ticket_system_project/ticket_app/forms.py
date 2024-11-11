from django import forms
from .models import Ticket
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import CustomUser
from django.contrib.auth import authenticate

User = get_user_model()

class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput())

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        # Override to use email as the username for authentication
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        
        if email and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Invalid login credentials.")
            else:
                self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data

class TicketForm(forms.ModelForm):
    assigned_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Assign Users"
    )
    
    class Meta:
        model = Ticket
        fields = ["title", "description", "priority", "status"]

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea, required=True)

class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status"]

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name','password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        
        return cleaned_data

