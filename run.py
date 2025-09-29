"""
Main application runner for the Automotive Price Monitor system
"""
import os
import sys
import click
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.app import create_app
from utils.logger import setup_logger

logger = setup_logger(__name__)


@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=5000, help='Port to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--threaded', is_flag=True, default=True, help='Enable threading')
def main(host, port, debug, threaded):
    """Run the Automotive Price Monitor dashboard"""
    try:
        # Create Flask app
        app = create_app()
        
        logger.info(f"Starting Automotive Price Monitor Dashboard")
        logger.info(f"Host: {host}, Port: {port}, Debug: {debug}")
        
        # Run the application
        app.run(
            host=host,
            port=int(port),
            debug=debug,
            threaded=threaded
        )
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
