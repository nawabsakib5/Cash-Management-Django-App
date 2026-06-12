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
        fields = ['title', 'amount', 'type', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount


# ── Admin-only Forms ───────────────────────────────────────────────────────────

class AdminUserCreateForm(forms.ModelForm):
    """
    Admin dashboard থেকে নতুন user তৈরির form।
    Password manually set করা হয়, তাই password field আলাদা।
    """
    password  = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        min_length=8,
        label="Password"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model  = CustomUser
        fields = ['username', 'full_name', 'phone', 'email', 'user_type']
        widgets = {
            'username':  forms.TextInput(attrs={'placeholder': 'Username'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name (optional)'}),
            'phone':     forms.TextInput(attrs={'placeholder': 'Phone (optional)'}),
            'email':     forms.EmailInput(attrs={'placeholder': 'Email'}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Password দুটো মিলছে না।")
        return cleaned


class AdminUserEditForm(forms.ModelForm):
    """
    Admin dashboard থেকে existing user edit করার form।
    Password এখানে change হবে না — আলাদা flow।
    """
    class Meta:
        model  = CustomUser
        fields = ['username', 'full_name', 'phone', 'email', 'user_type', 'is_frozen']
        widgets = {
            'username':  forms.TextInput(attrs={'placeholder': 'Username'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'phone':     forms.TextInput(attrs={'placeholder': 'Phone'}),
            'email':     forms.EmailInput(attrs={'placeholder': 'Email'}),
        }