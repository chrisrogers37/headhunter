from scrapers.linkedin_scraper import LinkedInScraper
import json
from datetime import datetime
from database.models import SessionLocal, Job
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Initialize the scraper
    scraper = LinkedInScraper(headless=True)
    
    # Test parameters
    search_term = "python developer"
    location = "United States"
    max_pages = 2
    max_jobs = 10
    
    logger.info(f"Starting scrape for '{search_term}' in {location}")
    logger.info(f"Max pages: {max_pages}, Max jobs: {max_jobs}")
    logger.info("-" * 50)
    
    # Run the scraper
    jobs = scraper.scrape_jobs(
        search_term=search_term,
        location=location,
        max_pages=max_pages,
        max_jobs=max_jobs
    )
    
    # Print results
    logger.info(f"\nScraped {len(jobs)} jobs")
    for job in jobs:
        logger.info(f"\nTitle: {job['title']}")
        logger.info(f"Company: {job['company']}")
        logger.info(f"Location: {job['location']}")
        logger.info(f"Posted: {job['date_posted']}")
        logger.info("-" * 50)
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jobs_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(jobs, f, indent=2)
    
    logger.info(f"\nResults saved to {filename}")
    
    # Verify database entries
    db = SessionLocal()
    try:
        db_jobs = db.query(Job).all()
        logger.info(f"\nFound {len(db_jobs)} jobs in database")
        for job in db_jobs:
            logger.info(f"\nTitle: {job.title}")
            logger.info(f"Company: {job.company}")
            logger.info(f"Location: {job.location}")
            logger.info(f"Posted: {job.date_posted}")
            logger.info("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    main() 