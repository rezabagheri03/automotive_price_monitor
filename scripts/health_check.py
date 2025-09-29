#!/usr/bin/env python3
"""
System health check script
"""
import os
import sys
import click
import json
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from utils.monitoring import system_monitor
from utils.email_notifier import email_notifier
from woocommerce_integration.api_client import WooCommerceClient
from config.database import db_manager
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.command()
@click.option('--verbose', is_flag=True, help='Verbose output')
@click.option('--notify', is_flag=True, help='Send notification if issues found')
@click.option('--output', help='Save results to JSON file')
def main(verbose, notify, output):
    """Perform comprehensive system health check"""
    
    logger.info("Starting system health check...")
    
    health_results = {
        'timestamp': datetime.utcnow().isoformat(),
        'overall_status': 'unknown',
        'checks': {},
        'recommendations': []
    }
    
    issues_found = []
    
    try:
        # 1. System Resources Check
        click.echo("Checking system resources...")
        system_stats = system_monitor.get_system_stats()
        
        if system_stats:
            health_results['checks']['system_resources'] = {
                'status': 'ok',
                'cpu_percent': system_stats['cpu_percent'],
                'memory_percent': system_stats['memory_percent'],
                'disk_percent': system_stats['disk_percent']
            }
            
            # Check thresholds
            if system_stats['cpu_percent'] > 80:
                issues_found.append(f"High CPU usage: {system_stats['cpu_percent']:.1f}%")
                health_results['checks']['system_resources']['status'] = 'warning'
            
            if system_stats['memory_percent'] > 85:
                issues_found.append(f"High memory usage: {system_stats['memory_percent']:.1f}%")
                health_results['checks']['system_resources']['status'] = 'warning'
            
            if system_stats['disk_percent'] > 90:
                issues_found.append(f"High disk usage: {system_stats['disk_percent']:.1f}%")
                health_results['checks']['system_resources']['status'] = 'error'
            
            if verbose:
                click.echo(f"  CPU: {system_stats['cpu_percent']:.1f}%")
                click.echo(f"  Memory: {system_stats['memory_percent']:.1f}%")
                click.echo(f"  Disk: {system_stats['disk_percent']:.1f}%")
        
        # 2. Database Connectivity Check
        click.echo("Checking database connectivity...")
        try:
            db_connected = db_manager.test_connection()
            if db_connected:
                health_results['checks']['database'] = {'status': 'ok', 'connected': True}
                if verbose:
                    click.echo("  Database: ✅ Connected")
            else:
                health_results['checks']['database'] = {'status': 'error', 'connected': False}
                issues_found.append("Database connection failed")
                click.echo("  Database: ❌ Connection failed")
        except Exception as e:
            health_results['checks']['database'] = {'status': 'error', 'error': str(e)}
            issues_found.append(f"Database error: {e}")
            click.echo(f"  Database: ❌ {e}")
        
        # 3. Database Statistics
        if health_results['checks']['database']['status'] == 'ok':
            click.echo("Checking database statistics...")
            db_stats = system_monitor.get_database_stats()
            
            health_results['checks']['database_stats'] = {
                'status': 'ok',
                'total_products': db_stats.get('total_products', 0),
                'active_products': db_stats.get('active_products', 0),
                'recent_price_entries': db_stats.get('recent_price_entries_24h', 0),
                'database_size_mb': db_stats.get('database_size_mb', 0)
            }
            
            if verbose:
                click.echo(f"  Products: {db_stats.get('total_products', 0):,} total, {db_stats.get('active_products', 0):,} active")
                click.echo(f"  Price entries (24h): {db_stats.get('recent_price_entries_24h', 0):,}")
                click.echo(f"  Database size: {db_stats.get('database_size_mb', 0):.2f} MB")
            
            # Check for data staleness
            if db_stats.get('recent_price_entries_24h', 0) == 0:
                issues_found.append("No price data updated in the last 24 hours")
                health_results['checks']['database_stats']['status'] = 'warning'
        
        # 4. WooCommerce API Check
        click.echo("Checking WooCommerce API...")
        try:
            wc_client = WooCommerceClient()
            wc_connection = wc_client.test_connection()
            
            if wc_connection:
                health_results['checks']['woocommerce'] = {'status': 'ok', 'connected': True}
                if verbose:
                    click.echo("  WooCommerce API: ✅ Connected")
            else:
                health_results['checks']['woocommerce'] = {'status': 'error', 'connected': False}
                issues_found.append("WooCommerce API connection failed")
                click.echo("  WooCommerce API: ❌ Connection failed")
        except Exception as e:
            health_results['checks']['woocommerce'] = {'status': 'error', 'error': str(e)}
            issues_found.append(f"WooCommerce API error: {e}")
            click.echo(f"  WooCommerce API: ❌ {e}")
        
        # 5. Scraping Performance Check
        click.echo("Checking scraping performance...")
        scraping_perf = system_monitor.get_scraping_performance()
        
        if scraping_perf and not scraping_perf.get('no_data'):
            success_rate = scraping_perf.get('success_rate_7d', 0)
            
            health_results['checks']['scraping_performance'] = {
                'status': 'ok' if success_rate >= 90 else 'warning' if success_rate >= 70 else 'error',
                'success_rate_7d': success_rate,
                'total_runs_7d': scraping_perf.get('total_runs_7d', 0),
                'avg_duration': scraping_perf.get('avg_duration_seconds', 0)
            }
            
            if verbose:
                click.echo(f"  Success rate (7d): {success_rate:.1f}%")
                click.echo(f"  Total runs (7d): {scraping_perf.get('total_runs_7d', 0)}")
                click.echo(f"  Avg duration: {scraping_perf.get('avg_duration_seconds', 0):.1f}s")
            
            if success_rate < 90:
                issues_found.append(f"Low scraping success rate: {success_rate:.1f}%")
        else:
            health_results['checks']['scraping_performance'] = {'status': 'warning', 'message': 'No recent scraping data'}
            issues_found.append("No recent scraping activity detected")
        
        # 6. Email Configuration Check
        click.echo("Checking email configuration...")
        email_test = email_notifier.test_email_configuration()
        
        health_results['checks']['email'] = {
            'status': 'ok' if email_test['configured'] and email_test['connection_success'] else 'warning',
            'configured': email_test['configured'],
            'connection_success': email_test.get('connection_success', False)
        }
        
        if not email_test['configured']:
            health_results['recommendations'].append("Configure email settings for notifications")
        elif not email_test.get('connection_success'):
            issues_found.append("Email configuration test failed")
        
        if verbose:
            status = "✅" if email_test['configured'] and email_test.get('connection_success') else "⚠️"
            click.echo(f"  Email: {status} {'Configured and working' if email_test['configured'] and email_test.get('connection_success') else 'Issues detected'}")
        
        # 7. Disk Space Check
        click.echo("Checking disk space...")
        if system_stats and system_stats['disk_percent'] > 85:
            health_results['recommendations'].append("Consider cleaning up old log files and backups")
        
        # Determine overall status
        if any(check.get('status') == 'error' for check in health_results['checks'].values()):
            health_results['overall_status'] = 'unhealthy'
        elif any(check.get('status') == 'warning' for check in health_results['checks'].values()) or issues_found:
            health_results['overall_status'] = 'degraded'
        else:
            health_results['overall_status'] = 'healthy'
        
        health_results['issues'] = issues_found
        
        # Output results
        status_icon = {
            'healthy': '✅',
            'degraded': '⚠️', 
            'unhealthy': '❌'
        }.get(health_results['overall_status'], '❓')
        
        click.echo(f"\nOverall System Status: {status_icon} {health_results['overall_status'].upper()}")
        
        if issues_found:
            click.echo("\nIssues Found:")
            for issue in issues_found:
                click.echo(f"  - {issue}")
        
        if health_results['recommendations']:
            click.echo("\nRecommendations:")
            for rec in health_results['recommendations']:
                click.echo(f"  - {rec}")
        
        # Save to file if requested
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(health_results, f, indent=2, ensure_ascii=False, default=str)
            click.echo(f"\nResults saved to: {output}")
        
        # Send notification if issues found
        if notify and (issues_found or health_results['overall_status'] != 'healthy'):
            _send_health_check_notification(health_results)
        
        logger.info(f"Health check completed: {health_results['overall_status']}")
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        click.echo(f"❌ Health check failed: {e}")
        sys.exit(1)


def _send_health_check_notification(health_results: Dict):
    """Send health check notification"""
    try:
        status = health_results['overall_status']
        subject = f"🏥 Health Check Report - {status.upper()}"
        
        message = f"""
System Health Check Report
=========================

Overall Status: {status.upper()}
Check Time: {health_results['timestamp']}

Issues Found:
"""
        
        for issue in health_results.get('issues', []):
            message += f"- {issue}\n"
        
        if health_results.get('recommendations'):
            message += "\nRecommendations:\n"
            for rec in health_results['recommendations']:
                message += f"- {rec}\n"
        
        message += """
Check the system dashboard for more detailed information.
"""
        
        email_notifier.send_notification(subject, message)
        
    except Exception as e:
        logger.error(f"Error sending health check notification: {e}")


if __name__ == '__main__':
    main()
