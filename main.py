"""
Main Entry Point for Estate Crawler
Provides CLI interface for running scraper, scheduler, export, and tests
"""

import sys
import logging
import argparse
from pathlib import Path

from config import LOG_DIR, LOG_FILE_NAME, LOG_LEVEL
from database import EstateDatabase
from scraper import MultiDomainScraper
from scheduler import CrawlerScheduler
from data_export import DataExporter

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{LOG_DIR}/{LOG_FILE_NAME}'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def init_command(args):
    """Initialize database"""
    logger.info("Initializing database...")
    db = EstateDatabase()
    logger.info("Database initialized successfully")
    logger.info(f"Database path: {db.db_path}")


def scrape_command(args):
    """Run scraper once"""
    logger.info("Starting single scrape operation...")
    scraper = MultiDomainScraper()
    results = scraper.scrape_all()
    
    print("\n" + "=" * 80)
    print("SCRAPE RESULTS")
    print("=" * 80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total records found: {results['total_records']}")
    print(f"Total records added: {results['total_added']}")
    print()
    
    for domain, domain_results in results['domains'].items():
        print(f"{domain:30} | Added: {domain_results['added']:4} | Duplicates: {domain_results['duplicates']:4} | Time: {domain_results['duration_seconds']:6.2f}s")
    
    print("=" * 80 + "\n")
    
    if args.export:
        logger.info("Exporting data...")
        exporter = DataExporter()
        export_results = exporter.export_all_formats()
        print("Export Results:")
        for format_type, filepath in export_results.items():
            if filepath:
                print(f"  ✓ {format_type}: {filepath}")
            else:
                print(f"  ✗ {format_type}: Failed")


def scheduler_command(args):
    """Start scheduler for automated runs"""
    logger.info("Starting scheduler...")
    scheduler = CrawlerScheduler()
    
    try:
        scheduler.start()
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            import time
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop()
        logger.info("Scheduler stopped")
        sys.exit(0)


def export_command(args):
    """Export data to various formats"""
    logger.info("Starting data export...")
    
    exporter = DataExporter()
    
    if args.format == 'all':
        results = exporter.export_all_formats()
    elif args.format == 'csv':
        results = {'csv': exporter.export_to_csv()}
    elif args.format == 'json':
        results = {'json': exporter.export_to_json()}
    elif args.format == 'parquet':
        results = {'parquet': exporter.export_to_parquet()}
    elif args.format == 'ml':
        results = {'ml_dataset': exporter.export_ml_dataset()}
    elif args.format == 'stats':
        results = {'statistics': exporter.export_statistics()}
    else:
        logger.error(f"Unknown format: {args.format}")
        return
    
    print("\n" + "=" * 80)
    print("EXPORT RESULTS")
    print("=" * 80)
    for format_type, filepath in results.items():
        if filepath:
            print(f"✓ {format_type:15}: {filepath}")
        else:
            print(f"✗ {format_type:15}: Failed or not available")
    print("=" * 80 + "\n")


def stats_command(args):
    """Show database statistics"""
    db = EstateDatabase()
    stats = db.get_stats()
    
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    print(f"Total Properties:     {stats.get('total_properties', 0):,}")
    print(f"Unique Provinces:     {stats.get('unique_provinces', 0)}")
    print(f"Unique Domains:       {stats.get('unique_domains', 0)}")
    print(f"Average Price (VND):  {stats.get('avg_price_vnd', 0):,.0f}")
    print(f"Average Area (m²):    {stats.get('avg_area_sqm', 0):.2f}")
    print(f"Average Bedrooms:     {stats.get('avg_bedrooms', 0):.1f}")
    print("=" * 80 + "\n")


def test_command(args):
    """Run unit tests"""
    logger.info("Running unit tests...")
    
    try:
        import unittest
        from test_scraper import run_tests
        
        success = run_tests()
        
        if success:
            logger.info("All tests passed!")
            sys.exit(0)
        else:
            logger.error("Some tests failed!")
            sys.exit(1)
    
    except ImportError as e:
        logger.error(f"Could not import test module: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Vietnam Real Estate Web Crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s init                    # Initialize database
  %(prog)s scrape                  # Run scraper once
  %(prog)s scrape --export         # Scrape and export data
  %(prog)s scheduler               # Start automated scheduler
  %(prog)s export --format all     # Export all formats
  %(prog)s stats                   # Show database statistics
  %(prog)s test                    # Run unit tests
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Run web scraper once')
    scrape_parser.add_argument('--export', action='store_true', help='Export data after scraping')
    
    # Scheduler command
    subparsers.add_parser('scheduler', help='Start automated scheduler')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export collected data')
    export_parser.add_argument(
        '--format',
        choices=['csv', 'json', 'parquet', 'ml', 'stats', 'all'],
        default='all',
        help='Export format (default: all)'
    )
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Test command
    subparsers.add_parser('test', help='Run unit tests')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'init':
        init_command(args)
    elif args.command == 'scrape':
        scrape_command(args)
    elif args.command == 'scheduler':
        scheduler_command(args)
    elif args.command == 'export':
        export_command(args)
    elif args.command == 'stats':
        stats_command(args)
    elif args.command == 'test':
        test_command(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
