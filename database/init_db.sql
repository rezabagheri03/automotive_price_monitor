-- Automotive Price Monitor Database Schema
-- MySQL/MariaDB compatible

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS automotive_prices 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE automotive_prices;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    category VARCHAR(100) NOT NULL,
    description TEXT,
    image_url VARCHAR(500),
    woocommerce_id INT,
    woocommerce_sku VARCHAR(100),
    site_urls JSON,
    is_active BOOLEAN DEFAULT TRUE,
    is_monitored BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_scraped TIMESTAMP NULL,
    
    INDEX idx_product_name (name),
    INDEX idx_product_sku (sku),
    INDEX idx_product_category (category),
    INDEX idx_product_woocommerce_id (woocommerce_id),
    INDEX idx_product_category_active (category, is_active),
    INDEX idx_product_name_category (name, category),
    INDEX idx_product_updated_monitored (updated_at, is_monitored),
    INDEX idx_product_active (is_active),
    INDEX idx_product_monitored (is_monitored),
    INDEX idx_product_created (created_at),
    INDEX idx_product_last_scraped (last_scraped)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create price_history table
CREATE TABLE IF NOT EXISTS price_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    site_price DECIMAL(10,2),
    site_url VARCHAR(500),
    site_availability BOOLEAN DEFAULT TRUE,
    avg_price DECIMAL(10,2),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    price_count INT DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'IRR',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    
    INDEX idx_price_product_id (product_id),
    INDEX idx_price_site_name (site_name),
    INDEX idx_price_scraped_at (scraped_at),
    INDEX idx_price_avg_price (avg_price),
    INDEX idx_price_min_price (min_price),
    INDEX idx_price_max_price (max_price),
    INDEX idx_price_product_date (product_id, scraped_at),
    INDEX idx_price_site_date (site_name, scraped_at),
    INDEX idx_price_avg_date (avg_price, scraped_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create scraping_logs table
CREATE TABLE IF NOT EXISTS scraping_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(50) NOT NULL,
    site_name VARCHAR(100) NOT NULL,
    spider_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    products_found INT DEFAULT 0,
    products_scraped INT DEFAULT 0,
    prices_extracted INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    duration_seconds INT,
    pages_scraped INT DEFAULT 0,
    requests_made INT DEFAULT 0,
    error_message TEXT,
    error_details JSON,
    initiated_by VARCHAR(100),
    
    INDEX idx_log_session_id (session_id),
    INDEX idx_log_site_name (site_name),
    INDEX idx_log_status (status),
    INDEX idx_log_start_time (start_time),
    INDEX idx_log_session_site (session_id, site_name),
    INDEX idx_log_status_time (status, start_time),
    INDEX idx_log_site_time (site_name, start_time)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create site_configs table
CREATE TABLE IF NOT EXISTS site_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_name VARCHAR(100) UNIQUE NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    selectors JSON,
    request_delay DECIMAL(3,1) DEFAULT 2.0,
    concurrent_requests INT DEFAULT 5,
    user_agent VARCHAR(500),
    requires_javascript BOOLEAN DEFAULT FALSE,
    uses_pagination BOOLEAN DEFAULT TRUE,
    max_pages INT DEFAULT 100,
    requires_auth BOOLEAN DEFAULT FALSE,
    auth_config JSON,
    is_active BOOLEAN DEFAULT TRUE,
    is_available BOOLEAN DEFAULT TRUE,
    last_successful_scrape TIMESTAMP NULL,
    consecutive_failures INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_site_name (site_name),
    INDEX idx_site_active (is_active),
    INDEX idx_site_available (is_available),
    INDEX idx_site_last_scrape (last_successful_scrape)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(128),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP NULL,
    login_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_user_username (username),
    INDEX idx_user_email (email),
    INDEX idx_user_role (role),
    INDEX idx_user_active (is_active)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT IGNORE INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified) 
VALUES (
    'admin', 
    'admin@lavazembazaar.com', 
    'pbkdf2:sha256:260000$8V1ZqY3xF2dE1KfI$8f9a02c96b7b8e9c5b8f7c6e4d3a2b1c0e9f8a7b6c5d4e3f2a1b0c9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0e9f8a7', 
    'System', 
    'Administrator', 
    'admin', 
    TRUE, 
    TRUE
);

-- Insert default site configurations
INSERT IGNORE INTO site_configs (site_name, base_url, selectors, request_delay, concurrent_requests, user_agent) VALUES
('auto-nik.com', 'https://auto-nik.com', 
 '{"price": ".price, .price-value", "title": "h1, .product-title", "availability": ".availability, .in-stock"}', 
 2.0, 5, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),

('bmwstor.com', 'https://bmwstor.com', 
 '{"price": ".price, .woocommerce-Price-amount", "title": ".product-title, h1", "availability": ".stock-status"}', 
 1.5, 8, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),

('benzstor.com', 'https://benzstor.com', 
 '{"price": ".price-value, .product-price", "title": ".product-name, h1", "availability": ".availability-status"}', 
 2.0, 6, 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),

('mryadaki.com', 'https://mryadaki.com', 
 '{"price": ".price, .product-price-value", "title": ".product-title", "availability": ".stock-info"}', 
 1.8, 10, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),

('carinopart.com', 'https://carinopart.com', 
 '{"price": ".price-amount, .current-price", "title": ".product-name", "availability": ".stock-status"}', 
 2.2, 4, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'),

('japanstor.com', 'https://japanstor.com', 
 '{"price": ".price, .product-price", "title": ".product-title", "availability": ".in-stock, .available"}', 
 1.6, 7, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101'),

('shojapart.com', 'https://shojapart.com', 
 '{"price": ".price-value, .wc-price", "title": "h1, .entry-title", "availability": ".availability"}', 
 2.4, 5, 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101'),

('luxyadak.com', 'https://luxyadak.com', 
 '{"price": ".price, .amount", "title": ".product-title", "availability": ".stock-available"}', 
 1.9, 6, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),

('parsianlent.com', 'https://parsianlent.com', 
 '{"price": ".price-current, .product-price", "title": ".product-name", "availability": ".availability-text"}', 
 2.1, 5, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),

('iranrenu.com', 'https://iranrenu.com', 
 '{"price": ".price, .sale-price", "title": ".product-title", "availability": ".stock-status"}', 
 1.7, 8, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),

('automoby.ir', 'https://automoby.ir', 
 '{"price": ".price-value, .current-price", "title": ".item-title", "availability": ".availability"}', 
 2.3, 4, 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),

('oil-city.ir', 'https://www.oil-city.ir', 
 '{"price": ".price, .product-price", "title": ".product-name", "availability": ".in-stock"}', 
 1.4, 9, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

-- Create views for reporting
CREATE OR REPLACE VIEW product_price_summary AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.sku,
    p.woocommerce_id,
    ph_latest.avg_price,
    ph_latest.min_price,
    ph_latest.max_price,
    ph_latest.price_count,
    ph_latest.scraped_at as last_price_update,
    p.is_active,
    p.is_monitored
FROM products p
LEFT JOIN (
    SELECT DISTINCT
        product_id,
        FIRST_VALUE(avg_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as avg_price,
        FIRST_VALUE(min_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as min_price,
        FIRST_VALUE(max_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as max_price,
        FIRST_VALUE(price_count) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as price_count,
        FIRST_VALUE(scraped_at) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as scraped_at
    FROM price_history
) ph_latest ON p.id = ph_latest.product_id;

-- Create view for scraping statistics
CREATE OR REPLACE VIEW scraping_statistics AS
SELECT 
    DATE(start_time) as scrape_date,
    site_name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    SUM(products_scraped) as total_products_scraped,
    SUM(prices_extracted) as total_prices_extracted,
    AVG(duration_seconds) as avg_duration_seconds,
    MAX(end_time) as last_run_time
FROM scraping_logs
GROUP BY DATE(start_time), site_name
ORDER BY scrape_date DESC, site_name;

-- Optimize tables
OPTIMIZE TABLE products, price_history, scraping_logs, site_configs, users;

-- Show table statistics
SELECT 
    TABLE_NAME,
    TABLE_ROWS,
    ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'automotive_prices'
ORDER BY TABLE_NAME;
