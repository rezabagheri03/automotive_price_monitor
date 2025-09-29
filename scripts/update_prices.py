#!/usr/bin/env python3
"""
Script to update WooCommerce prices from scraped data
"""
import os
import sys
import click
from datetime import datetime

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from data_processor.price_calculator import PriceCalculator
from data_processor.csv_generator import CSVGenerator
from woocommerce_integration.csv_importer import CSVImporter
from woocommerce_integration.batch_processor import BatchProcessor
from utils.logger import setup_logger
from utils.email_notifier import email_notifier

logger = setup_logger(__name__)


@click.command()
@click.option('--price-type', type=click.Choice(['avg', 'min', 'max']), 
              default='avg', help='Price type to use for updates')
@click.option('--dry-run', is_flag=True, help='Run without actually updating WooCommerce')
@click.option('--batch-size', type=int, default=50, help='Batch size for API calls')
@click.option('--notify', is_flag=True, default=True, help='Send email notifications')
@click.option('--generate-csv-only', is_flag=True, help='Only generate CSV, do not import')
def main(price_type, dry_run, batch_size, notify, generate_csv_only):
    """Update WooCommerce prices from scraped data"""
    
    start_time = datetime.utcnow()
    logger.info(f"Starting price update process")
    logger.info(f"Parameters: price_type={price_type}, dry_run={dry_run}, batch_size={batch_size}")
    
    results = {
        'start_time': start_time,
        'price_type': price_type,
        'dry_run': dry_run,
        'steps': {}
    }
    
    try:
        # Step 1: Calculate daily prices
        logger.info("Step 1: Calculating daily price statistics...")
        calculator = PriceCalculator()
        price_calculations = calculator.calculate_daily_prices()
        
        results['steps']['price_calculation'] = {
            'status': 'completed',
            'products_calculated': len(price_calculations),
            'duration': (datetime.utcnow() - start_time).total_seconds()
        }
        
        if not price_calculations:
            raise ValueError("No price data available for calculation")
        
        logger.info(f"Calculated prices for {len(price_calculations)} products")
        
        # Step 2: Generate CSV file
        logger.info("Step 2: Generating WooCommerce CSV...")
        csv_generator = CSVGenerator()
        csv_path = csv_generator.generate_woocommerce_csv(price_type)
        
        results['steps']['csv_generation'] = {
            'status': 'completed',
            'csv_path': csv_path,
            'duration': (datetime.utcnow() - start_time).total_seconds()
        }
        
        logger.info(f"Generated CSV file: {csv_path}")
        
        if generate_csv_only:
            logger.info("CSV generation completed, skipping WooCommerce import")
            results['steps']['woocommerce_import'] = {
                'status': 'skipped',
                'reason': 'generate_csv_only flag set'
            }
        else:
            # Step 3: Import to WooCommerce
            logger.info("Step 3: Importing to WooCommerce...")
            csv_importer = CSVImporter()
            import_results = csv_importer.import_csv_to_woocommerce(
                csv_path=csv_path,
                price_type=price_type,
                dry_run=dry_run
            )
            
            results['steps']['woocommerce_import'] = {
                'status': 'completed',
                'results': import_results,
                'duration': (datetime.utcnow() - start_time).total_seconds()
            }
            
            logger.info(f"WooCommerce import completed: {import_results}")
        
        # Step 4: Generate reports
        logger.info("Step 4: Generating reports...")
        comparison_csv = csv_generator.generate_price_comparison_csv()
        inventory_csv = csv_generator.generate_inventory_report_csv()
        
        results['steps']['reporting'] = {
            'status': 'completed',
            'comparison_csv': comparison_csv,
            'inventory_csv': inventory_csv,
            'duration': (datetime.utcnow() - start_time).total_seconds()
        }
        
        # Calculate total duration
        total_duration = (datetime.utcnow() - start_time).total_seconds()
        results['total_duration'] = total_duration
        results['status'] = 'completed'
        
        logger.info(f"Price update process completed in {total_duration:.2f} seconds")
        
        # Send success notification
        if notify:
            _send_success_notification(results)
        
    except Exception as e:
        logger.error(f"Price update process failed: {e}")
        
        results['status'] = 'failed'
        results['error'] = str(e)
        results['total_duration'] = (datetime.utcnow() - start_time).total_seconds()
        
        # Send error notification
        if notify:
            email_notifier.send_error_alert(
                'Price Update Failed',
                f"Price update process failed: {str(e)}",
                context=results
            )
        
        sys.exit(1)


def _send_success_notification(results: Dict):
    """Send success notification email"""
    try:
        subject = f"Price Update Completed - {results['price_type'].upper()} prices"
        
        message = f"""
Price Update Process Completed
=============================

Configuration:
- Price Type: {results['price_type'].upper()}
- Dry Run: {'Yes' if results['dry_run'] else 'No'}
- Duration: {results['total_duration']:.2f} seconds

Results Summary:
"""
        
        # Add step results
        for step_name, step_data in results['steps'].items():
            message += f"\n{step_name.replace('_', ' ').title()}:\n"
            message += f"- Status: {step_data['status']}\n"
            
            if step_name == 'price_calculation':
                message += f"- Products Processed: {step_data['products_calculated']}\n"
            elif step_name == 'woocommerce_import' and 'results' in step_data:
                import_results = step_data['results']
                message += f"- Total Rows: {import_results['total_rows']}\n"
                message += f"- Created: {import_results['created']}\n"
                message += f"- Updated: {import_results['updated']}\n"
                message += f"- Errors: {import_results['errors']}\n"
        
        email_notifier.send_notification(subject, message)
        
    except Exception as e:
        logger.error(f"Error sending success notification: {e}")


if __name__ == '__main__':
    main()
