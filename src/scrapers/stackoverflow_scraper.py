from playwright.sync_api import sync_playwright, TimeoutError
import time
import random
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote_plus
import os
import sys
from bs4 import BeautifulSoup

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database.models import StackOverflowJob, SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StackOverflowScraper:
    def __init__(self, headless: bool = True):
        self.base_url = "https://stackoverflowjobs.com"
        self.headless = headless
        self.playwright = sync_playwright().start()
        self.browser = None
        self.context = None
        self.page = None

    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay between actions to appear more human-like."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _setup_browser(self):
        """Set up the browser with anti-detection measures."""
        self.browser = self.playwright.chromium.launch(
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
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York coordinates
            locale='en-US',
            timezone_id='America/New_York',
        )

        # Set additional headers
        self.context.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })

        self.page = self.context.new_page()

    def _extract_job_data(self, job_element) -> Dict:
        try:
            html = job_element.inner_html()
            soup = BeautifulSoup(html, 'html.parser')

            # Title
            title_tag = soup.find('h2', class_='chakra-text')
            title = title_tag.get_text(strip=True) if title_tag else None

            # Company
            company_tag = soup.find('p', class_='css-a2ofi8')
            company = company_tag.get_text(strip=True) if company_tag else None

            # Location
            location_tag = soup.find('p', class_='css-tbx6ua')
            location = location_tag.get_text(strip=True) if location_tag else None

            # Salary (first badge with $)
            salary_tag = None
            for badge in soup.find_all('span', class_='chakra-badge'):
                if badge and '$' in badge.get_text():
                    salary_tag = badge
                    break
            salary_range = salary_tag.get_text(strip=True) if salary_tag else None

            # Job type (badge with 'Full-time', 'Part-time', etc.)
            job_type = None
            for badge in soup.find_all('span', class_='chakra-badge'):
                if badge and any(t in badge.get_text() for t in ['Full-time', 'Part-time', 'Contract', 'Internship']):
                    job_type = badge.get_text(strip=True)
                    break

            # Date posted
            date_tag = soup.find('p', class_='css-ewn64s')
            date_posted = None
            if date_tag:
                date_text = date_tag.get_text(strip=True)
                if 'ago' in date_text:
                    try:
                        days = int([s for s in date_text.split() if s.isdigit()][0])
                        date_posted = datetime.now() - timedelta(days=days)
                    except Exception:
                        pass
                elif 'day' in date_text:
                    date_posted = datetime.now() - timedelta(days=1)

            # URL (not directly available, can be constructed from jobkey if needed)
            jobkey = job_element.get_attribute('data-jobkey')
            url = f"{self.base_url}/viewjob?jk={jobkey}" if jobkey else None

            # Tags (not visible in card, placeholder for future extraction)
            tags = []

            # Company size, industry, remote (not visible in card, placeholder for future extraction)
            company_size = None
            company_industry = None
            remote_work = None

            # Experience level (try to infer from title or badges)
            experience_level = None
            if title and any(lvl in title.lower() for lvl in ['senior', 'lead', 'staff', 'principal']):
                experience_level = title

            # Description is set in scrape_jobs, not here
            description = None

            return {
                'job_id': jobkey,
                'title': title,
                'company': company,
                'location': location,
                'description': description,
                'url': url,
                'date_posted': date_posted,
                'salary_range': salary_range,
                'job_type': job_type,
                'experience_level': experience_level,
                'tags': tags,
                'company_size': company_size,
                'company_industry': company_industry,
                'remote_work': remote_work,
                'raw_data': soup.prettify(),
            }
        except Exception as e:
            logger.error(f"Error extracting job data: {str(e)}")
            return None

    def _save_to_database(self, job_data: Dict):
        """Save job data to the database."""
        try:
            db = SessionLocal()
            job = StackOverflowJob(**job_data)
            db.add(job)
            db.commit()
            logger.info(f"Saved job: {job.title} at {job.company}")
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def scrape_jobs(self, search_term: str, location: str, max_pages: int = 5, max_jobs: int = 100) -> List[Dict]:
        """
        Scrape jobs from Stack Overflow Jobs.
        
        Args:
            search_term (str): Job title or keywords to search for
            location (str): Location to search in
            max_pages (int): Maximum number of pages to scrape
            max_jobs (int): Maximum number of jobs to scrape
            
        Returns:
            List[Dict]: List of scraped job data
        """
        try:
            self._setup_browser()
            jobs = []
            page_num = 1

            search_url = f"{self.base_url}/?q={quote_plus(search_term)}&l={quote_plus(location)}"
            logger.info(f"Navigating to: {search_url}")
            self.page.goto(search_url)
            self._random_delay()

            # Wait for job list and at least one job card
            try:
                self.page.wait_for_selector('#job-list > li > div[data-jobkey]', timeout=15000)
                logger.info('Job list loaded.')
            except Exception as e:
                logger.warning(f'Job list did not load in time: {e}')

            # Save HTML snapshot before scraping
            html_snapshot = self.page.content()
            with open("stackoverflow_jobs_snapshot.html", "w") as f:
                f.write(html_snapshot)
            logger.info("Saved HTML snapshot as stackoverflow_jobs_snapshot.html")

            while page_num <= max_pages and len(jobs) < max_jobs:
                logger.info(f"Scraping page {page_num}")
                # Get the number of job cards on the page
                num_cards = len(self.page.query_selector_all('#job-list > li > div[data-jobkey]'))
                if num_cards == 0:
                    html = self.page.content()
                    with open(f"stackoverflow_debug_{int(time.time())}.html", "w") as f:
                        f.write(html)
                    logger.warning("No job cards found! Saved HTML for debugging.")
                    break
                logger.info(f"Found {num_cards} jobs on page {page_num}")
                for idx in range(num_cards):
                    if len(jobs) >= max_jobs:
                        break
                    card_selector = f'#job-list > li:nth-child({idx+1}) > div[data-jobkey]'
                    description = None
                    for attempt in range(3):
                        try:
                            # Scroll into view using JavaScript
                            self.page.eval_on_selector(card_selector, 'el => el.scrollIntoView({behavior: "instant", block: "center"})')
                            # Click the job card
                            self.page.click(card_selector, timeout=5000)
                            self._random_delay(1, 2)
                            # Wait for right pane to update
                            self.page.wait_for_selector('#right-pane-content .css-11gcbyb', timeout=7000)
                            desc_elem = self.page.query_selector('#right-pane-content .css-11gcbyb')
                            description = desc_elem.inner_text() if desc_elem else None
                            break  # Success
                        except Exception as e:
                            logger.warning(f"Attempt {attempt+1}: Could not extract description for job {idx+1}: {e}")
                            self._random_delay(0.5, 1.0)
                    # Extract other fields from the card as before
                    card = self.page.query_selector(card_selector)
                    job_data = self._extract_job_data(card) if card else None
                    if job_data:
                        job_data['description'] = description
                        jobs.append(job_data)
                        self._save_to_database(job_data)
                        self._random_delay(0.5, 1.5)
                # Next page logic
                next_button = self.page.query_selector('a[aria-label="Next page"]')
                if not next_button:
                    logger.info("No more pages available")
                    break
                next_button.click()
                self._random_delay(2, 4)
                page_num += 1
            logger.info(f"Scraped {len(jobs)} jobs in total")
            return jobs
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            return jobs if 'jobs' in locals() else []
        finally:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

if __name__ == "__main__":
    # Example usage
    scraper = StackOverflowScraper(headless=False)
    jobs = scraper.scrape_jobs(
        search_term="Data Scientist",
        location="New York, NY",
        max_pages=2,
        max_jobs=10
    )
    print(f"Scraped {len(jobs)} jobs") 