"""
Scheduler for automated crawling using APScheduler
Runs scraping jobs at regular intervals
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from pytz import utc

from config import SCHEDULER_INTERVAL_HOURS, LOG_LEVEL, LOG_DIR, LOG_FILE_NAME
from scraper import MultiDomainScraper

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


class CrawlerScheduler:
    """Manages scheduled crawling jobs"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = BackgroundScheduler(timezone=utc)
        self.scraper = MultiDomainScraper()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Add job to run scraper at regular intervals
            self.scheduler.add_job(
                self.run_crawl,
                trigger=IntervalTrigger(hours=SCHEDULER_INTERVAL_HOURS),
                id='estate_crawler',
                name='Real Estate Web Crawler',
                replace_existing=True,
                max_instances=1,
                misfire_grace_time=3600,
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info(f"Scheduler started. Crawling interval: {SCHEDULER_INTERVAL_HOURS} hours")
            
            # Run immediately on startup
            self.run_crawl()
        
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    def run_crawl(self):
        """Execute crawling job"""
        logger.info("=" * 80)
        logger.info(f"Starting crawl at {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        try:
            results = self.scraper.scrape_all()
            
            logger.info("=" * 80)
            logger.info(f"Crawl completed at {datetime.now().isoformat()}")
            logger.info(f"Total records: {results['total_records']}")
            logger.info(f"Total added: {results['total_added']}")
            logger.info("=" * 80)
            
            # Print domain-wise results
            for domain, domain_results in results['domains'].items():
                logger.info(f"{domain}: {domain_results['added']} added, {domain_results['duplicates']} duplicates, {domain_results['duration_seconds']:.2f}s")
        
        except Exception as e:
            logger.error(f"Error during crawl: {e}", exc_info=True)
    
    def pause(self):
        """Pause the scheduler (pause all jobs)"""
        try:
            self.scheduler.pause()
            logger.info("Scheduler paused")
        except Exception as e:
            logger.error(f"Error pausing scheduler: {e}")
    
    def resume(self):
        """Resume the scheduler"""
        try:
            self.scheduler.resume()
            logger.info("Scheduler resumed")
        except Exception as e:
            logger.error(f"Error resuming scheduler: {e}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def get_status(self) -> Dict:
        """Get scheduler status"""
        jobs = self.get_jobs()
        return {
            'is_running': self.is_running,
            'next_run_time': jobs[0].next_run_time.isoformat() if jobs and jobs[0].next_run_time else None,
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in jobs
            ]
        }


# Global scheduler instance
_scheduler = None


def get_scheduler() -> CrawlerScheduler:
    """Get or create scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CrawlerScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()


if __name__ == '__main__':
    # Test scheduler
    import time
    
    scheduler = get_scheduler()
    logger.info("Starting scheduler in test mode (will run once immediately)")
    
    try:
        scheduler.start()
        
        # Keep running for demonstration
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Stopping scheduler...")
        scheduler.stop()
        logger.info("Scheduler stopped")
