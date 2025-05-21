from playwright.sync_api import sync_playwright
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
from database.models import Job, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        load_dotenv()
        
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Add a random delay between requests to be polite."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def _extract_job_data(self, page) -> Dict:
        """Extract job data from the current job detail page."""
        try:
            return {
                "id": str(uuid.uuid4()),
                "title": page.query_selector(".job-details-jobs-unified-top-card__job-title").inner_text().strip(),
                "company": page.query_selector(".job-details-jobs-unified-top-card__company-name").inner_text().strip(),
                "location": page.query_selector(".job-details-jobs-unified-top-card__bullet").inner_text().strip(),
                "date_posted": page.query_selector(".job-details-jobs-unified-top-card__posted-date").inner_text().strip(),
                "description": page.query_selector(".job-details-jobs-unified-top-card__job-description").inner_text().strip(),
                "url": page.url,
                "scraped_at": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Error extracting job data: {str(e)}")
            return None

    def _save_job(self, job_data: Dict) -> None:
        """Save job data to the database."""
        try:
            db = SessionLocal()
            job = Job(**job_data)
            db.add(job)
            db.commit()
            logger.info(f"Saved job: {job.title} at {job.company}")
        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def scrape_jobs(
        self,
        search_term: str,
        location: str,
        max_pages: int = 5,
        max_jobs: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape job listings from LinkedIn based on search criteria.
        
        Args:
            search_term: Job title or keywords to search for
            location: Location to search in
            max_pages: Maximum number of pages to scrape
            max_jobs: Maximum number of jobs to scrape (None for no limit)
            
        Returns:
            List of dictionaries containing job data
        """
        jobs = []
        
        with sync_playwright() as p:
            # Launch browser with additional configurations
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            # Create a new context with specific viewport and user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            # Add additional headers
            context.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'DNT': '1'
            })
            
            page = context.new_page()
            
            try:
                # Navigate to LinkedIn Jobs
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={search_term}&location={location}"
                logger.info(f"Navigating to: {search_url}")
                page.goto(search_url)
                self._random_delay(2, 4)
                
                # Wait for job cards to load
                page.wait_for_selector(".job-card-container", timeout=10000)
                
                for page_num in range(max_pages):
                    if max_jobs and len(jobs) >= max_jobs:
                        break
                        
                    # Get all job cards on the current page
                    job_cards = page.query_selector_all(".job-card-container")
                    logger.info(f"Found {len(job_cards)} jobs on page {page_num + 1}")
                    
                    for card in job_cards:
                        if max_jobs and len(jobs) >= max_jobs:
                            break
                            
                        try:
                            # Click the job card to load details
                            card.click()
                            self._random_delay()
                            
                            # Wait for job details to load
                            page.wait_for_selector(".job-details-jobs-unified-top-card__job-title", timeout=5000)
                            
                            # Extract job data
                            job_data = self._extract_job_data(page)
                            if job_data:
                                jobs.append(job_data)
                                self._save_job(job_data)
                                logger.info(f"Scraped job: {job_data['title']} at {job_data['company']}")
                            
                        except Exception as e:
                            logger.error(f"Error processing job card: {str(e)}")
                            continue
                    
                    # Click next page if not on last page
                    if page_num < max_pages - 1:
                        try:
                            next_button = page.query_selector(".artdeco-pagination__button--next")
                            if next_button and next_button.is_enabled():
                                next_button.click()
                                self._random_delay(2, 4)
                                # Wait for new page to load
                                page.wait_for_selector(".job-card-container", timeout=10000)
                            else:
                                logger.info("No more pages available")
                                break
                        except Exception as e:
                            logger.error(f"Error navigating to next page: {str(e)}")
                            break
                
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
            
            finally:
                browser.close()
                
        return jobs

if __name__ == "__main__":
    # Example usage
    scraper = LinkedInScraper(headless=True)
    jobs = scraper.scrape_jobs(
        search_term="python developer",
        location="United States",
        max_pages=2,
        max_jobs=10
    )
    
    print(f"Scraped {len(jobs)} jobs")
    for job in jobs:
        print(f"\nTitle: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Posted: {job['date_posted']}")
        print("-" * 50) 