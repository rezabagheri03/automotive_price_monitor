#!/bin/bash
# Install dependencies for Automotive Price Monitor

set -e

echo "🚀 Installing Automotive Price Monitor Dependencies..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and development tools
echo "🐍 Installing Python and development tools..."
sudo apt install -y python3.9 python3.9-dev python3.9-venv python3-pip
sudo apt install -y build-essential libssl-dev libffi-dev
sudo apt install -y libxml2-dev libxslt1-dev zlib1g-dev
sudo apt install -y libjpeg-dev libpng-dev

# Install MySQL
echo "🗄️ Installing MySQL..."
sudo apt install -y mysql-server mysql-client libmysqlclient-dev
sudo systemctl start mysql
sudo systemctl enable mysql

# Install Redis (optional but recommended)
echo "📮 Installing Redis..."
sudo apt install -y redis-server
sudo systemctl start redis
sudo systemctl enable redis

# Install Nginx (for production)
echo "🌐 Installing Nginx..."
sudo apt install -y nginx
sudo systemctl enable nginx

# Install other utilities
echo "🛠️ Installing utilities..."
sudo apt install -y curl wget git htop supervisor cron

# Create project user (optional)
echo "👤 Setting up project user..."
sudo useradd -m -s /bin/bash automotive || echo "User already exists"

# Create project directories
echo "📁 Creating project directories..."
sudo mkdir -p /var/log/automotive-price-monitor
sudo mkdir -p /var/backups/automotive_prices
sudo mkdir -p /etc/automotive-price-monitor

# Set permissions
sudo chown -R automotive:automotive /var/log/automotive-price-monitor
sudo chown -R automotive:automotive /var/backups/automotive_prices

# Install Python dependencies
echo "📦 Installing Python dependencies..."
python3.9 -m pip install --upgrade pip setuptools wheel

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    python3.9 -m pip install -r requirements.txt
    echo "✅ Python dependencies installed from requirements.txt"
else
    echo "⚠️ requirements.txt not found, installing core dependencies..."
    python3.9 -m pip install scrapy pandas sqlalchemy pymysql flask requests python-dotenv
fi

# Setup MySQL database
echo "🗄️ Setting up MySQL database..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS automotive_prices CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'automotive'@'localhost' IDENTIFIED BY 'automotive_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON automotive_prices.* TO 'automotive'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "✅ MySQL database setup completed"

# Configure log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/automotive-price-monitor > /dev/null <<EOF
/var/log/automotive-price-monitor/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    copytruncate
}
EOF

# Setup cron job for daily execution
echo "⏰ Setting up cron job..."
(crontab -l 2>/dev/null || echo "") | grep -v "automotive-price-monitor" | \
{ cat; echo "0 3 * * * cd $(pwd) && python3.9 scripts/run_scraper.py && python3.9 scripts/update_prices.py"; } | crontab -

echo "✅ Cron job configured for 3 AM daily execution"

# Create systemd service files
echo "🔧 Creating systemd services..."

# Dashboard service
sudo tee /etc/systemd/system/automotive-dashboard.service > /dev/null <<EOF
[Unit]
Description=Automotive Price Monitor Dashboard
After=network.target mysql.service

[Service]
Type=simple
User=automotive
WorkingDirectory=$(pwd)
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3.9 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable automotive-dashboard.service

echo "🎯 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure your settings"
echo "2. Run database migrations: python3.9 database/migrations.py"
echo "3. Start the dashboard: sudo systemctl start automotive-dashboard"
echo "4. Access dashboard at: http://your-server:5000"
echo ""
echo "📚 Check the docs/ directory for detailed configuration guides"
