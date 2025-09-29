# API Reference - سیستم نظارت قیمت قطعات خودرو

## مقدمه

این سند API های REST سیستم نظارت قیمت قطعات خودرو را شرح می‌دهد.

**Base URL:** `https://your-domain.com/api`

**Authentication:** Bearer Token یا Session Cookie

## Authentication Endpoints

### Login
POST /auth/login
Content-Type:

{
"username": "string
, "password": "str
text

**Response:**
{
"success": tru
, "user
: {
id": 1, "usernam
": "admin",
"
text

### Logout
POST /auth/logout

text

## Products API

### Get Products List
GET /api/products?page=1&per_page=25&category=روغن

text

**Parameters:**
- `page` (int): شماره صفحه
- `per_page` (int): تعداد آیتم در صفحه
- `category` (string): فیلتر دسته‌بندی
- `search` (string): جستجو در نام
- `is_active` (boolean): فیلتر وضعیت فعالیت

**Response:**
{
"products":
[
{
"id": 1, "name": "
وغن موتور 5W-30",
"sku": "OIL-001",
"category": "روغن و مایعات
, "current_avg_price"
45000, "current_min_
rice": 42000,
"current_max_price":
48000, "is_active": true,

is
monitored": tru
, "u
dated_at": "
024-01-15T10:30
00Z" }
]
text

### Get Single Product
GET /api/products/{product_id}

text

### Create Product
POST /api/products
Content-Typ

{
"name": "نام محصول جدید
, "sku": "PRD-0
1", "category": "لوازم جانبی خ
درو", "description": "توضیحات
https://example.com/image.jpg",
"is_active": tru
, "is_monitored": t
ue, "woocommerce_id
text

### Update Product
PUT /api/products/{product_id}
Content-Type: application/jso

text

### Delete Product
DELETE /api/products/{product_id}

text

### Get Product Price History
GET /api/products/{product_id}/prices?days=30

text

**Response:**
{
"price_history":
[
{
"id": 1, "site_nam
": "autonik.com",
"site_price": 45
00, "avg_pric
": 44500, "mi
_price": 42000, "max_price": 4
0
0,
"scra
ed_at": "2024-01-15T08:00:00Z"
} ], "trends": {
"trend_direction"

text

## Scraping API

### Get Scraping Status
GET /api/scraping/status

text

**Response:**
{
"current_jobs":
[
{ "site_name"
"autonik", "s
atus": "running", "start_time":
"2024-01-15T10:00:00Z",
"products_found": 1
5
,
"products_processed": 400 } ],
"last_completed": "20
text

### Start Manual Scraping
POST /api/scraping/start
Conte

{
"sites": ["autonik", "bmwstor"
, "test_mode": fa
se, "notify_completion"
text

### Get Scraping Performance
GET /api/scraping/performance?days=7

text

### Get Site Status
GET /api/sites/status

text

**Response:**
{
"sites":
[
{ "name"
"autonik",
is_active": true,
"is_available": true, "last_successful_sc
ape": "2024-01-15T09:30:0
Z", "success_rate_
4
"
text

## Price Analysis API

### Calculate Daily Prices
POST /api/prices/calculate
Con

{
"date": "2024-01-15
, "price_type": "
text

### Get Category Statistics
GET /api/prices/category-stats

text

**Response:**
{
"categories":
{ "روغن و مایع
ت": { "product
count": 45, "
vg_price": 52000,
"min_price": 150
0, "max_price": 1
0
0
text

### Get Price Trends
GET /api/prices/trends?category=روغن&days=30

text

## WooCommerce Integration API

### Test WooCommerce Connection
POST /api/woocommerce/test
Con

{
"urlhttps://mystore.com",
"consumer_key": "ck_xxxxx
, "consumer_secret": "cs_xx
text

### Update WooCommerce Prices
POST /api/woocommerce/update-prices
Content-Type: applicatio

{
"price_type": "avg
, "dry_run": fa
se, "batch_siz
text

### Import CSV to WooCommerce
POST /api/woocommerce/import-csv
csv_file: [file]
update_existing: true
text

## Export API

### Export CSV Files
GET /api/export/csv/{type}

text

**Types:**
- `woocommerce`: فایل آماده برای WooCommerce
- `comparison`: مقایسه قیمت‌های سایت‌ها
- `inventory`: گزارش موجودی کلی

### Export PDF Report
POST /api/reports/export-pdf
C

{
"report_type": "full
, "date_range": "last_30_da
s", "include_charts"
text

## System Monitoring API

### Get System Health
GET /api/health

text

**Response:**
{
"overall_status": "healthy
, "timestamp": "2024-01-15T12:00:0
Z", "chec
s": { "da
abase": {
"status": "ok",
re
ponse_time
ms": 45 },
"redis": { "
ta
us": "ok",
"memory_usage":
"15%" }, "woocommerce": {


status": "ok
text

### Get System Statistics
GET /api/stats

text

**Response:**
{
"system":
{ "cpu_percent":
25.5, "memory_perce
t": 65.2, "disk_
er
ent": 45.8
, "database": { "
otal_products": 1250,
"active_products": 1100,

"price_entrie
_24h": 15400 },
scraping": { "total_
uns_7d": 14, "success_r
t
text

## User Management API

### Get Users List
GET /api/users

text

### Create User
POST /api/users
Content-Type:

{
"username": "newuser
, "email": "user@exm",
"password": "password123
, "role": "us
r", "is_active"
text

### Update User
PUT /api/users/{user_id}

text

### Toggle User Status
POST /api/users/{user_id}/toggle-status
{
"is_active": fal
text

## Error Responses

### 400 Bad Request
{
"error": "validation_failed
, "message": "داده‌های ورودی نامعت
ر", "detai
s": { "name": ["این فیلد الز
می است"], "price": ["قیمت باید ع
د
text

### 401 Unauthorized
{
"error": "unauthorized
, "message": "لطفاً وارد سیستم ش
text

### 403 Forbidden
{
"error": "insufficient_permissions
, "message": "شما دسترسی به این عملیات ندا
text

### 404 Not Found
{
"error": "not_found
, "message": "منبع مورد نظر یافت
text

### 500 Internal Server Error
{
"error": "internal_error
, "message": "خطای داخلی سر
ر", "request_id": "req_1234
text

## Rate Limiting

- **API Calls:** 1000 requests per hour per user
- **Scraping Operations:** 10 per hour per user
- **File Exports:** 50 per day per user

Headers:
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
text

## Webhooks (Optional)

### Register Webhook
POST /api/webhooks
Content-Typ

{
"urlhttps://your-app.com/webhook/price-update",
"events": ["price.updated", "scraping.completed"
, "secret": "your_webhook_sec
text

### Webhook Events

#### price.updated
{
"event": "price.updated
, "data
: { "product_i
": 123, "product_name": "روغن م
تور 5W-30", "ol
_price": 45000,
"new_price": 47000,
"change_percent": 4.4

"site_name": "autonik" }, "ti
text

#### scraping.completed
{
"event": "scraping.completed
, "data
: { "site_name": "a
tonik", "products_scr
ped": 1250, "duratio
_seconds": 180,
su
cess_rate": 98.4 }, "timestamp"
text

## SDK Usage Examples

### Python
import requests

Initialize client
class AutomotiveAPI:
def __init__(self, base_url, api_key):
self.base_url =
a

text
def get_products(self, **params):
    response = requests.get(
        f'{self.base_url}/api/products', 
        params=params,
        headers=self.headers
    )
    return response.json()
Usage
api = AutomotiveAPI('https://your-domain.com', 'your-api-key')
products = api.get_products(categ

text

### JavaScript
class AutomotiveAPI {
constructor(baseUrl, apiKe
) { this.baseUr
= baseUrl;
this.headers = { 'Authorization': `BeareBearer ${apiKey},
'Content-Type': 'appli
at
text
async getProducts(params = {}) {
    const url = new URL('/api/products', this.baseUrl);
    Object.keys(params).forEach(key => 
        url.searchParams.append(key, params[key])
    );
    
    const response = await fetch(url, {
        headers: this.headers
    });
    return response.json();
}
}

// Usage
const api = new Automohttps://your-domain.com', 'your-api-key');
const products = await api.getProducts({category

text

## Testing

### Using cURL
Get products
curl -X GET "https://your-domain.com/api/products"
-H "Authorization: Bearer YOUR_TOKEN"

Create product
curl -X POST "https://your-domain.com/api/products"
-H "Authorization: Bearer YOUR_TOKEN"
-H "Content-Type: application/json"
-d '{"name": "تست محصول", "category": "تست"}'

text

### Postman Collection
Import the provided Postman collection file for easier API testing.

## Support

برای پشتیبانی API:
- ایمیل: api-support@yourcompany.com
- تلگرام: @api_support
- مستندات بیشتر: https://docs.yourcompany.com/api
docs/troubleshooting.md
text
# راهنمای عیب‌یابی سیستم نظارت قیمت قطعات خودرو

## مشکلات رایج و راه‌حل‌ها

### 1. مشکلات نصب و راه‌اندازی

#### خطای وابستگی‌های Python
مشکل: ModuleNotFoundError
راه‌حل:
source venv/bin/activate
pip install -r r

در صورت مشکل با pip:
python -m pip install --upgrade pip
pip install -

text

#### خطای اتصال به MySQL
بررسی وضعیت MySQL
sudo systemctl status mysql

راه‌اندازی MySQL
sudo systemctl start mysql

بررسی اتصال
mysql -u automotive -p -h localhost automotive_prices

text

**خطاهای رایج MySQL:**
- `Access denied`: بررسی username/password در `.env`
- `Connection refused`: MySQL غیرفعال است
- `Unknown database`: پایگاه داده ایجاد نشده

#### مشکل مجوزهای فایل
تصحیح مالکیت فایل‌ها
sudo chown -R $USER:$USER /path/to/project

تنظیم مجوزهای صحیح
chmod 755 /path/to/project
chmod 644 /path/to/project/.env
chmod

text

### 2. مشکلات اسکرپینگ

#### Spider ها کار نمی‌کنند
تست spider به صورت دستی
cd scrapers/
scrapy crawl autonik -s CLOSESPIDER

بررسی لاگ‌های scrapy
tail -f logs/scrapy.log

text

**علل احتمالی:**
- سایت هدف در دسترس نیست
- تغییر ساختار HTML سایت
- مسدود شدن IP
- مشکل در proxy

#### مشکل با User-Agent
تنظیم User-Agent سفارشی
USER_AGENTS = [
'Mozilla/5.0 (compatible; AutomotiveBot/1.
)', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chro
text

#### خطای Timeout
افزایش timeout در settings
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_DELAY

text

### 3. مشکلات پایگاه داده

#### اتصال قطع می‌شود
در فایل database.py
engine = create_engine(
DATABASE_
RL, pool_pre_pi
g=True, pool_r
cycle=3600
text

#### خطای Migration
اجرای مجدد migrations
python database/migrations.py

در صورت مشکل، backup گیری و reset کردن
python scripts/backup_database.py
mysql -u automotive -p automo

text

#### کمبود فضای دیسک
بررسی فضای دیسک
df -h

پاک‌سازی لاگ‌های قدیمی
find logs/ -name "*.log" -mtime +30 -delete

فشرده‌سازی backup های قدیمی
gzip backups/*.sql

text

### 4. مشکلات WooCommerce

#### خطای Authentication
// بررسی کلیدهای API
{
"code": "woocommerce_rest_authentication_error
, "message": "Invalid signat
text

**راه‌حل:**
1. تولید مجدد Consumer Key/Secret
2. بررسی URL صحیح فروشگاه
3. فعال بودن SSL

#### خطای Permission
{
"code": "woocommerce_rest_cannot_create
, "message": "Sorry, you are not allowed to create resourc
text

**راه‌حل:**
- کلید API باید دسترسی Read/Write داشته باشد
- کاربر WooCommerce باید نقش Administrator داشته باشد

### 5. مشکلات عملکردی

#### سیستم کند است
بررسی CPU و RAM
htop

بررسی پردازش‌های در حال اجرا
ps aux | grep python

بررسی اتصالات پایگاه داده
mysql -e "SHOW PROCESSLIST;"

text

**بهینه‌سازی:**
- افزایش pool_size پایگاه داده
- فعال‌سازی Redis cache
- کاهش CONCURRENT_REQUESTS

#### خطای Memory
بررسی استفاده از حافظه
free -h

کشتن پردازش‌های غیرضروری
pkill -f "python.*scrapy"

راه‌اندازی مجدد supervisor
sudo supervisorctl restart automotive-price-monitor:*

text

### 6. مشکلات Dashboard

#### صفحه لود نمی‌شود
بررسی لاگ Flask
tail -f logs/dashboard.log

تست پورت
netstat -tlnp | grep :5000

راه‌اندازی مجدد
sudo supervisorctl restart automotive-dashboard

text

#### خطای 500
فعال‌سازی debug mode برای تشخیص
export FLASK_ENV=development
export DEBUG=True
text

#### مشکل Static Files
بررسی مجوزهای static files
ls -la dashboard/static/

کپی manual در nginx
sudo cp -r dashboard/static/* /var/www/html/static/

text

### 7. مشکلات Email

#### ایمیل ارسال نمی‌شود
تست تنظیمات SMTP
python -c "
from utils.email_notifier import email_notifier
result = email_notifier.test_email_configuration()
print(result)
text

**برای Gmail:**
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EM

text

### 8. مشکلات Proxy

#### Proxy کار نمی‌کند
تست manual proxy
import requests
proxhttp://proxy:port'}
response = requests.get(http://httpbin.org/ip', proxies=proxies)
pr

text

#### چرخش Proxy
در proxy_manager.py
def rotate_proxy(self):
if len(self.working_proxies)
1: sel

text

### 9. مشکلات Cron Jobs

#### Cron اجرا نمی‌شود
بررسی وضعیت cron
sudo systemctl status cron

مشاهده لاگ cron
grep automotive /var/log/syslog

تست دستی cron job
cd /path/to/project && python scripts/run_scraper.py

text

#### Path مشکل دارد
در crontab از absolute path استفاده کنید
0 3 * * * cd /full/path/to/project && /full/path/to/python scripts/run_scraper.py

text

### 10. مشکلات SSL/HTTPS

#### Certificate خطا
تجدید Let's Encrypt
sudo certbot renew

تست manual
sudo certbot certonly --manual -d yourdomain.com

text

### 11. ابزارهای عیب‌یابی

#### لاگ‌های سیستم
لاگ‌های اصلی
tail -f /var/log/automotive-price-monitor/*.log

لاگ‌های nginx
tail -f /var/log/nginx/error.log

لاگ‌های mysql
tail -f /var/log/mysql/error.log

text

#### مانیتورینگ پردازش‌ها
پردازش‌های Python
ps aux | grep python

اتصالات شبکه
netstat -tlnp

استفاده از منابع
iotop

text

### 12. Scripts تشخیصی

#### script بررسی سلامت
#!/bin/bash
echo "=== System Healt

echo "1. Checking Python processes..."
ps aux | grep python | grep -v

echo "2. Checking database connection..."
python -c "from config.database import db_manager; print('OK' if

echo "3. Checking disk space..."
echo "4. Checking memory..."
echo "5. Checking log file sizes..."
text

### 13. Backup و Recovery

#### Recovery از backup
متوقف کردن سرویس‌ها
sudo supervisorctl stop automotive-price-monitor:*

restore database
gunzip -c backup_20240115.sql.gz | mysql -u automotive -p automotive_prices

راه‌اندازی مجدد
sudo supervisorctl start automotive-price-monitor:*

text

### 14. مشکلات Performance

#### Query های کند
-- فعال‌سازی slow query log
SET GLOBAL slow_query_log = 'ON';
-- مشاهده queries کند
SELECT * FROM mysql.slow_log ORDER BY sta

text

#### بهینه‌سازی جداول
-- آنالیز جداول
ANALYZE TABLE products, price_history

-- بهینه‌سازی
OPTIMIZE TABLE products,

text

### 15. تماس با پشتیبانی

اگر مشکل حل نشد:

1. **لاگ‌های مرتبط** را جمع‌آوری کنید
2. **مراحل بازتولید** خطا را مستند کنید  
3. **اطلاعات سیستم** (OS, Python version, etc.) را ارائه دهید
4. **تنظیمات محیط** (environment variables) را چک کنید

**راه‌های تماس:**
- ایمیل: support@yourcompany.com
- تلگرام: @support_automotive
- GitHub Issues: https://github.com/yourrepo/issues

### 16. منابع مفید

- **مستندات Scrapy:** https://docs.scrapy.org/
- **مستندات Flask:** https://flask.palletsprojects.com/
- **WooCommerce REST API:** https://woocommerce.github.io/woocommerce-rest-api-docs/
- **MySQL Troubleshooting:** https://dev.mysql.com/doc/refman/8.0/en/problems.html