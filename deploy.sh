#!/bin/bash

# Production Deployment Script for Jannat Beauty E-commerce Site

set -e  # Exit on any error

echo "🚀 Starting Jannat Beauty E-commerce Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found! Please create it from .env.example"
    exit 1
fi

print_status "1. Creating application user..."
sudo useradd --system --shell /bin/bash --home /home/jannatbeauty --create-home jannatbeauty || true

print_status "2. Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server

print_status "3. Setting up PostgreSQL database..."
sudo -u postgres createuser --interactive --pwprompt jannatbeauty_user || true
sudo -u postgres createdb --owner=jannatbeauty_user jannatbeauty_db || true

print_status "4. Creating application directory..."
sudo mkdir -p /var/www/jannatbeauty
sudo chown jannatbeauty:www-data /var/www/jannatbeauty
sudo chmod 755 /var/www/jannatbeauty

print_status "5. Copying application files..."
sudo cp -r . /var/www/jannatbeauty/
sudo chown -R jannatbeauty:www-data /var/www/jannatbeauty/

print_status "6. Setting up Python virtual environment..."
sudo -u jannatbeauty python3 -m venv /var/www/jannatbeauty/venv
sudo -u jannatbeauty /var/www/jannatbeauty/venv/bin/pip install --upgrade pip
sudo -u jannatbeauty /var/www/jannatbeauty/venv/bin/pip install -r /var/www/jannatbeauty/requirements.txt

print_status "7. Running Django setup..."
cd /var/www/jannatbeauty
sudo -u jannatbeauty /var/www/jannatbeauty/venv/bin/python manage.py collectstatic --noinput
sudo -u jannatbeauty /var/www/jannatbeauty/venv/bin/python manage.py migrate

print_status "8. Creating systemd service..."
sudo tee /etc/systemd/system/jannatbeauty.service > /dev/null << 'EOF'
[Unit]
Description=Jannat Beauty E-commerce Application
After=network.target

[Service]
Type=notify
User=jannatbeauty
Group=www-data
WorkingDirectory=/var/www/jannatbeauty
Environment=PATH=/var/www/jannatbeauty/venv/bin
EnvironmentFile=/var/www/jannatbeauty/.env
ExecStart=/var/www/jannatbeauty/venv/bin/gunicorn --workers 3 --bind unix:/var/www/jannatbeauty/jannatbeauty.sock ecommerce.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

print_status "9. Configuring Nginx..."
sudo tee /etc/nginx/sites-available/jannatbeauty > /dev/null << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 20M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/jannatbeauty;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        root /var/www/jannatbeauty;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/jannatbeauty/jannatbeauty.sock;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/jannatbeauty /etc/nginx/sites-enabled/
sudo nginx -t

print_status "10. Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable jannatbeauty
sudo systemctl start jannatbeauty
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo systemctl enable redis-server
sudo systemctl start redis-server

print_status "11. Setting up SSL with Let's Encrypt..."
sudo apt install -y certbot python3-certbot-nginx
print_warning "Run the following command to setup SSL:"
print_warning "sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com"

print_status "12. Setting up firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw --force enable

print_status "✅ Deployment completed successfully!"
print_status "📋 Next steps:"
echo "1. Update your .env file with production values"
echo "2. Update yourdomain.com in nginx config with your actual domain"
echo "3. Run SSL setup: sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "4. Create superuser: sudo -u jannatbeauty /var/www/jannatbeauty/venv/bin/python /var/www/jannatbeauty/manage.py createsuperuser"

print_status "📊 Service status:"
sudo systemctl status jannatbeauty --no-pager -l
sudo systemctl status nginx --no-pager -l