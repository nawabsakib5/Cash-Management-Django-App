from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Transaction, Project, Category, SubCategory


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
                'placeholder': 'Project name'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Project description (optional)'
            }),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model  = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Food, Transport, Salary…'
            }),
        }


class SubCategoryForm(forms.ModelForm):
    class Meta:
        model  = SubCategory
        fields = ['category', 'name', 'users']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Lunch, Taxi, Bonus…'
            }),
            'users': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': 6,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset    = Category.objects.all()
        self.fields['category'].empty_label = 'Select a category'
        self.fields['users'].queryset  = CustomUser.objects.filter(
            user_type='user'
        ).order_by('username')
        self.fields['users'].required  = False
        self.fields['users'].label     = 'Restrict to users (optional)'



class UserSubCategoryForm(forms.Form):
    
    subcategories = forms.ModelMultipleChoiceField(
        queryset=SubCategory.objects.all(),
        required=False,
        label='Assign Existing Sub-categories',
        widget=forms.CheckboxSelectMultiple(),
    )

    new_sub_category   = forms.CharField(
        max_length=100,
        required=False,
        label='New Sub-category Name',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Bonus, Taxi…'}),
    )
    new_sub_category_cat = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Category for new sub-category',
        empty_label='Select category',
    )

    def clean(self):
        cleaned = super().clean()
        new_name = cleaned.get('new_sub_category', '').strip()
        new_cat  = cleaned.get('new_sub_category_cat')

        if new_name and not new_cat:
            raise forms.ValidationError(
                "Please select a category for the new sub-category."
            )
        return cleaned


class TransactionForm(forms.ModelForm):
    class Meta:
        model  = Transaction
        fields = ['title', 'amount', 'type', 'date', 'category', 'sub_category']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset    = Category.objects.all()
        self.fields['category'].empty_label = 'Select category (optional)'
        self.fields['category'].required    = False

        self.fields['sub_category'].queryset    = SubCategory.objects.none()
        self.fields['sub_category'].empty_label = 'Select sub-category (optional)'
        self.fields['sub_category'].required    = False

        if self.user is not None:
            visible_subs = SubCategory.objects.filter(
                models.Q(users__isnull=True) | models.Q(users=self.user)
            ).distinct()
        else:
            visible_subs = SubCategory.objects.filter(users__isnull=True)

        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['sub_category'].queryset = visible_subs.filter(
                    category_id=category_id
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.category:
            self.fields['sub_category'].queryset = visible_subs.filter(
                category=self.instance.category
            )

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Amount must be greater than 0.")
        return amount


class AdminUserCreateForm(forms.ModelForm):
    password = forms.CharField(
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
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class AdminUserEditForm(forms.ModelForm):
    class Meta:
        model  = CustomUser
        fields = ['username', 'full_name', 'phone', 'email', 'user_type', 'is_frozen']
        widgets = {
            'username':  forms.TextInput(attrs={'placeholder': 'Username'}),
            'full_name': forms.TextInput(attrs={'placeholder': 'Full Name'}),
            'phone':     forms.TextInput(attrs={'placeholder': 'Phone'}),
            'email':     forms.EmailInput(attrs={'placeholder': 'Email'}),
        }