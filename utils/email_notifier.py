"""
Email notification utilities
"""
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
import yagmail
from config.settings import Config
from .logger import setup_logger

logger = setup_logger(__name__)


class EmailNotifier:
    """Handle email notifications for the system"""
    
    def __init__(self):
        self.config = Config()
        self.gmail_client = None
        self._init_gmail_client()
    
    def _init_gmail_client(self):
        """Initialize Gmail client if credentials are available"""
        try:
            if all([self.config.EMAIL_USER, self.config.EMAIL_PASSWORD]):
                self.gmail_client = yagmail.SMTP(
                    user=self.config.EMAIL_USER,
                    password=self.config.EMAIL_PASSWORD,
                    host=self.config.EMAIL_HOST,
                    port=self.config.EMAIL_PORT
                )
                logger.info("Email client initialized successfully")
            else:
                logger.warning("Email credentials not configured")
        except Exception as e:
            logger.error(f"Failed to initialize email client: {e}")
    
    def send_notification(self, subject: str, message: str, 
                         recipients: Optional[List[str]] = None,
                         html_content: Optional[str] = None,
                         attachments: Optional[List[str]] = None) -> bool:
        """Send email notification"""
        
        if not self.gmail_client:
            logger.warning("Email client not available, skipping notification")
            return False
        
        try:
            # Use default recipient if none specified
            if not recipients:
                recipients = [self.config.EMAIL_TO] if self.config.EMAIL_TO else []
            
            if not recipients:
                logger.warning("No recipients specified for email notification")
                return False
            
            # Prepare content
            contents = [message]
            if html_content:
                contents.append(html_content)
            
            # Send email
            self.gmail_client.send(
                to=recipients,
                subject=subject,
                contents=contents,
                attachments=attachments or []
            )
            
            logger.info(f"Email notification sent to {recipients}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False
    
    def send_scraping_report(self, results: Dict) -> bool:
        """Send scraping results report"""
        subject = f"Scraping Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Create message content
        message = f"""
Scraping Report
===============

Summary:
- Total Sites: {len(results.get('sites', {}))}
- Products Scraped: {results.get('total_products', 0)}
- Successful: {results.get('successful_sites', 0)}
- Failed: {results.get('failed_sites', 0)}
- Duration: {results.get('duration', 0):.2f} seconds

Site Results:
"""
        
        for site_name, site_result in results.get('sites', {}).items():
            status = "✅" if site_result.get('status') == 'completed' else "❌"
            message += f"- {status} {site_name}: {site_result.get('products_scraped', 0)} products\n"
        
        if results.get('errors'):
            message += f"\nErrors ({len(results['errors'])}):\n"
            for error in results['errors'][:5]:  # Limit to 5 errors
                message += f"- {error}\n"
        
        return self.send_notification(subject, message)
    
    def send_price_update_report(self, results: Dict) -> bool:
        """Send price update report"""
        subject = f"Price Update Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        message = f"""
Price Update Report
==================

Summary:
- Total Products: {results.get('total_products', 0)}
- Updated: {results.get('updated', 0)}
- Failed: {results.get('failed', 0)}
- Skipped: {results.get('skipped', 0)}
- Duration: {results.get('duration', 0):.2f} seconds

WooCommerce Integration:
- Products Synchronized: {results.get('wc_synchronized', 0)}
- API Errors: {len(results.get('api_errors', []))}

Price Statistics:
- Average Price: {results.get('avg_price', 0):,.0f} IRR
- Price Range: {results.get('min_price', 0):,.0f} - {results.get('max_price', 0):,.0f} IRR
"""
        
        if results.get('errors'):
            message += f"\nErrors:\n"
            for error in results['errors'][:3]:
                message += f"- {error}\n"
        
        return self.send_notification(subject, message)
    
    def send_error_alert(self, error_type: str, error_message: str, 
                        context: Optional[Dict] = None) -> bool:
        """Send error alert notification"""
        subject = f"🚨 Error Alert: {error_type}"
        
        message = f"""
Error Alert
===========

Type: {error_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Error Message:
{error_message}
"""
        
        if context:
            message += "\nContext:\n"
            for key, value in context.items():
                message += f"- {key}: {value}\n"
        
        message += """
Please check the system logs for more details.

System: Automotive Price Monitor
"""
        
        return self.send_notification(subject, message)
    
    def send_system_status(self, status_data: Dict) -> bool:
        """Send system status report"""
        subject = f"System Status Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        message = f"""
System Status Report
===================

Database:
- Total Products: {status_data.get('total_products', 0):,}
- Active Products: {status_data.get('active_products', 0):,}
- Products with Prices: {status_data.get('products_with_prices', 0):,}
- Last Scraping: {status_data.get('last_scraping', 'N/A')}

Site Status:
"""
        
        for site_name, site_status in status_data.get('sites', {}).items():
            status_icon = "🟢" if site_status.get('available', False) else "🔴"
            message += f"- {status_icon} {site_name}: {site_status.get('last_success', 'Never')}\n"
        
        message += f"""
Performance:
- Cache Hit Rate: {status_data.get('cache_hit_rate', 0):.1f}%
- Average Response Time: {status_data.get('avg_response_time', 0):.2f}s
- Error Rate: {status_data.get('error_rate', 0):.1f}%

System Resources:
- CPU Usage: {status_data.get('cpu_usage', 0):.1f}%
- Memory Usage: {status_data.get('memory_usage', 0):.1f}%
- Disk Usage: {status_data.get('disk_usage', 0):.1f}%
"""
        
        return self.send_notification(subject, message)
    
    def send_price_alert(self, alerts: List[Dict]) -> bool:
        """Send price change alerts"""
        if not alerts:
            return True
        
        subject = f"📊 Price Alerts - {len(alerts)} significant changes detected"
        
        message = """
Price Change Alerts
==================

The following products have significant price changes:

"""
        
        for alert in alerts[:10]:  # Limit to 10 alerts
            change_icon = "📈" if alert['change_percent'] > 0 else "📉"
            message += f"{change_icon} {alert['product_name']}\n"
            message += f"   Previous: {alert['previous_price']:,.0f} IRR\n"
            message += f"   Current: {alert['current_price']:,.0f} IRR\n"
            message += f"   Change: {alert['change_percent']:+.1f}%\n\n"
        
        if len(alerts) > 10:
            message += f"... and {len(alerts) - 10} more alerts\n"
        
        return self.send_notification(subject, message)
    
    def send_daily_summary(self, summary_data: Dict) -> bool:
        """Send daily summary report"""
        subject = f"📈 Daily Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ background-color: #f8f9fa; padding: 20px; text-align: center; }}
        .summary {{ background-color: #e9ecef; padding: 15px; margin: 10px 0; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background-color: white; border-radius: 5px; }}
        .good {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Automotive Price Monitor</h1>
        <h2>Daily Summary Report</h2>
        <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
    </div>
    
    <div class="summary">
        <h3>Key Metrics</h3>
        <div class="metric">
            <strong>Products Monitored:</strong><br>
            <span style="font-size: 24px;">{summary_data.get('total_products', 0):,}</span>
        </div>
        <div class="metric">
            <strong>Price Updates:</strong><br>
            <span style="font-size: 24px;">{summary_data.get('price_updates', 0):,}</span>
        </div>
        <div class="metric">
            <strong>Sites Scraped:</strong><br>
            <span style="font-size: 24px;">{summary_data.get('sites_scraped', 0)}</span>
        </div>
    </div>
    
    <div class="summary">
        <h3>Price Trends</h3>
        <p>Average price change: <strong>{summary_data.get('avg_price_change', 0):+.1f}%</strong></p>
        <p>Most volatile category: <strong>{summary_data.get('most_volatile_category', 'N/A')}</strong></p>
    </div>
</body>
</html>
"""
        
        # Plain text version
        text_content = f"""
Daily Summary Report - {datetime.now().strftime('%Y-%m-%d')}
========================================

Key Metrics:
- Products Monitored: {summary_data.get('total_products', 0):,}
- Price Updates: {summary_data.get('price_updates', 0):,}
- Sites Scraped: {summary_data.get('sites_scraped', 0)}

Price Trends:
- Average price change: {summary_data.get('avg_price_change', 0):+.1f}%
- Most volatile category: {summary_data.get('most_volatile_category', 'N/A')}

System Health:
- Uptime: {summary_data.get('uptime', 'Unknown')}
- Error Rate: {summary_data.get('error_rate', 0):.1f}%
"""
        
        return self.send_notification(subject, text_content, html_content=html_content)
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration"""
        test_result = {
            'configured': False,
            'connection_success': False,
            'send_success': False,
            'error_message': None
        }
        
        try:
            # Check if configured
            if not all([self.config.EMAIL_USER, self.config.EMAIL_PASSWORD, self.config.EMAIL_TO]):
                test_result['error_message'] = "Email configuration incomplete"
                return test_result
            
            test_result['configured'] = True
            
            # Test connection
            if self.gmail_client:
                test_result['connection_success'] = True
                
                # Test sending
                success = self.send_notification(
                    subject="Email Configuration Test",
                    message="This is a test email from Automotive Price Monitor system.",
                    recipients=[self.config.EMAIL_TO]
                )
                
                test_result['send_success'] = success
                if not success:
                    test_result['error_message'] = "Failed to send test email"
            else:
                test_result['error_message'] = "Failed to initialize email client"
                
        except Exception as e:
            test_result['error_message'] = str(e)
            logger.error(f"Email configuration test failed: {e}")
        
        return test_result
    
    def get_email_stats(self) -> Dict:
        """Get email notification statistics"""
        return {
            'configured': self.gmail_client is not None,
            'host': self.config.EMAIL_HOST,
            'port': self.config.EMAIL_PORT,
            'user': self.config.EMAIL_USER,
            'default_recipient': self.config.EMAIL_TO,
            'from_address': self.config.EMAIL_FROM
        }


# Create global email notifier instance
email_notifier = EmailNotifier()
