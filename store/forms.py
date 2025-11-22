from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    """Form for sellers to add or update products"""
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'compare_price', 'stock', 'category', 'major_category', 'image', 'available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your product...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'compare_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (optional)'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'major_category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        
        # Add help text
        self.fields['compare_price'].help_text = 'Original price if this product is on sale (optional)'
        self.fields['stock'].help_text = 'Number of items available for sale'
        self.fields['available'].help_text = 'Uncheck to hide this product from customers'
        
        # Make category field more user-friendly
        self.fields['category'].empty_label = "Select a category"
        self.fields['major_category'].empty_label = "Select a major category (optional)"
        
        # Filter major categories based on seller permissions
        if user and not user.is_superuser:
            if hasattr(user, 'seller_profile'):
                try:
                    seller_profile = user.seller_profile
                    allowed_categories = seller_profile.get_manageable_major_categories()
                    # Only show allowed major categories
                    choices = [choice for choice in Product.MAJOR_CATEGORY_CHOICES if choice[0] in allowed_categories]
                    if choices:
                        self.fields['major_category'].choices = choices
                    else:
                        # If no categories allowed, hide the field
                        del self.fields['major_category']
                except:
                    # If seller profile doesn't exist, hide major_category field
                    if 'major_category' in self.fields:
                        del self.fields['major_category']
        elif user and user.is_superuser:
            # Superusers can manage all categories
            self.fields['major_category'].choices = Product.MAJOR_CATEGORY_CHOICES
        else:
            # If no user provided, show all categories
            self.fields['major_category'].choices = Product.MAJOR_CATEGORY_CHOICES
        
        # Set initial values for new products
        if not self.instance.pk:
            self.fields['available'].initial = True
            
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('Price must be greater than zero.')
        return price
        
    def clean_compare_price(self):
        compare_price = self.cleaned_data.get('compare_price')
        price = self.cleaned_data.get('price')
        
        if compare_price is not None:
            if compare_price <= 0:
                raise forms.ValidationError('Compare price must be greater than zero.')
            if price is not None and compare_price <= price:
                raise forms.ValidationError('Compare price must be higher than the regular price.')
                
        return compare_price
        
    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('Stock cannot be negative.')
        return stock


class AdminProductForm(forms.ModelForm):
    """Form for administrators to add or update products with all fields"""
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'compare_price', 'stock', 'category', 'image', 'available', 'featured', 'approved', 'seller']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the product...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'compare_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00 (optional)'
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'approved': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'seller': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add help text
        self.fields['compare_price'].help_text = 'Original price if this product is on sale (optional)'
        self.fields['stock'].help_text = 'Number of items available for sale'
        self.fields['available'].help_text = 'Uncheck to hide this product from customers'
        self.fields['featured'].help_text = 'Check to feature this product on the homepage'
        self.fields['approved'].help_text = 'Check to approve this product for public viewing'
        
        # Make fields more user-friendly
        self.fields['category'].empty_label = "Select a category"
        self.fields['seller'].empty_label = "Select a seller"
        
        # Filter sellers to only show approved sellers
        from accounts.models import SellerProfile
        approved_sellers = SellerProfile.objects.filter(approval_status='approved').values_list('user_id', flat=True)
        self.fields['seller'].queryset = self.fields['seller'].queryset.filter(id__in=approved_sellers)
        
        # Set initial values for new products
        if not self.instance.pk:
            self.fields['available'].initial = True
            self.fields['approved'].initial = True