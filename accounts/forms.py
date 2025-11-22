from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, SellerProfile
from store.models import Product


class CustomerRegistrationForm(forms.Form):
    """Form for customer registration"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'required': True
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'required': True
        }),
        help_text='Enter the same password as above, for verification.'
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        
        # Generate username from email
        username = email.split('@')[0]
        username = ''.join(c for c in username if c.isalnum() or c in ['_', '-'])
        if not username:
            username = 'user'
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile with customer role
        Profile.objects.create(user=user, role='customer')
        
        return user


class SellerRegistrationForm(forms.Form):
    """Form for seller registration with business details"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email address',
            'required': True
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password',
            'required': True
        }),
        min_length=8,
        help_text='Password must be at least 8 characters long.'
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'required': True
        }),
        help_text='Enter the same password as above, for verification.'
    )
    business_name = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business Name',
            'required': True
        })
    )
    business_description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe your business',
            'required': True
        })
    )
    business_address = forms.CharField(
        required=True,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business Address',
            'required': True
        })
    )
    business_phone = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business Phone',
            'required': True
        })
    )
    business_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Business Email',
            'required': True
        })
    )
    tax_id = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tax ID (optional)'
        })
    )
    bank_account = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bank Account (optional)'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password1']
        business_name = self.cleaned_data['business_name']
        business_description = self.cleaned_data['business_description']
        business_address = self.cleaned_data['business_address']
        business_phone = self.cleaned_data['business_phone']
        business_email = self.cleaned_data['business_email']
        tax_id = self.cleaned_data.get('tax_id', '')
        bank_account = self.cleaned_data.get('bank_account', '')
        
        # Generate username from email
        username = email.split('@')[0]
        username = ''.join(c for c in username if c.isalnum() or c in ['_', '-'])
        if not username:
            username = 'seller'
        
        # Ensure username is unique
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Create profile with seller role
        profile = Profile.objects.create(user=user, role='seller')
        
        # Create seller profile
        SellerProfile.objects.create(
            user=user,
            business_name=business_name,
            business_description=business_description,
            business_address=business_address,
            business_phone=business_phone,
            business_email=business_email,
            tax_id=tax_id,
            bank_account=bank_account,
            approval_status='pending'
        )
        
        return user


class ProfileUpdateForm(forms.ModelForm):
    """Form for users to update their profile"""
    
    class Meta:
        model = Profile
        fields = ['phone', 'gender', 'date_of_birth', 'address', 'city', 'state', 'zipcode', 'country']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'zipcode': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Make phone field required
        self.fields['phone'].required = False
        
        # Set initial values
        if self.instance and self.instance.pk:
            # If profile exists, populate fields
            pass
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Add phone validation if needed
            pass
        return phone
    
    def clean(self):
        cleaned_data = super().clean()
        # Add cross-field validation if needed
        return cleaned_data
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
        return profile


class SellerProfileUpdateForm(forms.ModelForm):
    """Form for sellers to update their seller profile"""
    
    class Meta:
        model = SellerProfile
        fields = ['business_name', 'business_description', 'business_address', 'business_phone', 'business_email', 'tax_id', 'bank_account']
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'business_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'business_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'business_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'business_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make description field larger
        if 'business_description' in self.fields:
            self.fields['business_description'].widget.attrs['rows'] = 3


class SellerProfileAdminForm(forms.ModelForm):
    """Custom admin form for SellerProfile with checkbox widget for major categories"""
    
    allowed_major_categories = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'major-category-checkboxes'
        }),
        choices=[],
        help_text='Select major categories this seller can manage. Leave all unchecked to restrict access (seller will not see major category field).'
    )
    
    class Meta:
        model = SellerProfile
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get major category choices from Product model (excluding 'none')
        self.fields['allowed_major_categories'].choices = [
            choice for choice in Product.MAJOR_CATEGORY_CHOICES 
            if choice[0] != 'none'
        ]
        
        # Set initial value from JSON field
        if self.instance and self.instance.pk:
            if self.instance.allowed_major_categories:
                self.fields['allowed_major_categories'].initial = self.instance.allowed_major_categories
            else:
                self.fields['allowed_major_categories'].initial = []
        else:
            self.fields['allowed_major_categories'].initial = []
    
    def clean_allowed_major_categories(self):
        """Convert selected categories to JSON list"""
        selected = self.cleaned_data.get('allowed_major_categories', [])
        # Return as list (Django's JSONField will handle conversion)
        return selected if selected else []
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # The JSONField will automatically handle the list conversion
        instance.allowed_major_categories = self.cleaned_data.get('allowed_major_categories', [])
        if commit:
            instance.save()
        return instance