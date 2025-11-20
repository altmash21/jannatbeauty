# 🛍️ Jannat Beauty E-Commerce Platform - Complete Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Installation & Setup](#installation--setup)
4. [Configuration Guide](#configuration-guide)
5. [Features & Functionality](#features--functionality)
6. [User Roles & Access](#user-roles--access)
7. [Admin Panel Guide](#admin-panel-guide)
8. [Payment Gateway Setup](#payment-gateway-setup)
9. [Shipping Integration](#shipping-integration)
10. [Email Configuration](#email-configuration)
11. [Database Management](#database-management)
12. [Deployment Guide](#deployment-guide)
13. [Maintenance & Support](#maintenance--support)
14. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**Jannat Beauty** is a comprehensive multi-vendor e-commerce platform built with Django 5.2.8, designed specifically for beauty and cosmetics retail in the Indian market.

### Key Highlights
- **Multi-Vendor Marketplace**: Support for multiple sellers with approval workflow
- **Payment Integration**: Razorpay payment gateway (UPI, Cards, Wallets, Net Banking)
- **Shipping Automation**: Shiprocket integration for automated logistics
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **Inventory Management**: Real-time stock tracking and out-of-stock indicators
- **Coupon System**: Discount codes and promotional campaigns
- **Review System**: Customer reviews and ratings for products

### Technology Stack
- **Backend**: Django 5.2.8 (Python 3.10.11)
- **Database**: SQLite (Development) / PostgreSQL (Production Recommended)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **Payment**: Razorpay Payment Gateway
- **Shipping**: Shiprocket API
- **Media Storage**: Cloudinary (Images & Static Files)
- **Caching**: Redis
- **Icons**: Font Awesome 6.4.0

---

## 💻 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS
- **Python**: Version 3.10 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Stable connection for API integrations

### Software Dependencies
- Python 3.10.11
- pip (Python package manager)
- Virtual environment tool (venv)
- Git (for version control)
- Web browser (Chrome, Firefox, Safari, Edge)

---

## 🚀 Installation & Setup

### Step 1: Clone the Project
```bash
cd D:\your-project-folder
# Project files should be in this directory
```

### Step 2: Create Virtual Environment
```powershell
# Navigate to project directory
cd D:\lol

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

### Step 3: Install Dependencies
```powershell
# Install all required packages
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the project root directory:

```env
# Django Settings
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
# DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Razorpay Configuration
RAZORPAY_ENABLED=True
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret

# Shiprocket Configuration
SHIPROCKET_ENABLED=True
SHIPROCKET_API_EMAIL=your_shiprocket_email
SHIPROCKET_API_PASSWORD=your_shiprocket_password

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=your_email@gmail.com

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Redis Configuration (Optional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# CSRF Trusted Origins (Add your domain)
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### Step 5: Database Setup
```powershell
# Run database migrations
python manage.py migrate

# Create superuser account
python manage.py createsuperuser
# Enter username, email, and password when prompted
```

### Step 6: Load Initial Data (Optional)
```powershell
# Create sample categories
python manage.py shell
```
```python
from store.models import Category
Category.objects.create(name="Skincare", description="Skincare products")
Category.objects.create(name="Makeup", description="Makeup and cosmetics")
Category.objects.create(name="Haircare", description="Hair care products")
Category.objects.create(name="Fragrance", description="Perfumes and fragrances")
exit()
```

### Step 7: Run Development Server
```powershell
python manage.py runserver
```

**Access the application:**
- Website: http://127.0.0.1:8000
- Admin Panel: http://127.0.0.1:8000/admin

---

## ⚙️ Configuration Guide

### 1. Generate Secret Key
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Copy the output and set it as `SECRET_KEY` in your `.env` file.

### 2. Razorpay Setup (Payment Gateway)
1. Sign up at https://razorpay.com
2. Navigate to Settings → API Keys
3. Generate Test/Live API Keys
4. Copy Key ID and Key Secret to `.env` file
5. Configure webhook URL: `https://yourdomain.com/orders/razorpay/verify/`

**Test Credentials** (for development):
- Test Card: 4111 1111 1111 1111
- CVV: Any 3 digits
- Expiry: Any future date

### 3. Shiprocket Setup (Shipping)
1. Sign up at https://www.shiprocket.in
2. Get API credentials from Settings
3. Add email and password to `.env` file
4. Configure pickup address in Shiprocket dashboard
5. Set up courier preferences

### 4. Cloudinary Setup (Image Hosting)
1. Sign up at https://cloudinary.com
2. Get credentials from Dashboard
3. Add to `.env` file
4. Media files will automatically upload to Cloudinary

### 5. Email Configuration
For Gmail:
1. Enable 2-Factor Authentication
2. Generate App Password: Google Account → Security → App Passwords
3. Use App Password in `.env` (not your regular password)

---

## 🎨 Features & Functionality

### Customer Features
✅ **User Registration & Login**
- Email/Username based registration
- OTP verification for new accounts
- Password reset functionality
- Customer dashboard with order history

✅ **Product Browsing**
- Browse by categories and subcategories
- Search functionality
- Product filtering and sorting
- Featured products and new arrivals
- Product detail pages with images and descriptions

✅ **Shopping Cart**
- Add/remove products
- Update quantities
- Apply coupon codes
- Real-time price calculations
- Stock validation
- Cart persists across sessions

✅ **Checkout Process**
- Auto-filled customer information
- Address management
- Multiple payment options (Razorpay)
- Order summary with pricing breakdown
- Secure payment processing

✅ **Order Management**
- Order confirmation
- Order tracking with AWB number
- Order history in customer dashboard
- Email notifications for order updates
- Order status: Pending → Processing → Shipped → Delivered

✅ **Reviews & Ratings**
- Submit product reviews
- Star ratings (1-5)
- View all product reviews

### Seller Features
✅ **Seller Registration**
- Separate seller registration form
- Business information collection
- Tax ID and banking details
- Approval workflow

✅ **Seller Dashboard**
- Business profile management
- Add/edit/delete products
- Inventory management
- Order management
- Sales analytics

✅ **Product Management**
- Add products with images
- Set pricing (regular & compare price)
- Manage stock levels
- Product categories and descriptions
- Approval process before going live

### Admin Features
✅ **Seller Management**
- Approve/reject seller applications
- View seller profiles
- Monitor seller activities
- Set commission rates
- Suspend sellers if needed

✅ **Product Management**
- Approve seller products
- Add store products directly
- Manage categories/subcategories
- Bulk product operations
- Product availability control

✅ **Order Management**
- View all orders
- Update order status
- Create Shiprocket shipments
- Track deliveries
- Handle cancellations/refunds

✅ **Coupon Management**
- Create discount coupons
- Set validity periods
- Usage limit controls
- Percentage or fixed discounts

✅ **Content Management**
- Manage blog posts
- Update site content
- Category management
- Review moderation

---

## 👥 User Roles & Access

### 1. Customer
**Access**: Limited to customer-facing features
- Browse and purchase products
- Manage cart and orders
- Submit reviews
- Update profile information

**Dashboard**: `/accounts/customer-dashboard/`

### 2. Seller
**Access**: Product and inventory management
- Add/edit own products
- View and manage seller orders
- Update business profile
- Cannot access other sellers' data

**Dashboard**: `/accounts/seller-dashboard/`

**Requirements**:
- Must be approved by admin
- Products require admin approval

### 3. Administrator
**Access**: Full system access
- Manage all users, sellers, and products
- Access Django admin panel
- Configure system settings
- View analytics and reports

**Admin Panel**: `/admin/`

---

## 🎛️ Admin Panel Guide

### Accessing Admin Panel
1. Navigate to: http://yourdomain.com/admin
2. Login with superuser credentials
3. Dashboard shows all models and statistics

### Common Admin Tasks

#### Approve a Seller
1. Navigate to **Accounts → Seller Profiles**
2. Select pending seller
3. Change **Approval Status** to "Approved"
4. Save changes
5. Seller can now add products

#### Approve Products
1. Navigate to **Store → Products**
2. Filter by: `approved = No`
3. Select products to approve
4. Use bulk action: "Approve selected products"
5. Execute action

#### Create Coupon Code
1. Navigate to **Coupons → Coupons**
2. Click "Add Coupon"
3. Fill in details:
   - Code: DISCOUNT20
   - Discount: 20 (percentage) or amount
   - Valid from/to dates
   - Active: Yes
4. Save

#### Create Shiprocket Shipment
1. Navigate to **Orders → Orders**
2. Select an order
3. Ensure order status is "Processing" or "Paid"
4. Click "Create Shipment" button
5. Shiprocket order ID and AWB will be generated
6. Update order status to "Shipped"

#### Manage Categories
1. Navigate to **Store → Categories**
2. Add/Edit/Delete categories
3. Upload category images
4. Set descriptions for SEO

---

## 💳 Payment Gateway Setup

### Razorpay Integration

#### Test Mode (Development)
```env
RAZORPAY_ENABLED=True
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxx
```

#### Production Mode
1. Complete KYC verification on Razorpay
2. Activate live mode
3. Generate live API keys
4. Update `.env` with live keys
5. Test with small transactions first

#### Payment Flow
1. Customer clicks "Place Order"
2. Razorpay checkout modal opens
3. Customer selects payment method:
   - Cards (Credit/Debit)
   - UPI (Google Pay, PhonePe, Paytm)
   - Net Banking
   - Wallets (Paytm, Mobikwik, etc.)
4. Payment processed
5. Verification callback to server
6. Order marked as "Paid"
7. Confirmation email sent

#### Webhook Setup (Production)
1. Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://yourdomain.com/orders/razorpay/verify/`
3. Select events: `payment.captured`, `payment.failed`
4. Add webhook secret to `.env`

#### Testing
**Test Cards**:
- Success: 4111 1111 1111 1111
- Failure: 4000 0000 0000 0002
- CVV: Any 3 digits
- Expiry: Any future date
- OTP: 1234

---

## 📦 Shipping Integration

### Shiprocket Setup

#### Initial Configuration
1. Create account at shiprocket.in
2. Add pickup address
3. KYC verification
4. Get API credentials
5. Configure in `.env`

#### Creating Shipments

**From Admin Panel**:
1. Order must be marked as "Paid"
2. Click "Create Shipment" button
3. Shiprocket order created automatically
4. AWB (tracking number) generated
5. Update order status to "Shipped"

**What Gets Sent to Shiprocket**:
- Order ID and date
- Customer name and address
- Product details and quantities
- Order amount
- Payment mode (prepaid/COD)

#### Tracking Orders
- AWB code stored in order
- Customer can track via carrier website
- Admin can view tracking in Shiprocket dashboard

#### Courier Selection
- Shiprocket automatically recommends courier
- Based on: destination, weight, dimensions
- Admin can override in Shiprocket dashboard

#### Returns & Exchanges
- Manage through Shiprocket dashboard
- Create reverse pickup requests
- Update order status accordingly

---

## 📧 Email Configuration

### Gmail SMTP Setup

#### Enable App Passwords
1. Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password for "Mail"
4. Copy 16-character password

#### Configuration
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Jannat Beauty <youremail@gmail.com>
```

### Email Templates
Located in: `templates/accounts/emails/`
- Order confirmation
- Order shipped notification
- Registration verification
- Password reset

### Testing Emails
```powershell
python manage.py shell
```
```python
from django.core.mail import send_mail
send_mail(
    'Test Email',
    'This is a test message.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

### Other Email Providers
**SendGrid**, **Mailgun**, **AWS SES** can also be used. Update `EMAIL_HOST` and credentials accordingly.

---

## 🗄️ Database Management

### Current Setup (SQLite)
- File: `db.sqlite3`
- Good for: Development, small-scale testing
- **Not recommended for production**

### Backup Database
```powershell
# Backup SQLite
python manage.py dumpdata > backup.json

# Backup to SQL file
python manage.py dbbackup
```

### Restore Database
```powershell
python manage.py loaddata backup.json
```

### Migration to PostgreSQL (Recommended for Production)

#### 1. Install PostgreSQL
```powershell
pip install psycopg2-binary
```

#### 2. Create Database
```sql
CREATE DATABASE jannat_beauty;
CREATE USER dbuser WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE jannat_beauty TO dbuser;
```

#### 3. Update settings.py
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'jannat_beauty',
        'USER': 'dbuser',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### 4. Migrate Data
```powershell
# Export from SQLite
python manage.py dumpdata > data.json

# Switch to PostgreSQL in settings

# Run migrations
python manage.py migrate

# Import data
python manage.py loaddata data.json
```

### Regular Maintenance
```powershell
# Clean up old sessions
python manage.py clearsessions

# Optimize database
python manage.py optimize_db

# Check for issues
python manage.py check
```

---

## 🚀 Deployment Guide

### Pre-Deployment Checklist
- [ ] Generate new SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Set up PostgreSQL database
- [ ] Configure production email backend
- [ ] Set Razorpay to live mode
- [ ] Configure Cloudinary for media
- [ ] Set up SSL certificate (HTTPS)
- [ ] Configure static file serving
- [ ] Set up Redis for caching
- [ ] Test payment flow
- [ ] Test email sending
- [ ] Backup database

### Production Settings (.env)
```env
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=new-production-secret-key

DATABASE_URL=postgresql://user:pass@host:5432/dbname

RAZORPAY_KEY_ID=rzp_live_xxxxx
RAZORPAY_KEY_SECRET=live_secret_key

CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Deployment Options

#### Option 1: Railway / Render / Heroku
1. Create account on platform
2. Connect GitHub repository
3. Add environment variables
4. Deploy with one click
5. Configure custom domain

#### Option 2: VPS (DigitalOcean, AWS, Linode)
**Requirements**:
- Ubuntu Server 20.04+
- Nginx web server
- Gunicorn WSGI server
- PostgreSQL database
- SSL certificate (Let's Encrypt)

**Steps**:
```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql

# Clone project
git clone your-repo-url
cd project

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Nginx
sudo nano /etc/nginx/sites-available/jannat-beauty

# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:8000 ecommerce.wsgi:application
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /home/user/project;
    }
    
    location /media/ {
        root /home/user/project;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Static Files Collection
```powershell
# Collect all static files
python manage.py collectstatic --noinput
```

### SSL Certificate (HTTPS)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔧 Maintenance & Support

### Regular Tasks

#### Daily
- Monitor error logs: `logs/` directory
- Check pending orders
- Verify payment reconciliation
- Review new seller applications

#### Weekly
- Backup database
- Review product approvals
- Check inventory levels
- Monitor site performance

#### Monthly
- Update dependencies: `pip list --outdated`
- Security updates
- Clear old sessions
- Generate sales reports
- Review and respond to reviews

### Logs & Monitoring
```powershell
# View Django logs
Get-Content logs\django.log -Tail 50

# View error logs
Get-Content logs\errors.log -Tail 50

# Monitor server
python manage.py runserver --verbosity 2
```

### Performance Optimization
```python
# Enable Redis caching (already configured)
# Check settings.py CACHES configuration

# Optimize images before upload
# Use Cloudinary auto-optimization

# Database query optimization
# Add indexes for frequently searched fields
```

### Security Updates
```powershell
# Update Django
pip install --upgrade django

# Update all packages
pip install --upgrade -r requirements.txt

# Check for vulnerabilities
pip install safety
safety check
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "CSRF Token Missing or Incorrect"
**Solution**:
```env
# Add to .env
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

#### 2. "Product Not Available for Purchase"
**Check**:
- Product `approved = True`
- Product `available = True`
- Product `stock > 0`
- Seller is approved

**Fix in Admin**:
1. Products → Select product
2. Check all checkboxes
3. Set stock > 0
4. Save

#### 3. "Razorpay Order Creation Failed"
**Solutions**:
- Verify API keys in `.env`
- Check `RAZORPAY_ENABLED=True`
- Ensure amount > 0
- Check internet connection

#### 4. "Shiprocket Integration Disabled"
**Solutions**:
```env
SHIPROCKET_ENABLED=True
SHIPROCKET_API_EMAIL=your_email
SHIPROCKET_API_PASSWORD=your_password
```

#### 5. "Static Files Not Loading"
**Solutions**:
```powershell
# Collect static files
python manage.py collectstatic

# Check settings.py
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

#### 6. "Email Not Sending"
**Check**:
- Gmail App Password (not regular password)
- EMAIL_USE_TLS=True
- Port 587 for Gmail
- 2FA enabled on Gmail account

#### 7. "Database Locked Error" (SQLite)
**Solutions**:
- Close other connections
- Restart development server
- Consider migrating to PostgreSQL

#### 8. "Out of Stock But Stock Shows Available"
**Solution**:
```powershell
# Refresh templates cache
python manage.py clear_cache

# Or restart server
```

### Debug Mode
For troubleshooting in development:
```env
DEBUG=True
```
**Never use DEBUG=True in production!**

### Getting Help
1. Check logs in `logs/` directory
2. Review `BUGS_AND_DEPLOYMENT.md`
3. Review `CODE_IMPROVEMENTS.md`
4. Check Django documentation
5. Contact developer support

---

## 📞 Support Information

### Documentation Files
- `README.md` - Project overview
- `BUGS_AND_DEPLOYMENT.md` - Known issues and fixes
- `CODE_IMPROVEMENTS.md` - Optimization suggestions
- `EMAIL_CONFIGURATION.md` - Email setup details
- `CLOUDINARY_SETUP.md` - Media storage setup
- `REDIS_INTEGRATION.md` - Caching configuration
- `REDIS_SETUP.md` - Redis installation guide

### Developer Contact
For technical support and custom development:
- Repository: jannat-beauty (altmash21)
- Issues: Check GitHub issues tab

### Important URLs (After Deployment)
- Website: https://yourdomain.com
- Admin Panel: https://yourdomain.com/admin
- Customer Dashboard: https://yourdomain.com/accounts/customer-dashboard/
- Seller Dashboard: https://yourdomain.com/accounts/seller-dashboard/

---

## 📝 Quick Start Summary

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Create `.env` file with credentials
3. **Setup DB**: `python manage.py migrate`
4. **Create Admin**: `python manage.py createsuperuser`
5. **Run**: `python manage.py runserver`
6. **Access**: http://127.0.0.1:8000

**First Steps After Login**:
1. Add categories (Admin Panel)
2. Approve sellers (if any)
3. Add products
4. Configure payment gateway
5. Test checkout flow

---

## 🎉 Conclusion

Your Jannat Beauty e-commerce platform is production-ready with all essential features:
- ✅ Complete shopping experience
- ✅ Multi-vendor support
- ✅ Payment gateway integration
- ✅ Shipping automation
- ✅ Inventory management
- ✅ Mobile responsive design

**Next Steps**: Configure production environment, add products, and launch!

For any questions or support, refer to the documentation files or contact the development team.

---

*Document Version: 1.0*  
*Last Updated: November 19, 2025*  
*Platform: Jannat Beauty E-Commerce*
