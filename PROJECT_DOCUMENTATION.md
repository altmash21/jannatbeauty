# Jannat Library - E-commerce Platform Documentation

## Project Overview

Jannat Library is a full-featured e-commerce platform built with Django, designed for selling authentic Islamic products including Qurans, prayer essentials, accessories, and Islamic decor. The platform provides a seamless shopping experience with modern features including real-time cart updates, coupon management, order tracking, and payment integration.

**Live URL:** https://jannatlibrary.com  
**Technology Stack:** Django 5.2.8, Python 3.10.11, SQLite/PostgreSQL, Bootstrap 5  


---

## Table of Contents

1. [Features](#features)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Project Structure](#project-structure)
5. [Key Modules](#key-modules)
6. [Admin Panel Guide](#admin-panel-guide)
7. [User Workflows](#user-workflows)
8. [API Documentation](#api-documentation)
9. [Payment Integration](#payment-integration)
10. [Email System](#email-system)
11. [Security Features](#security-features)
12. [Performance Optimization](#performance-optimization)
13. [Deployment](#deployment)
14. [Maintenance & Support](#maintenance--support)
15. [Troubleshooting](#troubleshooting)

---

## Features

### Customer Features
- **Product Browsing & Search**
  - Category-based navigation
  - Advanced search with typewriter effect
  - Product filtering and sorting
  - Responsive image gallery with zoom

- **Shopping Cart**
  - Real-time cart updates via AJAX
  - Quantity management
  - MRP and discount calculations
  - Persistent cart (session-based)
  - Coupon code application

- **Checkout & Orders**
  - Guest and registered user checkout
  - Multiple address management
  - Pincode-based delivery verification
  - COD and online payment options
  - Order tracking with real-time status updates
  - Order history and invoice download

- **User Account**
  - Email/OTP-based registration
  - Secure authentication
  - Profile management
  - Address book
  - Order history
  - Wishlist functionality

- **Promotional Features**
  - Dynamic offer banner system
  - Coupon code management
  - Discount popup for lead generation
  - Time-based promotions

### Admin Features
- **Product Management**
  - CRUD operations for products
  - Image upload and management
  - Inventory tracking
  - Category management
  - Bulk product operations

- **Order Management**
  - Order processing workflow
  - Status updates with email notifications
  - Shiprocket integration for shipping
  - Invoice generation
  - Payment reconciliation

- **Marketing Tools**
  - Offer banner management
  - Coupon creation and tracking
  - Lead management
  - Email campaign support

- **User Management**
  - Customer accounts
  - Seller accounts (multi-vendor support)
  - Role-based permissions
  - Activity logging

### Technical Features
- **Responsive Design**
  - Mobile-first approach
  - Touch-optimized interface
  - Progressive Web App (PWA) ready
  - Cross-browser compatibility

- **Performance**
  - Image optimization
  - Lazy loading
  - Database query optimization
  - Static file caching

- **Security**
  - CSRF protection
  - XSS prevention
  - SQL injection protection
  - Secure password hashing
  - HTTPS enforcement

---

## System Architecture

### Technology Stack

**Backend:**
- Django 5.2.8 (Python web framework)
- Python 3.10.11
- SQLite (development) / PostgreSQL (production)

**Frontend:**
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap 5.3
- Swiper.js for carousels
- AJAX for dynamic updates

**Payment Gateway:**
- Cashfree Payment Gateway
- Razorpay (alternative)

**Shipping:**
- Shiprocket API integration

**Email:**
- Django email backend
- SMTP configuration (Gmail/Custom)

**File Storage:**
- Cloudinary (media files)
- Static files (WhiteNoise)

### Application Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│  (Bootstrap 5 + Custom CSS + JavaScript)                │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   Django Application                     │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Store   │  │   Cart   │  │  Orders  │  │Accounts │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ Coupons  │  │  Reviews │  │   Blog   │  │  Utils  │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                   External Services                      │
├─────────────────────────────────────────────────────────┤
│  Cashfree  │  Shiprocket  │  Cloudinary  │  SMTP       │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│                      Database Layer                      │
│              SQLite / PostgreSQL                         │
└─────────────────────────────────────────────────────────┘
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Virtual environment (venv)
- Git

### Local Development Setup


1. **Clone the Repository**
```bash
# (Repository URL provided upon request)
cd jannatbeauty
```

2. **Create Virtual Environment**
```bash
python -m venv .venv
```

3. **Activate Virtual Environment**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

5. **Environment Configuration**

Create a `.env` file in the project root:
```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost/dbname

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Payment Gateway
CASHFREE_CLIENT_ID=your-cashfree-client-id
CASHFREE_CLIENT_SECRET=your-cashfree-client-secret
CASHFREE_ENV=sandbox  # or production

# Shiprocket
SHIPROCKET_EMAIL=your-shiprocket-email
SHIPROCKET_PASSWORD=your-shiprocket-password

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

6. **Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **Create Superuser**
```bash
python manage.py createsuperuser
```

8. **Collect Static Files**
```bash
python manage.py collectstatic
```

9. **Run Development Server**
```bash
python manage.py runserver
```

Access the application at: `http://127.0.0.1:8000`  
Admin panel at: `http://127.0.0.1:8000/admin`

---

## Project Structure

```
jannatbeauty/
├── accounts/                 # User authentication & profiles
│   ├── migrations/
│   ├── templates/
│   ├── admin.py
│   ├── models.py            # User, Profile, Address models
│   ├── views.py             # Login, registration, dashboard
│   ├── forms.py             # User forms
│   └── urls.py
│
├── blog/                    # Blog functionality
│   ├── migrations/
│   ├── templates/
│   ├── models.py           # BlogPost, Category
│   └── views.py
│
├── cart/                   # Shopping cart
│   ├── migrations/
│   ├── templates/
│   ├── cart.py            # Cart class (session-based)
│   ├── views.py           # Add, remove, update cart
│   └── context_processors.py
│
├── coupons/               # Coupon management
│   ├── migrations/
│   ├── templates/
│   ├── models.py         # Coupon, CouponUsage
│   ├── views.py          # Apply, remove coupons
│   └── admin.py
│
├── ecommerce/            # Project settings
│   ├── settings.py       # Configuration
│   ├── urls.py          # URL routing
│   └── wsgi.py
│
├── orders/              # Order processing
│   ├── migrations/
│   ├── templates/
│   ├── models.py       # Order, OrderItem
│   ├── views_checkout.py
│   ├── cashfree_service.py
│   ├── shiprocket_api.py
│   └── utils.py
│
├── reviews/            # Product reviews
│   ├── migrations/
│   ├── models.py      # Review, Rating
│   └── views.py
│
├── store/             # Core store functionality
│   ├── migrations/
│   ├── templates/
│   │   ├── store/
│   │   │   ├── home.html
│   │   │   ├── about.html
│   │   │   └── product/
│   │   │       ├── list.html
│   │   │       └── detail.html
│   ├── models.py     # Product, Category, OfferBanner
│   ├── views.py      # Product listing, detail
│   ├── admin.py
│   ├── context_processors_offerbanner.py
│   └── urls.py
│
├── templates/         # Global templates
│   ├── base.html     # Base template with navbar
│   ├── base_customer.html
│   ├── emails/       # Email templates
│   └── includes/
│
├── static/           # Static files
│   ├── css/
│   ├── js/
│   ├── images/
│   └── videos/
│
├── media/           # User uploads
│   ├── products/
│   └── categories/
│
├── logs/           # Application logs
│
├── utils/         # Utility functions
│
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

---

## Key Modules

### 1. Store Module

**Purpose:** Core e-commerce functionality for product management and display.

**Key Models:**
- `Category`: Product categorization with hierarchical structure
- `Product`: Product information, pricing, inventory
- `OfferBanner`: Dynamic promotional banners

**Key Features:**
- Product CRUD operations
- Category management
- Image handling with Cloudinary
- SEO-friendly URLs
- Stock management

### 2. Cart Module

**Purpose:** Session-based shopping cart functionality.

**Key Components:**
- `Cart` class: Session-based cart management
- AJAX-based updates
- Quantity management
- Price calculations

**Cart Operations:**
```python
cart = Cart(request)
cart.add(product, quantity=1)
cart.remove(product_id)
cart.update(product_id, quantity)
cart.clear()
```

### 3. Orders Module

**Purpose:** Order processing, payment, and fulfillment.

**Key Models:**
- `Order`: Order details and status
- `OrderItem`: Individual products in order

**Order Workflow:**
1. Cart → Checkout
2. Address selection
3. Payment processing (Cashfree/COD)
4. Order confirmation
5. Shiprocket shipment creation
6. Status updates & tracking

### 4. Accounts Module

**Purpose:** User authentication and profile management.

**Key Models:**
- `User`: Django's built-in user model
- `Profile`: Extended user information
- `Address`: User addresses for delivery

**Authentication Features:**
- Email/OTP registration
- Password reset via OTP
- Profile management
- Address book

### 5. Coupons Module

**Purpose:** Discount and promotional code management.

**Key Models:**
- `Coupon`: Coupon details and validation rules
- `CouponUsage`: Track coupon usage

**Coupon Types:**
- Percentage discount
- Fixed amount discount
- Minimum purchase requirements
- Usage limits
- Date-based validity

**Banner Integration:**
- Coupons can be displayed in the top offer banner
- Automatic coupon code copying
- Real-time validation

---

## Admin Panel Guide

### Accessing Admin Panel

URL: `https://jannatlibrary.com/admin`

**Login with superuser credentials**

### Dashboard Overview

The admin panel provides comprehensive management tools:

1. **Products Management**
   - Add/Edit/Delete products
   - Upload product images
   - Set pricing and discounts
   - Manage inventory
   - Bulk actions

2. **Category Management**
   - Create product categories
   - Upload category images
   - Set category order

3. **Order Management**
   - View all orders
   - Update order status
   - Process refunds
   - Generate invoices
   - Track shipments

4. **Offer Banner Management**
   - Create promotional banners
   - Set expiry dates
   - Toggle active status

5. **Coupon Management**
   - Create discount coupons
   - Set discount type and value
   - Configure usage limits
   - Set validity period
   - Enable banner display

6. **User Management**
   - View customer accounts
   - Manage seller accounts
   - View order history

### Creating a New Product

1. Navigate to **Store → Products → Add Product**
2. Fill in required fields:
   - Name
   - Description
   - Price
   - Compare price (MRP)
   - Category
   - Stock quantity
3. Upload product images
4. Set product as active
5. Save

### Creating Promotional Coupons

1. Navigate to **Coupons → Add Coupon**
2. Enter coupon code (e.g., WELCOME5830UC)
3. Select discount type (percentage/fixed)
4. Enter discount value
5. Set minimum purchase amount (optional)
6. Set usage limits (optional)
7. Set valid from/to dates
8. Check "Show on banner" to display in top banner
9. Save

### Managing Orders

1. **View Orders**: Coupons → Orders
2. **Update Status**: Select order → Change status
3. **Send Updates**: Status change automatically sends email
4. **Available Statuses**:
   - Pending
   - Confirmed
   - Processing
   - Shipped
   - Delivered
   - Cancelled
   - Refunded

---

## User Workflows

### Customer Purchase Journey

```
Browse Products
    ↓
View Product Details
    ↓
Add to Cart
    ↓
View Cart → Apply Coupon (optional)
    ↓
Proceed to Checkout
    ↓
Login/Register (or continue as guest)
    ↓
Select/Add Delivery Address
    ↓
Verify Pincode
    ↓
Choose Payment Method
    ↓
Complete Payment
    ↓
Order Confirmation
    ↓
Track Order
    ↓
Receive Product
```

### Registration & Login

**Registration:**
1. Click "Sign In" → "Register"
2. Enter email and password
3. Receive OTP via email
4. Verify OTP
5. Complete profile

**Login:**
1. Enter email and password
2. Click "Login"
3. Redirect to dashboard/previous page

### Applying Coupons

**Method 1: From Banner**
1. Click on coupon code in top banner
2. Code is copied to clipboard
3. Go to cart
4. Paste and apply

**Method 2: Manual Entry**
1. Go to cart page
2. Enter coupon code in "Coupon Code" section
3. Click "Apply Coupon"
4. Discount is applied immediately

### Order Tracking

1. Login to account
2. Navigate to "My Orders"
3. Click on order to view details
4. View tracking information
5. Contact support if needed

---

## API Documentation

### Cart API Endpoints

**GET /cart/count/**
- Returns current cart item count
- Used for navbar badge updates
```json
Response: {"count": 3}
```

**POST /cart/add/<product_id>/**
- Adds product to cart
- Parameters: `quantity`, `buy_now`
```json
Response: {
  "success": true,
  "cart_total_quantity": 3,
  "message": "Product added to cart"
}
```

**POST /cart/remove/<product_id>/**
- Removes product from cart
```json
Response: {"success": true}
```

**POST /cart/update/<product_id>/**
- Updates product quantity
- Parameters: `quantity`
```json
Response: {
  "success": true,
  "item_total_price": 299.99,
  "total": 899.97
}
```

### Coupon API Endpoints

**POST /coupons/apply/**
- Applies coupon code
- Parameters: `coupon_code`
- Returns success message with discount amount

**POST /coupons/remove/**
- Removes applied coupon
- Returns success message

### Order API Endpoints

**POST /orders/verify-pincode/**
- Verifies delivery availability
- Parameters: `pincode`
```json
Response: {
  "available": true,
  "delivery_days": 5
}
```

---

## Payment Integration

### Cashfree Integration

**Configuration:**
```python
CASHFREE_CLIENT_ID = 'your-client-id'
CASHFREE_CLIENT_SECRET = 'your-client-secret'
CASHFREE_ENV = 'production'  # or 'sandbox'
```

**Payment Flow:**
1. Customer initiates checkout
2. Order created with status "Pending"
3. Cashfree session created
4. Customer redirected to payment page
5. Payment processed
6. Webhook received for confirmation
7. Order status updated to "Confirmed"

**Webhook Endpoint:** `/orders/cashfree-webhook/`

### Cash on Delivery (COD)

- Available for verified pincodes
- Order confirmed immediately
- Payment collected on delivery

---

## Email System

### Email Templates

Located in `templates/emails/`:
- `order_confirmation.html` - Order confirmation
- `order_status_update.html` - Status updates
- `otp_verification.html` - Registration OTP
- `password_reset_otp.html` - Password reset
- `welcome.html` - Welcome email

### Email Configuration

**SMTP Settings:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'app-password'
DEFAULT_FROM_EMAIL = 'Jannat Library <noreply@jannatlibrary.com>'
```

### Automated Emails

- Registration verification
- Order confirmation
- Order status updates
- Payment confirmation
- Shipping updates
- Promotional campaigns

---

## Security Features

### Implemented Security Measures

1. **CSRF Protection**
   - All POST requests protected with CSRF tokens
   - Enforced across all forms

2. **XSS Prevention**
   - Django's template auto-escaping
   - Input sanitization

3. **SQL Injection Protection**
   - Django ORM parameterized queries
   - No raw SQL without proper escaping

4. **Password Security**
   - Argon2 hashing algorithm
   - Strong password requirements
   - Password reset via OTP

5. **HTTPS Enforcement**
   - SSL/TLS encryption
   - HSTS headers
   - Secure cookies

6. **Session Security**
   - Session timeout
   - HttpOnly cookies
   - Secure flag on cookies

7. **File Upload Security**
   - File type validation
   - Size restrictions
   - Cloudinary CDN

### Security Best Practices

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## Performance Optimization

### Database Optimization

1. **Query Optimization**
   - `select_related()` for foreign keys
   - `prefetch_related()` for many-to-many
   - Database indexing on frequently queried fields

2. **Caching Strategy**
   - Static files cached with WhiteNoise
   - Cloudinary CDN for media files
   - Browser caching headers

### Frontend Optimization

1. **Image Optimization**
   - Cloudinary auto-format
   - Responsive images
   - Lazy loading

2. **Asset Optimization**
   - Minified CSS/JS
   - CDN delivery for libraries
   - Gzip compression

3. **Code Splitting**
   - Async JavaScript loading
   - Deferred non-critical scripts

### Performance Metrics

- **Page Load Time:** < 3 seconds
- **Time to Interactive:** < 5 seconds
- **First Contentful Paint:** < 2 seconds

---

## Deployment

### Production Deployment Checklist

#### Pre-Deployment

- [ ] Set `DEBUG = False` in settings
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Configure environment variables
- [ ] Set up Cloudinary for media
- [ ] Configure email settings
- [ ] Set up payment gateway (production mode)
- [ ] Configure Shiprocket API
- [ ] Run security checks

#### Deployment Steps

1. **Database Setup**
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

2. **Environment Configuration**
```bash
export SECRET_KEY='production-secret-key'
export DEBUG=False
export DATABASE_URL='postgresql://...'
```

3. **Server Configuration**
   - Gunicorn as WSGI server
   - Nginx as reverse proxy
   - Supervisor for process management

4. **SSL Certificate**
   - Let's Encrypt SSL
   - Auto-renewal setup

#### Post-Deployment

- [ ] Verify all pages load correctly
- [ ] Test checkout process
- [ ] Verify email sending
- [ ] Test payment integration
- [ ] Check admin panel access
- [ ] Monitor error logs
- [ ] Set up monitoring (e.g., Sentry)

### Deployment Scripts

**build.sh:**
```bash
#!/bin/bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

**deploy.sh:**
```bash
#!/bin/bash
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

---

## Maintenance & Support

### Regular Maintenance Tasks

**Daily:**
- Monitor error logs
- Check order processing
- Review payment transactions

**Weekly:**
- Database backup
- Review customer feedback
- Update inventory

**Monthly:**
- Security updates
- Performance review
- Analytics review
- Content updates

### Backup Strategy

**Database Backup:**
```bash
# PostgreSQL backup
pg_dump dbname > backup_$(date +%Y%m%d).sql

# Automated daily backups
0 2 * * * pg_dump dbname > /backups/db_$(date +\%Y\%m\%d).sql
```

**Media Files Backup:**
- Cloudinary provides automatic backup
- Additional backup to S3/external storage

### Monitoring

**Application Monitoring:**
- Error tracking with Sentry
- Uptime monitoring
- Performance metrics

**Server Monitoring:**
- CPU/Memory usage
- Disk space
- Network traffic

### Log Files

Located in `logs/` directory:
- `django.log` - Application logs
- `error.log` - Error logs
- `access.log` - Access logs

---

## Troubleshooting

### Common Issues & Solutions

#### Issue: Coupon not applying
**Solution:**
1. Verify coupon is active in admin
2. Check validity dates
3. Ensure cart total meets minimum
4. Clear browser cache and try again

#### Issue: Payment not processing
**Solution:**
1. Check Cashfree credentials
2. Verify webhook URL is accessible
3. Check payment gateway logs
4. Ensure SSL is properly configured

#### Issue: Emails not sending
**Solution:**
1. Verify SMTP settings in .env
2. Check email credentials
3. Enable "Less secure apps" for Gmail
4. Use app-specific passwords
5. Check spam folder

#### Issue: Images not loading
**Solution:**
1. Verify Cloudinary configuration
2. Check image URLs
3. Ensure CORS settings are correct
4. Clear CDN cache

#### Issue: Cart items disappearing
**Solution:**
1. Check session configuration
2. Verify cookies are enabled
3. Check session timeout settings

### Debug Mode

**Enable Debug Mode (Development Only):**
```python
# settings.py
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

**View Detailed Errors:**
Set `DEBUG = True` temporarily to see detailed error pages.

### Getting Support

**Contact Information:**
- Email: support@jannatlibrary.com
- Phone: +91 8400043322
- GitHub Issues: https://github.com/altmash21/jannatbeauty/issues

---

## Changelog

### Version 1.0.0 (Current)

**New Features:**
- Dynamic offer banner system with coupon integration
- Mobile-responsive design with bottom navigation
- Real-time cart updates via AJAX
- Coupon code management with discount tracking
- Cashfree payment integration
- Shiprocket shipping integration
- Order tracking system
- Email notification system
- Product review and rating system
- Blog functionality
- Multi-address management
- Pincode verification
- Guest checkout support

**Improvements:**
- Optimized database queries
- Enhanced mobile UX
- Improved checkout flow
- Better error handling
- Security enhancements

**Bug Fixes:**
- Fixed banner positioning on mobile
- Resolved coupon application issues
- Fixed cart total calculation
- Corrected email template rendering

---

## Future Enhancements

### Planned Features

**Phase 2:**
- [ ] Wishlist functionality
- [ ] Product comparison
- [ ] Advanced filters (price, brand, rating)
- [ ] Social media integration
- [ ] Live chat support
- [ ] Product recommendations
- [ ] Customer reviews with images

**Phase 3:**
- [ ] Multi-vendor marketplace
- [ ] Loyalty program
- [ ] Subscription service
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Inventory forecasting
- [ ] Multi-currency support
- [ ] Multi-language support

---

## Credits & Acknowledgments

**Developed By:** Altmash Shaikh (Full Stack Developer)  
**Framework:** Django (Python Web Framework)  
**Frontend:** Bootstrap 5, Swiper.js  
**Payment:** Cashfree Payment Gateway  
**Shipping:** Shiprocket  
**Media Storage:** Cloudinary  

**Third-Party Libraries:**
- Django
- Bootstrap
- Swiper.js
- Cloudinary
- Gunicorn
- WhiteNoise
- Pillow

---

## License

This project is proprietary software developed for Jannat Library. All rights reserved.

**Copyright © 2025 Jannat Library**

---

## Appendix

### Useful Commands

```bash
# Start development server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run tests
python manage.py test

# Shell access
python manage.py shell

# Database shell
python manage.py dbshell

# Clear sessions
python manage.py clearsessions
```

### Environment Variables Reference

```env
# Required
SECRET_KEY=
DEBUG=
ALLOWED_HOSTS=
DATABASE_URL=

# Email
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# Payment
CASHFREE_CLIENT_ID=
CASHFREE_CLIENT_SECRET=
CASHFREE_ENV=

# Shipping
SHIPROCKET_EMAIL=
SHIPROCKET_PASSWORD=

# Media
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

### Quick Reference Links

- **Admin Panel:** https://jannatlibrary.com/admin
- **Django Documentation:** https://docs.djangoproject.com/
- **Bootstrap Documentation:** https://getbootstrap.com/docs/
- **Cashfree Docs:** https://docs.cashfree.com/

---

**Document Version:** 1.0  
**Last Updated:** December 1, 2025  
**Prepared By:** Altmash Shaikh  
**Contact:** support@jannatlibrary.com

---

*This documentation is confidential and intended for authorized personnel only.*
