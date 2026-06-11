# cashApp/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Transaction, Project


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model  = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(AuthenticationForm):
    class Meta:
        model  = CustomUser
        fields = ['username', 'password']


class ProjectForm(forms.ModelForm):
    class Meta:
        model  = Project
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Project এর নাম'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Project সম্পর্কে কিছু লিখুন (optional)'
            }),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model  = Transaction
        fields = ['title', 'amount', 'type', 'date']  # project field view থেকে set হবে
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount