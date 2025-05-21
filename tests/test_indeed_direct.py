import logging
from scrapers.indeed_scraper import IndeedScraper

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum detail
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Initialize scraper with headless=False to see the browser
    scraper = IndeedScraper(headless=False)
    
    # Test with a simple search
    logger.info("Starting scraper test...")
    try:
        jobs = scraper.scrape_jobs(
            search_term="python developer",
            location="United States",
            max_pages=1,
            max_jobs=2
        )
        
        logger.info(f"Scraped {len(jobs)} jobs")
        for job in jobs:
            logger.info(f"\nTitle: {job['title']}")
            logger.info(f"Company: {job['company']}")
            logger.info(f"Location: {job['location']}")
            logger.info(f"Posted: {job['date_posted']}")
            logger.info("-" * 50)
            
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 