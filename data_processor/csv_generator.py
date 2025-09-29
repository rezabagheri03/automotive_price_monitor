"""
CSV generation for WooCommerce integration
"""
import csv
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from database.models import Product, PriceHistory
from config.database import db_manager
from config.settings import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class CSVGenerator:
    """Generate CSV files for WooCommerce import"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.config = Config()
        self.output_dir = os.path.join(self.config.DATA_DIR, 'exports')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_woocommerce_csv(self, price_type: str = 'avg') -> str:
        """Generate CSV file for WooCommerce import
        
        Args:
            price_type: 'avg', 'min', or 'max'
            
        Returns:
            Path to generated CSV file
        """
        logger.info(f"Generating WooCommerce CSV with {price_type} prices")
        
        try:
            # Get product data with latest prices
            products_data = self._get_products_with_prices(price_type)
            
            if not products_data:
                raise ValueError("No product data found")
            
            # Generate CSV filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"woocommerce_import_{price_type}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Write CSV file
            self._write_woocommerce_csv(products_data, filepath)
            
            logger.info(f"Generated CSV file: {filepath} ({len(products_data)} products)")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating WooCommerce CSV: {e}")
            raise
    
    def _get_products_with_prices(self, price_type: str) -> List[Dict]:
        """Get products with latest price data"""
        try:
            with self.db_manager.get_session() as session:
                # Query products with their latest price history
                query = """
                SELECT 
                    p.id,
                    p.name,
                    p.sku,
                    p.category,
                    p.description,
                    p.image_url,
                    p.woocommerce_id,
                    ph.avg_price,
                    ph.min_price,
                    ph.max_price,
                    ph.scraped_at
                FROM products p
                LEFT JOIN (
                    SELECT DISTINCT
                        product_id,
                        FIRST_VALUE(avg_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as avg_price,
                        FIRST_VALUE(min_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as min_price,
                        FIRST_VALUE(max_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as max_price,
                        FIRST_VALUE(scraped_at) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as scraped_at,
                        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as rn
                    FROM price_history
                    WHERE avg_price IS NOT NULL
                ) ph ON p.id = ph.product_id AND ph.rn = 1
                WHERE p.is_active = 1 AND p.is_monitored = 1
                ORDER BY p.category, p.name
                """
                
                result = session.execute(query).fetchall()
                
                products_data = []
                for row in result:
                    # Select price based on type
                    if price_type == 'avg':
                        price = row.avg_price
                    elif price_type == 'min':
                        price = row.min_price
                    elif price_type == 'max':
                        price = row.max_price
                    else:
                        price = row.avg_price
                    
                    # Skip products without prices
                    if not price:
                        continue
                    
                    products_data.append({
                        'id': row.id,
                        'name': row.name or '',
                        'price': float(price),
                        'description': row.description or '',
                        'category': row.category or 'لوازم جانبی خودرو',
                        'image': row.image_url or '',
                        'sku': row.sku or f"AUTO-{row.id}",
                        'woocommerce_id': row.woocommerce_id,
                        'last_updated': row.scraped_at
                    })
                
                return products_data
                
        except Exception as e:
            logger.error(f"Error getting products with prices: {e}")
            raise
    
    def _write_woocommerce_csv(self, products_data: List[Dict], filepath: str):
        """Write CSV file in WooCommerce format"""
        # WooCommerce CSV format: name,price,description,category,image
        fieldnames = ['name', 'price', 'description', 'category', 'image']
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for product in products_data:
                # Format data for WooCommerce
                row = {
                    'name': product['name'],
                    'price': f"{product['price']:.0f}",  # Format as integer
                    'description': product['description'][:500] if product['description'] else '',
                    'category': product['category'],
                    'image': product['image']
                }
                writer.writerow(row)
    
    def generate_price_comparison_csv(self) -> str:
        """Generate CSV with price comparison across all sites"""
        logger.info("Generating price comparison CSV")
        
        try:
            with self.db_manager.get_session() as session:
                # Get price data from all sites for comparison
                query = """
                SELECT 
                    p.name,
                    p.category,
                    p.sku,
                    ph.site_name,
                    ph.site_price,
                    ph.avg_price,
                    ph.min_price,
                    ph.max_price,
                    ph.scraped_at
                FROM products p
                JOIN price_history ph ON p.id = ph.product_id
                WHERE ph.scraped_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                  AND ph.site_price IS NOT NULL
                ORDER BY p.name, ph.site_name
                """
                
                result = session.execute(query).fetchall()
                
                # Convert to DataFrame for easier processing
                df = pd.DataFrame(result, columns=[
                    'product_name', 'category', 'sku', 'site_name', 
                    'site_price', 'avg_price', 'min_price', 'max_price', 'scraped_at'
                ])
                
                # Pivot to show prices from different sites
                pivot_df = df.pivot_table(
                    index=['product_name', 'category', 'sku'],
                    columns='site_name',
                    values='site_price',
                    aggfunc='last'  # Get latest price if multiple entries
                ).reset_index()
                
                # Add statistical columns
                price_columns = [col for col in pivot_df.columns if col not in ['product_name', 'category', 'sku']]
                if price_columns:
                    pivot_df['avg_price'] = pivot_df[price_columns].mean(axis=1)
                    pivot_df['min_price'] = pivot_df[price_columns].min(axis=1)
                    pivot_df['max_price'] = pivot_df[price_columns].max(axis=1)
                    pivot_df['price_variance'] = pivot_df[price_columns].var(axis=1)
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"price_comparison_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)
                
                # Save to CSV
                pivot_df.to_csv(filepath, index=False, encoding='utf-8-sig')
                
                logger.info(f"Generated price comparison CSV: {filepath}")
                return filepath
                
        except Exception as e:
            logger.error(f"Error generating price comparison CSV: {e}")
            raise
    
    def generate_inventory_report_csv(self) -> str:
        """Generate inventory status report CSV"""
        logger.info("Generating inventory report CSV")
        
        try:
            with self.db_manager.get_session() as session:
                # Get inventory data
                query = """
                SELECT 
                    p.name,
                    p.category,
                    p.sku,
                    p.woocommerce_id,
                    COUNT(DISTINCT ph.site_name) as site_count,
                    ph_latest.avg_price,
                    ph_latest.min_price,
                    ph_latest.max_price,
                    ph_latest.scraped_at as last_updated,
                    p.is_active,
                    p.is_monitored
                FROM products p
                LEFT JOIN price_history ph ON p.id = ph.product_id
                LEFT JOIN (
                    SELECT DISTINCT
                        product_id,
                        FIRST_VALUE(avg_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as avg_price,
                        FIRST_VALUE(min_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as min_price,
                        FIRST_VALUE(max_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as max_price,
                        FIRST_VALUE(scraped_at) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as scraped_at
                    FROM price_history
                    WHERE avg_price IS NOT NULL
                ) ph_latest ON p.id = ph_latest.product_id
                GROUP BY p.id
                ORDER BY p.category, p.name
                """
                
                result = session.execute(query).fetchall()
                
                # Prepare data for CSV
                inventory_data = []
                for row in result:
                    inventory_data.append({
                        'Product Name': row.name,
                        'Category': row.category,
                        'SKU': row.sku or f"AUTO-{row[0]}",  # row[0] is id
                        'WooCommerce ID': row.woocommerce_id or '',
                        'Sites Count': row.site_count or 0,
                        'Average Price': f"{float(row.avg_price):.0f}" if row.avg_price else '',
                        'Min Price': f"{float(row.min_price):.0f}" if row.min_price else '',
                        'Max Price': f"{float(row.max_price):.0f}" if row.max_price else '',
                        'Last Updated': row.last_updated.strftime('%Y-%m-%d %H:%M') if row.last_updated else '',
                        'Active': 'Yes' if row.is_active else 'No',
                        'Monitored': 'Yes' if row.is_monitored else 'No',
                        'Status': self._get_product_status(row)
                    })
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"inventory_report_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)
                
                # Write CSV
                if inventory_data:
                    df = pd.DataFrame(inventory_data)
                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                
                logger.info(f"Generated inventory report CSV: {filepath} ({len(inventory_data)} products)")
                return filepath
                
        except Exception as e:
            logger.error(f"Error generating inventory report CSV: {e}")
            raise
    
    def _get_product_status(self, row) -> str:
        """Determine product status based on data"""
        if not row.is_active:
            return 'Inactive'
        elif not row.is_monitored:
            return 'Not Monitored'
        elif not row.avg_price:
            return 'No Price Data'
        elif row.site_count == 0:
            return 'No Site Data'
        elif row.last_updated and (datetime.utcnow() - row.last_updated).days > 7:
            return 'Stale Data'
        else:
            return 'OK'
    
    def generate_category_summary_csv(self) -> str:
        """Generate category summary CSV"""
        logger.info("Generating category summary CSV")
        
        try:
            with self.db_manager.get_session() as session:
                query = """
                SELECT 
                    p.category,
                    COUNT(p.id) as product_count,
                    COUNT(CASE WHEN p.is_active = 1 THEN 1 END) as active_products,
                    COUNT(CASE WHEN ph.avg_price IS NOT NULL THEN 1 END) as products_with_prices,
                    AVG(ph.avg_price) as avg_category_price,
                    MIN(ph.min_price) as min_category_price,
                    MAX(ph.max_price) as max_category_price,
                    COUNT(DISTINCT ph.site_name) as sites_covered
                FROM products p
                LEFT JOIN (
                    SELECT DISTINCT
                        product_id,
                        FIRST_VALUE(avg_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as avg_price,
                        FIRST_VALUE(min_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as min_price,
                        FIRST_VALUE(max_price) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as max_price,
                        FIRST_VALUE(site_name) OVER (PARTITION BY product_id ORDER BY scraped_at DESC) as site_name
                    FROM price_history
                    WHERE avg_price IS NOT NULL
                ) ph ON p.id = ph.product_id
                GROUP BY p.category
                ORDER BY product_count DESC
                """
                
                result = session.execute(query).fetchall()
                
                # Prepare summary data
                summary_data = []
                for row in result:
                    summary_data.append({
                        'Category': row.category,
                        'Total Products': row.product_count,
                        'Active Products': row.active_products,
                        'Products with Prices': row.products_with_prices,
                        'Coverage %': f"{(row.products_with_prices / row.product_count * 100):.1f}" if row.product_count > 0 else "0.0",
                        'Avg Price (IRR)': f"{float(row.avg_category_price):.0f}" if row.avg_category_price else '',
                        'Min Price (IRR)': f"{float(row.min_category_price):.0f}" if row.min_category_price else '',
                        'Max Price (IRR)': f"{float(row.max_category_price):.0f}" if row.max_category_price else '',
                        'Sites Covered': row.sites_covered or 0
                    })
                
                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"category_summary_{timestamp}.csv"
                filepath = os.path.join(self.output_dir, filename)
                
                # Write CSV
                if summary_data:
                    df = pd.DataFrame(summary_data)
                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                
                logger.info(f"Generated category summary CSV: {filepath}")
                return filepath
                
        except Exception as e:
            logger.error(f"Error generating category summary CSV: {e}")
            raise
    
    def get_export_files(self) -> List[Dict]:
        """Get list of generated export files"""
        files = []
        
        try:
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.csv'):
                    filepath = os.path.join(self.output_dir, filename)
                    stat = os.stat(filepath)
                    
                    files.append({
                        'name': filename,
                        'path': filepath,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_ctime),
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting export files: {e}")
        
        return files
