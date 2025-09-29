#!/bin/bash
# Complete environment setup for Automotive Price Monitor

set -e

echo "🌟 Setting up Automotive Price Monitor Environment..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️ This script should not be run as root. Run as regular user with sudo access."
   exit 1
fi

# Install dependencies first
echo "📦 Installing system dependencies..."
./scripts/install_dependencies.sh

# Setup Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3.9 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "✅ Python environment setup completed"

# Setup configuration
echo "⚙️ Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Created .env file from template"
    echo "⚠️ Please edit .env file with your actual configuration values"
fi

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p data/exports
mkdir -p data/cache
mkdir -p backups
chmod 755 logs data backups

# Initialize database
echo "🗄️ Initializing database..."
if [ -f database/init_db.sql ]; then
    mysql -u automotive -pautomotive_password automotive_prices < database/init_db.sql
    echo "✅ Database schema created"
fi

# Run Python migrations
python database/migrations.py

# Setup supervisor configuration
echo "👷 Setting up process supervisor..."
sudo tee /etc/supervisor/conf.d/automotive-price-monitor.conf > /dev/null <<EOF
[group:automotive-price-monitor]
programs=automotive-dashboard

[program:automotive-dashboard]
command=$(pwd)/venv/bin/python run.py
directory=$(pwd)
user=automotive
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/automotive-price-monitor/dashboard.log
environment=PATH="$(pwd)/venv/bin"
EOF

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Setup nginx configuration (optional)
echo "🌐 Setting up Nginx configuration..."
sudo tee /etc/nginx/sites-available/automotive-price-monitor > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias $(pwd)/dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/automotive-price-monitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Set up SSL certificate (Let's Encrypt)
echo "🔒 Setting up SSL certificate..."
sudo apt install -y certbot python3-certbot-nginx

echo "⚠️ To enable HTTPS, run: sudo certbot --nginx -d your-domain.com"

# Create maintenance scripts
echo "🔧 Creating maintenance scripts..."

# Daily maintenance script
tee scripts/daily_maintenance.py > /dev/null <<EOF
#!/usr/bin/env python3
"""Daily maintenance tasks"""
import sys
sys.path.insert(0, '.')

from utils.monitoring import system_monitor
from utils.email_notifier import email_notifier
from data_processor.cache_manager import CacheManager

def main():
    # Clean up cache
    cache = CacheManager()
    cache.cleanup_expired()
    
    # System health check
    health = system_monitor.check_health()
    
    # Send daily report
    if health['overall_status'] != 'healthy':
        email_notifier.send_system_status(health)

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/daily_maintenance.py

# Weekly maintenance script
tee scripts/weekly_maintenance.py > /dev/null <<EOF
#!/usr/bin/env python3
"""Weekly maintenance tasks"""
import sys
sys.path.insert(0, '.')

from scripts.backup_database import main as backup_main
from utils.proxy_manager import proxy_manager

def main():
    # Create database backup
    backup_main.callback(
        output_dir=None,
        compress=True,
        cleanup_old=True,
        retention_days=30,
        notify=True
    )
    
    # Refresh proxy list
    if proxy_manager.is_proxy_enabled():
        proxy_manager.refresh_failed_proxies()

if __name__ == '__main__':
    main()
EOF

chmod +x scripts/weekly_maintenance.py

# Add weekly cron job
(crontab -l 2>/dev/null || echo "") | grep -v "weekly_maintenance" | \
{ cat; echo "0 2 * * 0 cd $(pwd) && python3.9 scripts/weekly_maintenance.py"; } | crontab -

# Test installation
echo "🧪 Testing installation..."
python -c "
import scrapy
import pandas
import sqlalchemy
import flask
from database.models import Product
from config.database import db_manager
print('✅ All imports successful')
"

# Test database connection
python -c "
from config.database import db_manager
if db_manager.test_connection():
    print('✅ Database connection successful')
else:
    print('❌ Database connection failed')
"

echo ""
echo "🎉 Environment setup completed successfully!"
echo ""
echo "📋 Setup Summary:"
echo "- Python virtual environment: venv/"
echo "- Database: MySQL with automotive_prices database"
echo "- Web server: Nginx reverse proxy"
echo "- Process manager: Supervisor"
echo "- Caching: Redis server"
echo "- Automation: Cron jobs configured"
echo ""
echo "🚀 To start the system:"
echo "1. Edit .env file with your configuration"
echo "2. Start services: sudo supervisorctl start automotive-dashboard"
echo "3. Access dashboard: http://your-server-ip"
echo ""
echo "📚 Documentation available in docs/ directory"
echo "🔍 Check logs: tail -f /var/log/automotive-price-monitor/dashboard.log"
