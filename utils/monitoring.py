"""
System monitoring utilities
"""
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import threading
from database.models import Product, PriceHistory, ScrapingLog
from config.database import db_manager
from .logger import setup_logger
from .email_notifier import email_notifier

logger = setup_logger(__name__)


class SystemMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.db_manager = db_manager
        self.start_time = datetime.utcnow()
        self.monitoring_active = False
        self.monitoring_thread = None
        self.alerts_sent = {}
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'disk_percent': 90.0,
            'error_rate_percent': 10.0,
            'response_time_seconds': 30.0
        }
    
    def get_system_stats(self) -> Dict:
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk_percent,
                'disk_used_gb': disk.used / (1024 * 1024 * 1024),
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'process_memory_mb': process_memory.rss / (1024 * 1024),
                'process_threads': process.num_threads()
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with self.db_manager.get_session() as session:
                # Product statistics
                total_products = session.query(Product).count()
                active_products = session.query(Product).filter(Product.is_active == True).count()
                monitored_products = session.query(Product).filter(Product.is_monitored == True).count()
                
                # Price history statistics
                total_price_entries = session.query(PriceHistory).count()
                recent_prices = session.query(PriceHistory).filter(
                    PriceHistory.scraped_at >= datetime.utcnow() - timedelta(hours=24)
                ).count()
                
                # Scraping log statistics
                recent_logs = session.query(ScrapingLog).filter(
                    ScrapingLog.start_time >= datetime.utcnow() - timedelta(hours=24)
                ).all()
                
                successful_scrapes = sum(1 for log in recent_logs if log.status == 'completed')
                failed_scrapes = sum(1 for log in recent_logs if log.status == 'failed')
                
                # Calculate database size (approximation)
                table_stats = session.execute("""
                    SELECT 
                        TABLE_NAME,
                        TABLE_ROWS,
                        ROUND(((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024), 2) AS 'Size_MB'
                    FROM information_schema.TABLES 
                    WHERE TABLE_SCHEMA = %s
                """, (session.bind.url.database,)).fetchall()
                
                total_size_mb = sum(row[2] for row in table_stats if row[2])
                
                return {
                    'total_products': total_products,
                    'active_products': active_products,
                    'monitored_products': monitored_products,
                    'total_price_entries': total_price_entries,
                    'recent_price_entries_24h': recent_prices,
                    'successful_scrapes_24h': successful_scrapes,
                    'failed_scrapes_24h': failed_scrapes,
                    'error_rate_24h': (failed_scrapes / max(len(recent_logs), 1)) * 100,
                    'database_size_mb': total_size_mb,
                    'table_stats': [{'name': row[0], 'rows': row[1], 'size_mb': row[2]} for row in table_stats]
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_scraping_performance(self) -> Dict:
        """Get scraping performance metrics"""
        try:
            with self.db_manager.get_session() as session:
                # Recent scraping logs (last 7 days)
                recent_logs = session.query(ScrapingLog).filter(
                    ScrapingLog.start_time >= datetime.utcnow() - timedelta(days=7)
                ).all()
                
                if not recent_logs:
                    return {'no_data': True}
                
                # Calculate metrics
                total_runs = len(recent_logs)
                successful_runs = sum(1 for log in recent_logs if log.status == 'completed')
                failed_runs = sum(1 for log in recent_logs if log.status == 'failed')
                
                # Average duration
                completed_logs = [log for log in recent_logs if log.duration_seconds]
                avg_duration = sum(log.duration_seconds for log in completed_logs) / len(completed_logs) if completed_logs else 0
                
                # Products scraped
                total_products_scraped = sum(log.products_scraped or 0 for log in recent_logs)
                avg_products_per_run = total_products_scraped / total_runs if total_runs > 0 else 0
                
                # Site performance
                site_stats = {}
                for log in recent_logs:
                    site = log.site_name
                    if site not in site_stats:
                        site_stats[site] = {'runs': 0, 'success': 0, 'products': 0, 'duration': 0}
                    
                    site_stats[site]['runs'] += 1
                    if log.status == 'completed':
                        site_stats[site]['success'] += 1
                    site_stats[site]['products'] += log.products_scraped or 0
                    site_stats[site]['duration'] += log.duration_seconds or 0
                
                # Calculate success rates per site
                for site, stats in site_stats.items():
                    stats['success_rate'] = (stats['success'] / stats['runs']) * 100 if stats['runs'] > 0 else 0
                    stats['avg_duration'] = stats['duration'] / stats['runs'] if stats['runs'] > 0 else 0
                    stats['avg_products'] = stats['products'] / stats['runs'] if stats['runs'] > 0 else 0
                
                return {
                    'total_runs_7d': total_runs,
                    'successful_runs_7d': successful_runs,
                    'failed_runs_7d': failed_runs,
                    'success_rate_7d': (successful_runs / total_runs) * 100 if total_runs > 0 else 0,
                    'avg_duration_seconds': avg_duration,
                    'total_products_scraped_7d': total_products_scraped,
                    'avg_products_per_run': avg_products_per_run,
                    'site_performance': site_stats
                }
                
        except Exception as e:
            logger.error(f"Error getting scraping performance: {e}")
            return {}
    
    def check_health(self) -> Dict:
        """Perform comprehensive health check"""
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        issues = []
        
        try:
            # System resource check
            system_stats = self.get_system_stats()
            if system_stats:
                if system_stats['cpu_percent'] > self.thresholds['cpu_percent']:
                    issues.append(f"High CPU usage: {system_stats['cpu_percent']:.1f}%")
                
                if system_stats['memory_percent'] > self.thresholds['memory_percent']:
                    issues.append(f"High memory usage: {system_stats['memory_percent']:.1f}%")
                
                if system_stats['disk_percent'] > self.thresholds['disk_percent']:
                    issues.append(f"High disk usage: {system_stats['disk_percent']:.1f}%")
                
                health_status['checks']['system_resources'] = {
                    'status': 'warning' if any('High' in issue for issue in issues) else 'ok',
                    'details': system_stats
                }
            
            # Database connectivity check
            try:
                db_connected = self.db_manager.test_connection()
                health_status['checks']['database'] = {
                    'status': 'ok' if db_connected else 'error',
                    'connected': db_connected
                }
                if not db_connected:
                    issues.append("Database connection failed")
            except Exception as e:
                health_status['checks']['database'] = {
                    'status': 'error',
                    'error': str(e)
                }
                issues.append(f"Database error: {e}")
            
            # Scraping performance check
            scraping_perf = self.get_scraping_performance()
            if scraping_perf and not scraping_perf.get('no_data'):
                success_rate = scraping_perf.get('success_rate_7d', 0)
                if success_rate < 90:
                    issues.append(f"Low scraping success rate: {success_rate:.1f}%")
                
                health_status['checks']['scraping_performance'] = {
                    'status': 'warning' if success_rate < 90 else 'ok',
                    'success_rate': success_rate
                }
            
            # Determine overall status
            if any('error' in check['status'] for check in health_status['checks'].values()):
                health_status['overall_status'] = 'unhealthy'
            elif any('warning' in check['status'] for check in health_status['checks'].values()):
                health_status['overall_status'] = 'degraded'
            
            health_status['issues'] = issues
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status
    
    def send_alert_if_needed(self, alert_type: str, message: str, cooldown_hours: int = 1):
        """Send alert email if not sent recently"""
        now = datetime.utcnow()
        last_sent = self.alerts_sent.get(alert_type)
        
        if not last_sent or (now - last_sent).total_seconds() > cooldown_hours * 3600:
            success = email_notifier.send_error_alert(alert_type, message)
            if success:
                self.alerts_sent[alert_type] = now
                logger.info(f"Alert sent for {alert_type}")
    
    def start_monitoring(self, check_interval: int = 300):
        """Start continuous monitoring"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(check_interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info(f"System monitoring started with {check_interval}s interval")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def _monitoring_loop(self, check_interval: int):
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                health = self.check_health()
                
                # Send alerts for critical issues
                if health['overall_status'] == 'unhealthy':
                    self.send_alert_if_needed(
                        'system_unhealthy',
                        f"System health check failed: {', '.join(health.get('issues', []))}"
                    )
                elif health['overall_status'] == 'degraded':
                    self.send_alert_if_needed(
                        'system_degraded',
                        f"System performance degraded: {', '.join(health.get('issues', []))}"
                    )
                
                # Check specific thresholds
                system_stats = self.get_system_stats()
                if system_stats:
                    if system_stats['cpu_percent'] > self.thresholds['cpu_percent']:
                        self.send_alert_if_needed(
                            'high_cpu',
                            f"High CPU usage detected: {system_stats['cpu_percent']:.1f}%"
                        )
                    
                    if system_stats['memory_percent'] > self.thresholds['memory_percent']:
                        self.send_alert_if_needed(
                            'high_memory',
                            f"High memory usage detected: {system_stats['memory_percent']:.1f}%"
                        )
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(check_interval)
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            'monitoring_active': self.monitoring_active,
            'start_time': self.start_time.isoformat(),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'thresholds': self.thresholds,
            'recent_alerts': {
                alert_type: last_sent.isoformat()
                for alert_type, last_sent in self.alerts_sent.items()
            }
        }
    
    def update_thresholds(self, new_thresholds: Dict):
        """Update monitoring thresholds"""
        self.thresholds.update(new_thresholds)
        logger.info(f"Updated monitoring thresholds: {new_thresholds}")


# Create global system monitor instance
system_monitor = SystemMonitor()
