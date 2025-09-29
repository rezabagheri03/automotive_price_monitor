# Automotive Price Monitor

A comprehensive system for scraping prices of automotive parts and accessories from Iranian websites, calculating statistics, and automatically updating WooCommerce-based WordPress sites.

## 📋 Features

- **Multi-Site Scraping**: Monitor prices from 12 Iranian automotive websites
- **Statistical Analysis**: Calculate average, minimum, and maximum prices
- **WooCommerce Integration**: Automatic price updates via CSV import
- **Web Dashboard**: Manage products, view logs, and configure settings
- **Daily Automation**: Scheduled price updates with monitoring
- **Proxy Support**: Rotate IPs to prevent blocking
- **Error Handling**: Robust error recovery and logging

## 🏗️ Architecture

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ WEB SCRAPER │─▶│ DATA PROC. │─▶│ WOOCOMMERCE │─▶│ DASHBOARD │
│ (Scrapy) │ │ (Pandas) │ │ (CSV/API) │ │ (Flask) │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
│ │ │ │
▼ ▼ ▼ ▼
┌─────────────────────────────────────────────────────────────────┐
│ MySQL Database │
└─────────────────────────────────────────────────────────────────┘



## 🚀 Quick Start

### Prerequisites
- Ubuntu 22.04 LTS VPS (4GB+ RAM recommended)
- Python 3.9+
- MySQL 8.0+
- Redis (optional, for caching)

### Installation

1. **Clone the repository**
git clone <repository-url>
cd automotive_price_monitor



2. **Run setup script**
chmod +x scripts/setup_environment.sh
sudo ./scripts/setup_environment.sh



3. **Configure environment**
cp .env.example .env

Edit .env with your database credentials and API keys
nano .env



4. **Initialize database**
python database/migrations.py



5. **Start the dashboard**
python run.py



### Target Websites
- [اتونیک](https://auto-nik.com/) - ABS, ECU & Wiring
- [بی ام و استور](https://bmwstor.com/) - BMW Parts & Accessories  
- [بنز استور](https://benzstor.com/) - Mercedes Parts
- [مستریدکی](https://mryadaki.com/) - General Auto Parts
- [کارینو پارت](https://carinopart.com/) - Auto Components
- [ژاپن استور](https://japanstor.com/) - Japanese Car Parts
- [شجاع پارت](https://shojapart.com/) - Engine & Motor Parts
- [لوکس یدک](https://luxyadak.com/) - Luxury Car Parts
- [پارسیان لنت](https://parsianlent.com/) - Brake Components
- [ایران رنو](https://iranrenu.com/) - Renault Parts
- [اتوموبی](https://automoby.ir/) - Online Auto Marketplace
- [شهر روغن](https://oil-city.ir/) - Oils & Fluids

## 📊 Product Categories

The system handles 14 main automotive categories:
- اکتان و مکمل ها (Octane & Additives)
- رینگ و لاستیک (Wheels & Tires)
- سیستم خنک کننده (Cooling System)
- قطعات موتوری (Engine Parts)
- لوازم جانبی خودرو (Accessories)
- جلوبندی و تعلیق و سیستم فرمان (Suspension & Steering)
- سوخت رسانی و احتراق و اگزوز (Fuel & Exhaust)
- فیلتر و صافی (Filters)
- گیربکس و انتقال قدرت (Transmission)
- لوازم مصرفی (Consumables)
- روغن و مایعات (Oils & Fluids)
- قطعات بدنه و داخل کابین (Body & Interior)
- لوازم الکترونیک و سنسورها (Electronics & Sensors)
- سیستم ترمز (Brake System)

## 🛠️ Usage

### Running the Scraper
Run all spiders
python scripts/run_scraper.py

Run specific spider
python scripts/run_scraper.py --spider autonik

Test mode (limited products)
python scripts/run_scraper.py --test



### Updating WooCommerce
Generate CSV and update WooCommerce
python scripts/update_prices.py --price-type avg

Available price types: avg, min, max
python scripts/update_prices.py --price-type min



### Dashboard Access
- URL: `http://your-server:5000`
- Default credentials: admin/admin (change after first login)

## 📁 Project Structure

automotive_price_monitor/
├── config/ # Configuration files
├── scrapers/ # Scrapy spiders for each website
├── data_processor/ # Price calculation and validation
├── woocommerce_integration/ # WooCommerce API integration
├── dashboard/ # Flask web dashboard
├── database/ # Database models and migrations
├── utils/ # Utility functions (logging, proxy, etc.)
├── scripts/ # Automation and maintenance scripts
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── data/ # Data files (CSV, JSON configs)
├── deployment/ # Production deployment configs
└── logs/ # Application logs



## 🔒 Security Features

- Environment variable configuration
- Database connection encryption
- Input validation and sanitization
- Rate limiting and proxy rotation
- Authentication for dashboard access
- HTTPS enforcement in production

## 📈 Monitoring & Logging

- Comprehensive error logging
- Email notifications for failures
- System health monitoring
- Performance metrics tracking
- Database backup automation

## 🧪 Testing

Run all tests
python -m pytest tests/

Run specific test category
python -m pytest tests/test_scrapers.py
python -m pytest tests/test_data_processor.py


## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support and questions, please open an issue in the GitHub repository.