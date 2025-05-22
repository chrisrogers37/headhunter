from ..scrapers.stackoverflow_scraper import StackOverflowScraper
from ..database.models import StackOverflowJob, ScrapingMetrics, SessionLocal
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def view_scraping_metrics():
    """View the most recent scraping metrics from the database."""
    db = SessionLocal()
    try:
        # Get the most recent metrics
        metrics = db.query(ScrapingMetrics)\
            .order_by(ScrapingMetrics.created_at.desc())\
            .first()
            
        if metrics:
            logger.info("\nMost Recent Scraping Metrics:")
            logger.info(f"Scraper: {metrics.scraper_name}")
            logger.info(f"Start Time: {metrics.start_time}")
            logger.info(f"End Time: {metrics.end_time}")
            logger.info(f"Duration: {metrics.total_duration:.2f} seconds")
            logger.info(f"Jobs Found: {metrics.total_jobs_found}")
            logger.info(f"Jobs Scraped: {metrics.total_jobs_scraped}")
            logger.info(f"Jobs Saved: {metrics.total_jobs_saved}")
            logger.info(f"Failed Jobs: {metrics.failed_jobs}")
            logger.info(f"Success Rate: {metrics.success_rate:.1f}%")
            logger.info(f"Total Requests: {metrics.total_requests}")
            logger.info(f"Failed Requests: {metrics.failed_requests}")
            
            if metrics.errors:
                logger.info("\nErrors encountered:")
                for error in metrics.errors:
                    logger.info(f"- {error['type']}: {error['message']}")
        else:
            logger.info("No scraping metrics found in the database.")
            
    finally:
        db.close()

def view_recent_jobs():
    """View the most recently scraped jobs."""
    db = SessionLocal()
    try:
        # Get jobs from the last hour
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        jobs = db.query(StackOverflowJob)\
            .filter(StackOverflowJob.scraped_at >= one_hour_ago)\
            .order_by(StackOverflowJob.scraped_at.desc())\
            .all()
            
        if jobs:
            logger.info(f"\nFound {len(jobs)} jobs scraped in the last hour:")
            for job in jobs:
                logger.info(f"\nJob: {job.title}")
                logger.info(f"Company: {job.company}")
                logger.info(f"Location: {job.location}")
                logger.info(f"Posted: {job.date_posted}")
                logger.info(f"Scraped: {job.scraped_at}")
                logger.info(f"URL: {job.url}")
        else:
            logger.info("No jobs found in the last hour.")
            
    finally:
        db.close()

def main():
    # Initialize and run the scraper
    scraper = StackOverflowScraper(headless=False)
    jobs = scraper.scrape_jobs(
        search_term="Python Developer",
        location="New York, NY",
        max_pages=2,
        max_jobs=10
    )
    
    # View the results
    logger.info("\n=== Scraping Results ===")
    view_scraping_metrics()
    view_recent_jobs()

if __name__ == "__main__":
    main() 