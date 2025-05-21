from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid
import json
from database.models import IndeedJob, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IndeedScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        load_dotenv()
        
    def _random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
        """Add a random delay between requests to be polite."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def _extract_job_data(self, page) -> Dict:
        """Extract job data from the current job detail page."""
        try:
            # Basic job information
            job_data = {
                "id": str(uuid.uuid4()),
                "job_id": page.url.split("/")[-1],  # Extract Indeed's job ID from URL
                "title": page.query_selector("h1.jobsearch-JobInfoHeader-title").inner_text().strip(),
                "company": page.query_selector("div[data-company-name='true']").inner_text().strip(),
                "location": page.query_selector("div[data-testid='inlineHeader-companyLocation']").inner_text().strip(),
                "description": page.query_selector("div#jobDescriptionText").inner_text().strip(),
                "url": page.url,
                "date_posted": page.query_selector("span[data-testid='myJobsStateDate']").inner_text().strip(),
                "scraped_at": datetime.utcnow()
            }
            
            # Indeed-specific fields
            try:
                job_data["salary"] = page.query_selector("div[data-testid='salary-estimate']").inner_text().strip()
            except:
                job_data["salary"] = None
                
            try:
                job_data["job_type"] = page.query_selector("div[data-testid='jobType']").inner_text().strip()
            except:
                job_data["job_type"] = None
                
            try:
                job_data["company_rating"] = page.query_selector("div[data-testid='company-rating']").inner_text().strip()
            except:
                job_data["company_rating"] = None
                
            try:
                job_data["company_reviews_count"] = page.query_selector("div[data-testid='company-reviews-count']").inner_text().strip()
            except:
                job_data["company_reviews_count"] = None
                
            try:
                job_data["company_website"] = page.query_selector("a[data-testid='company-website']").get_attribute("href")
            except:
                job_data["company_website"] = None
                
            # Extract benefits if available
            benefits = []
            try:
                benefits_elements = page.query_selector_all("div[data-testid='benefits'] li")
                benefits = [benefit.inner_text().strip() for benefit in benefits_elements]
            except:
                pass
            job_data["benefits"] = json.dumps(benefits)
            
            # Store complete raw data
            job_data["raw_data"] = json.dumps({
                "html": page.content(),
                "metadata": {
                    "scraped_at": datetime.utcnow().isoformat(),
                    "url": page.url,
                    "title": job_data["title"],
                    "company": job_data["company"]
                }
            })
            
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting job data: {str(e)}")
            return None

    def _save_job(self, job_data: Dict) -> None:
        """Save job data to the database."""
        try:
            db = SessionLocal()
            job = IndeedJob(**job_data)
            db.add(job)
            db.commit()
            logger.info(f"Saved job: {job.title} at {job.company}")
        except Exception as e:
            logger.error(f"Error saving job to database: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def _handle_captcha(self, page) -> bool:
        """Handle CAPTCHA if present."""
        try:
            # Check for common CAPTCHA indicators
            captcha_present = page.query_selector("div#captcha-challenge") or \
                            page.query_selector("div#captcha") or \
                            page.query_selector("iframe[title*='captcha']")
            
            if captcha_present:
                logger.warning("CAPTCHA detected! Please solve it manually.")
                # Wait for manual intervention
                page.wait_for_selector("div#captcha-challenge", state="hidden", timeout=120000)
                return True
            return False
        except:
            return False

    def scrape_jobs(
        self,
        search_term: str,
        location: str,
        max_pages: int = 5,
        max_jobs: Optional[int] = None
    ) -> List[Dict]:
        """
        Scrape job listings from Indeed based on search criteria.
        
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
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins',
                    '--disable-site-isolation-trials',
                ]
            )
            
            # Create a new context with specific viewport and user agent
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York coordinates
                permissions=['geolocation']
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
                'DNT': '1',
                'Cache-Control': 'max-age=0'
            })
            
            page = context.new_page()
            
            try:
                # Navigate to Indeed
                search_url = f"https://www.indeed.com/jobs?q={search_term}&l={location}"
                logger.info(f"Navigating to: {search_url}")
                
                # First visit the homepage
                page.goto("https://www.indeed.com")
                self._random_delay(3, 5)
                
                # Then navigate to search results
                page.goto(search_url)
                self._random_delay(2, 4)
                
                # Check for CAPTCHA
                if self._handle_captcha(page):
                    logger.info("CAPTCHA solved, continuing...")
                
                # Save HTML for debugging
                html_dump_path = os.path.join(os.getcwd(), "indeed_debug.html")
                with open(html_dump_path, "w", encoding="utf-8") as f:
                    f.write(page.content())
                logger.info(f"Saved page HTML to {html_dump_path}")
                
                # Wait for job cards to load
                try:
                    page.wait_for_selector("div.job_seen_beacon", timeout=15000)
                except TimeoutError:
                    # Try alternative selectors
                    selectors = [
                        "div.job_seen_beacon",
                        "div[data-testid='job-card']",
                        "div.jobsearch-ResultsList > div",
                        "div.job_seen_beacon"
                    ]
                    
                    for selector in selectors:
                        try:
                            page.wait_for_selector(selector, timeout=5000)
                            logger.info(f"Found jobs using selector: {selector}")
                            break
                        except TimeoutError:
                            continue
                
                for page_num in range(max_pages):
                    if max_jobs and len(jobs) >= max_jobs:
                        break
                        
                    # Get all job cards on the current page
                    job_cards = page.query_selector_all("div.job_seen_beacon")
                    if not job_cards:
                        job_cards = page.query_selector_all("div[data-testid='job-card']")
                    
                    logger.info(f"Found {len(job_cards)} jobs on page {page_num + 1}")
                    
                    for card in job_cards:
                        if max_jobs and len(jobs) >= max_jobs:
                            break
                            
                        try:
                            # Click the job card to load details
                            card.click()
                            self._random_delay()
                            
                            # Wait for job details to load
                            page.wait_for_selector("h1.jobsearch-JobInfoHeader-title", timeout=5000)
                            
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
                            next_button = page.query_selector("a[data-testid='pagination-page-next']")
                            if next_button and next_button.is_enabled():
                                next_button.click()
                                self._random_delay(2, 4)
                                # Wait for new page to load
                                page.wait_for_selector("div.job_seen_beacon", timeout=10000)
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
    scraper = IndeedScraper(headless=True)
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