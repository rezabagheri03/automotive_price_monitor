#!/usr/bin/env python3
"""
Main script to run the automotive price scraper
"""
import os
import sys
import click
import uuid
from datetime import datetime
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.scrapy_settings import SCRAPY_SETTINGS
from database.models import ScrapingLog
from config.database import db_manager
from utils.logger import setup_logger
from utils.email_notifier import email_notifier

logger = setup_logger(__name__)


@click.command()
@click.option('--spider', help='Run specific spider (e.g., autonik, bmwstor)')
@click.option('--test', is_flag=True, help='Run in test mode with limited products')
@click.option('--concurrent', type=int, help='Override concurrent requests setting')
@click.option('--delay', type=float, help='Override download delay setting')
@click.option('--output', help='Output file path for scraped data')
@click.option('--notify', is_flag=True, default=True, help='Send email notifications')
def main(spider, test, concurrent, delay, output, notify):
    """Run the automotive price scraper"""
    
    session_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    logger.info(f"Starting scraper session: {session_id}")
    logger.info(f"Parameters: spider={spider}, test={test}, concurrent={concurrent}, delay={delay}")
    
    try:
        # Get project settings
        settings = get_project_settings()
        settings.setdict(SCRAPY_SETTINGS)
        
        # Override settings if provided
        if concurrent:
            settings.set('CONCURRENT_REQUESTS', concurrent)
        if delay:
            settings.set('DOWNLOAD_DELAY', delay)
        if test:
            settings.set('CLOSESPIDER_ITEMCOUNT', 100)  # Limit to 100 items in test mode
        if output:
            settings.set('FEEDS', {output: {'format': 'json'}})
        
        # Initialize scraping log
        log_entry = _create_scraping_log(session_id, spider or 'all', start_time)
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Add spiders to run
        spiders_to_run = []
        if spider:
            # Run specific spider
            if spider in get_available_spiders():
                spiders_to_run.append(spider)
            else:
                raise ValueError(f"Spider '{spider}' not found. Available spiders: {get_available_spiders()}")
        else:
            # Run all spiders
            spiders_to_run = get_available_spiders()
        
        # Start spiders
        for spider_name in spiders_to_run:
            process.crawl(spider_name, session_id=session_id)
        
        # Run the process
        logger.info(f"Starting {len(spiders_to_run)} spider(s): {spiders_to_run}")
        process.start()
        
        # Update log entry with completion
        _update_scraping_log(log_entry, 'completed', datetime.utcnow())
        
        # Send notification if enabled
        if notify:
            _send_completion_notification(session_id, spiders_to_run, start_time)
        
        logger.info(f"Scraper session completed: {session_id}")
        
    except Exception as e:
        logger.error(f"Scraper session failed: {e}")
        
        # Update log with failure
        if 'log_entry' in locals():
            _update_scraping_log(log_entry, 'failed', datetime.utcnow(), str(e))
        
        # Send error notification
        if notify:
            email_notifier.send_error_alert(
                'Scraper Failure',
                f"Scraper session {session_id} failed: {str(e)}"
            )
        
        sys.exit(1)


def get_available_spiders() -> list:
    """Get list of available spider names"""
    return [
        'autonik',
        'bmwstor', 
        'benzstor',
        'mryadaki',
        'carinopart',
        'japanstor',
        'shojapart',
        'luxyadak',
        'parsianlent',
        'iranrenu',
        'automoby',
        'oilcity'
    ]


def _create_scraping_log(session_id: str, spider_name: str, start_time: datetime) -> int:
    """Create initial scraping log entry"""
    try:
        with db_manager.get_session() as session:
            log_entry = ScrapingLog(
                session_id=session_id,
                site_name=spider_name,
                spider_name=spider_name,
                status='started',
                start_time=start_time,
                initiated_by='script'
            )
            session.add(log_entry)
            session.flush()
            return log_entry.id
            
    except Exception as e:
        logger.error(f"Error creating scraping log: {e}")
        return None


def _update_scraping_log(log_id: int, status: str, end_time: datetime, error_message: str = None):
    """Update scraping log with completion details"""
    if not log_id:
        return
    
    try:
        with db_manager.get_session() as session:
            log_entry = session.query(ScrapingLog).get(log_id)
            if log_entry:
                log_entry.status = status
                log_entry.end_time = end_time
                log_entry.duration_seconds = int((end_time - log_entry.start_time).total_seconds())
                
                if error_message:
                    log_entry.error_message = error_message
                
    except Exception as e:
        logger.error(f"Error updating scraping log: {e}")


def _send_completion_notification(session_id: str, spiders: list, start_time: datetime):
    """Send completion notification email"""
    try:
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        subject = f"Scraping Completed - Session {session_id[:8]}"
        message = f"""
Scraping Session Completed
=========================

Session ID: {session_id}
Spiders Run: {', '.join(spiders)}
Duration: {duration:.2f} seconds
Completed At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Check the dashboard for detailed results.
"""
        
        email_notifier.send_notification(subject, message)
        
    except Exception as e:
        logger.error(f"Error sending completion notification: {e}")


if __name__ == '__main__':
    main()
