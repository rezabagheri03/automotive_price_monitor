"""
Price calculation and statistical analysis
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from database.models import Product, PriceHistory
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PriceCalculator:
    """Handle price calculations and statistical analysis"""
    
    def __init__(self):
        self.db_manager = db_manager
    
    def calculate_daily_prices(self, date: Optional[datetime] = None) -> Dict:
        """Calculate daily price statistics for all products"""
        if date is None:
            date = datetime.utcnow().date()
        
        logger.info(f"Calculating daily prices for {date}")
        
        try:
            with self.db_manager.get_session() as session:
                # Get all price data for the specified date
                price_data = session.query(PriceHistory).filter(
                    PriceHistory.scraped_at >= date,
                    PriceHistory.scraped_at < date + timedelta(days=1),
                    PriceHistory.site_price.isnot(None)
                ).all()
                
                if not price_data:
                    logger.warning(f"No price data found for {date}")
                    return {}
                
                # Group by product
                product_prices = {}
                for price_entry in price_data:
                    product_id = price_entry.product_id
                    if product_id not in product_prices:
                        product_prices[product_id] = []
                    product_prices[product_id].append(float(price_entry.site_price))
                
                # Calculate statistics for each product
                results = {}
                for product_id, prices in product_prices.items():
                    stats = self._calculate_price_statistics(prices)
                    results[product_id] = stats
                    
                    # Update database with calculated prices
                    self._update_calculated_prices(session, product_id, stats, date)
                
                logger.info(f"Calculated prices for {len(results)} products")
                return results
                
        except Exception as e:
            logger.error(f"Error calculating daily prices: {e}")
            raise
    
    def _calculate_price_statistics(self, prices: List[float]) -> Dict:
        """Calculate statistical measures for a list of prices"""
        if not prices:
            return {
                'avg_price': None,
                'min_price': None,
                'max_price': None,
                'median_price': None,
                'std_dev': None,
                'price_count': 0,
                'outliers_removed': 0
            }
        
        prices_array = np.array(prices)
        
        # Remove outliers using IQR method
        cleaned_prices, outliers_count = self._remove_outliers(prices_array)
        
        if len(cleaned_prices) == 0:
            cleaned_prices = prices_array  # Use original if all were outliers
            outliers_count = 0
        
        return {
            'avg_price': float(np.mean(cleaned_prices)),
            'min_price': float(np.min(cleaned_prices)),
            'max_price': float(np.max(cleaned_prices)),
            'median_price': float(np.median(cleaned_prices)),
            'std_dev': float(np.std(cleaned_prices)),
            'price_count': len(cleaned_prices),
            'outliers_removed': outliers_count
        }
    
    def _remove_outliers(self, prices: np.ndarray) -> Tuple[np.ndarray, int]:
        """Remove outliers using IQR method"""
        if len(prices) <= 2:
            return prices, 0
        
        Q1 = np.percentile(prices, 25)
        Q3 = np.percentile(prices, 75)
        IQR = Q3 - Q1
        
        # Define outlier boundaries
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Filter outliers
        mask = (prices >= lower_bound) & (prices <= upper_bound)
        cleaned_prices = prices[mask]
        outliers_count = len(prices) - len(cleaned_prices)
        
        return cleaned_prices, outliers_count
    
    def _update_calculated_prices(self, session, product_id: int, stats: Dict, date: datetime):
        """Update calculated prices in database"""
        try:
            # Find existing price history entry for today
            existing_entry = session.query(PriceHistory).filter(
                PriceHistory.product_id == product_id,
                PriceHistory.scraped_at >= date,
                PriceHistory.scraped_at < date + timedelta(days=1),
                PriceHistory.avg_price.isnot(None)
            ).first()
            
            if existing_entry:
                # Update existing entry
                existing_entry.avg_price = stats['avg_price']
                existing_entry.min_price = stats['min_price']
                existing_entry.max_price = stats['max_price']
                existing_entry.price_count = stats['price_count']
            else:
                # Create new entry with calculated prices
                price_entry = PriceHistory(
                    product_id=product_id,
                    site_name='calculated',
                    avg_price=stats['avg_price'],
                    min_price=stats['min_price'],
                    max_price=stats['max_price'],
                    price_count=stats['price_count'],
                    scraped_at=datetime.utcnow()
                )
                session.add(price_entry)
                
        except Exception as e:
            logger.error(f"Error updating calculated prices for product {product_id}: {e}")
    
    def get_price_trends(self, product_id: int, days: int = 30) -> Dict:
        """Get price trends for a product over specified days"""
        try:
            with self.db_manager.get_session() as session:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
                
                prices = session.query(PriceHistory).filter(
                    PriceHistory.product_id == product_id,
                    PriceHistory.scraped_at >= start_date,
                    PriceHistory.avg_price.isnot(None)
                ).order_by(PriceHistory.scraped_at).all()
                
                if not prices:
                    return {}
                
                # Convert to DataFrame for analysis
                df = pd.DataFrame([{
                    'date': p.scraped_at.date(),
                    'avg_price': float(p.avg_price),
                    'min_price': float(p.min_price) if p.min_price else None,
                    'max_price': float(p.max_price) if p.max_price else None,
                } for p in prices])
                
                # Calculate trends
                df = df.groupby('date').agg({
                    'avg_price': 'mean',
                    'min_price': 'min',
                    'max_price': 'max'
                }).reset_index()
                
                # Calculate trend direction
                if len(df) >= 2:
                    recent_avg = df.tail(7)['avg_price'].mean()
                    older_avg = df.head(7)['avg_price'].mean()
                    trend = 'increasing' if recent_avg > older_avg else 'decreasing'
                    trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
                else:
                    trend = 'stable'
                    trend_percentage = 0
                
                return {
                    'trend_direction': trend,
                    'trend_percentage': round(trend_percentage, 2),
                    'current_avg': float(df.tail(1)['avg_price'].iloc[0]),
                    'min_in_period': float(df['min_price'].min()),
                    'max_in_period': float(df['max_price'].max()),
                    'data_points': len(df),
                    'price_history': df.to_dict('records')
                }
                
        except Exception as e:
            logger.error(f"Error calculating price trends for product {product_id}: {e}")
            return {}
    
    def get_category_price_summary(self, category: str = None) -> Dict:
        """Get price summary by category"""
        try:
            with self.db_manager.get_session() as session:
                query = session.query(Product).join(PriceHistory)
                
                if category:
                    query = query.filter(Product.category == category)
                
                products = query.filter(
                    Product.is_active == True,
                    PriceHistory.avg_price.isnot(None)
                ).all()
                
                if not products:
                    return {}
                
                # Group by category
                category_data = {}
                for product in products:
                    cat = product.category
                    if cat not in category_data:
                        category_data[cat] = {
                            'products': [],
                            'prices': []
                        }
                    
                    if product.price_history:
                        latest_price = sorted(product.price_history, 
                                            key=lambda p: p.scraped_at, 
                                            reverse=True)[0]
                        if latest_price.avg_price:
                            category_data[cat]['products'].append(product.name)
                            category_data[cat]['prices'].append(float(latest_price.avg_price))
                
                # Calculate summary for each category
                summary = {}
                for cat, data in category_data.items():
                    if data['prices']:
                        prices = np.array(data['prices'])
                        summary[cat] = {
                            'product_count': len(data['products']),
                            'avg_price': float(np.mean(prices)),
                            'min_price': float(np.min(prices)),
                            'max_price': float(np.max(prices)),
                            'median_price': float(np.median(prices)),
                            'price_range': float(np.max(prices) - np.min(prices))
                        }
                
                return summary
                
        except Exception as e:
            logger.error(f"Error calculating category price summary: {e}")
            return {}
    
    def calculate_price_alerts(self, threshold_percentage: float = 10.0) -> List[Dict]:
        """Calculate price alerts for significant changes"""
        alerts = []
        
        try:
            with self.db_manager.get_session() as session:
                # Get products with recent price changes
                two_days_ago = datetime.utcnow() - timedelta(days=2)
                
                recent_prices = session.query(PriceHistory).filter(
                    PriceHistory.scraped_at >= two_days_ago,
                    PriceHistory.avg_price.isnot(None)
                ).order_by(PriceHistory.product_id, PriceHistory.scraped_at).all()
                
                # Group by product
                product_prices = {}
                for price in recent_prices:
                    product_id = price.product_id
                    if product_id not in product_prices:
                        product_prices[product_id] = []
                    product_prices[product_id].append(price)
                
                # Check for significant changes
                for product_id, prices in product_prices.items():
                    if len(prices) >= 2:
                        latest = prices[-1]
                        previous = prices[-2]
                        
                        if previous.avg_price and latest.avg_price:
                            change_percent = ((latest.avg_price - previous.avg_price) / previous.avg_price) * 100
                            
                            if abs(change_percent) >= threshold_percentage:
                                product = session.query(Product).get(product_id)
                                alerts.append({
                                    'product_id': product_id,
                                    'product_name': product.name if product else 'Unknown',
                                    'previous_price': float(previous.avg_price),
                                    'current_price': float(latest.avg_price),
                                    'change_percent': round(change_percent, 2),
                                    'alert_type': 'increase' if change_percent > 0 else 'decrease',
                                    'timestamp': latest.scraped_at
                                })
                
        except Exception as e:
            logger.error(f"Error calculating price alerts: {e}")
        
        return alerts
