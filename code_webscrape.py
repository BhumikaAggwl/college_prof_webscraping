import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from datetime import datetime

class FacultyDirectoryScraper:
    def __init__(self, headless=True, timeout=15):
        """Initialize the scraper with webdriver options"""
        self.logger = self._setup_logger()
        self.timeout = timeout

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--lang=en-US")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.faculty_data = []
        self.results_per_page = 12
        self.empty_page_threshold = 3

    def _setup_logger(self):
        """Configure logging for the scraper"""
        logger = logging.getLogger('FacultyScraper')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.hasHandlers():
            logger.addHandler(handler)
        return logger

    def _wait_for_element(self, locator, timeout=None):
        """Wait for an element to be present and visible"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def navigate_to_page(self, url):
        """Navigate to the faculty directory page"""
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)

            try:
                self._wait_for_element((By.CSS_SELECTOR, ".CoveoResult, .coveo-no-results"))
                return True
            except TimeoutException:
                self.logger.warning("Timeout waiting for results to load")
                return False

        except Exception as e:
            self.logger.error(f"Error loading page: {str(e)}")
            return False

    def _parse_staff_positions(self, faculty_card):
        positions = []
        try:
            position_elements = faculty_card.select("p.staff-position")

            for pos in position_elements:
                if pos.find("br"):
                    # Positions separated by <br> tags
                    for content in pos.contents:
                        if getattr(content, 'name', None) == "br":
                            continue
                        text = content.strip() if isinstance(content, str) else content.get_text(" ", strip=True)
                        if text:
                            positions.append(text)
                elif pos.select("span"):
                    # Positions in separate <span> elements
                    positions.extend([
                        span.get_text(" ", strip=True)
                        for span in pos.select("span")
                        if span.get_text(strip=True)
                    ])
                else:
                    # Plain text position
                    text = pos.get_text(" ", strip=True)
                    if text:
                        positions.append(text)

            # Clean and filter results
            positions = [p for p in positions if p and p.lower() not in ["n/a", "null", "none", ""]]

            # Remove duplicates preserving order
            seen = set()
            return [p for p in positions if not (p in seen or seen.add(p))]

        except Exception as e:
            self.logger.warning(f"Error parsing positions: {str(e)}")
            return ["Position information not available"]

    def parse_faculty_card(self, faculty_card):
        try:
            name_element = faculty_card.select_one("div.col-12 a.CoveoResultLink")
            name = name_element.get_text(strip=True) if name_element else "N/A"
            profile_link = name_element.get('href') if name_element else "N/A"

            staff_positions = self._parse_staff_positions(faculty_card)

            email_element = faculty_card.select_one("div.col-12 a[href^='mailto:']")
            email = email_element.get_text(strip=True) if email_element else "N/A"

            keyword_elements = faculty_card.select("span.CoveoFieldValue")
            keywords = list({kw.get_text(strip=True) for kw in keyword_elements if kw.get_text(strip=True)})

            bio_element = faculty_card.select_one("p.CoveoExcerpt")
            bio = bio_element.get_text(" ", strip=True) if bio_element else "N/A"

            import_time = datetime.now().isoformat()

            self.logger.info(f"Scraped: {name} | Email: {email} | Positions: {staff_positions} | Keywords: {len(keywords)}")

            return {
                "name": name,
                "profile_link": profile_link,
                "staff_positions": staff_positions,
                "email": email,
                "keywords": keywords,
                "bio": bio,
                "import_time": import_time
            }

        except Exception as e:
            self.logger.error(f"Error parsing faculty card: {str(e)}")
            return None

    

    def go_to_next_page(self, current_url, increment=True, step=12):
        """
        Navigate to the next or previous page by modifying the 'first' value in the URL fragment.
        This is specific to UAlberta's Coveo-based search that uses #first=<offset>.
            """
        try:
            # Modify the fragment for pagination
            parsed = urlparse(current_url)
            fragment_params = parse_qs(parsed.fragment)

            # Get current start index or assume 0
            current_start = int(fragment_params.get('first', [0])[0])
            new_start = current_start + step if increment else max(0, current_start - step)

        # Update the fragment
            fragment_params['first'] = [str(new_start)]
            new_fragment = urlencode(fragment_params, doseq=True)

        # Construct the new URL with updated fragment
            next_url = urlunparse(parsed._replace(fragment=new_fragment))
            self.driver.get(next_url)

        # Wait for results to load (adapt selector as needed)
            self._wait_for_element((By.CSS_SELECTOR, ".CoveoResult, .coveo-no-results"))

            return next_url

        except Exception as e:
            self.logger.warning(f"Failed to go to next page: {str(e)}")
            return None



    def _modify_url_pagination(self, url, increment=True, times=12):
        """Modify URL query params for pagination"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # This example assumes 'start' param controls pagination offset; adapt if needed
            start = int(query_params.get('start', [0])[0])
            start = start + times if increment else max(0, start - times)
            query_params['start'] = [str(start)]

            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse(parsed._replace(query=new_query))
            return new_url
        except Exception as e:
            self.logger.warning(f"URL pagination modification failed: {str(e)}")
            return None

    def scrape_current_page(self):
        """Scrape faculty cards on the current page"""
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            faculty_cards = soup.select("div.CoveoResult")

            count = 0
            for card in faculty_cards:
                data = self.parse_faculty_card(card)
                if data:
                    self.faculty_data.append(data)
                    count += 1
            self.logger.info(f"Scraped {count} faculty cards on current page")
            return count
        except Exception as e:
            self.logger.error(f"Error scraping current page: {str(e)}")
            return 0

    def scrape_directory(self, start_url, max_pages=None, start_page=1):
        """
        Scrape the entire faculty directory through pagination

        Args:
            start_url: Base URL to start scraping from
            max_pages: Maximum number of pages to scrape (None for all pages)
            start_page: Page number to start from (for resuming scraping)
        """
        try:
            # Adjust starting position if needed
            if start_page > 1:
                start_url = self._modify_url_pagination(start_url, increment=False)
                start_url = self._modify_url_pagination(start_url, increment=True, times=(start_page-1)*self.results_per_page)

            if not self.navigate_to_page(start_url):
                self.logger.error("Failed to load the starting page")
                return

            page_count = start_page
            empty_pages = 0
            total_scraped = 0

            while True:
                self.logger.info(f"Scraping page {page_count}...")

                scraped_count = self.scrape_current_page()
                total_scraped += scraped_count

                if scraped_count == 0:
                    empty_pages += 1
                    if empty_pages >= self.empty_page_threshold:
                        self.logger.info("Reached empty page threshold - stopping")
                        break
                else:
                    empty_pages = 0

                if max_pages and page_count >= max_pages:
                    self.logger.info(f"Reached max pages limit ({max_pages})")
                    break

                if page_count % 5 == 0:
                    self.save_to_csv(f"progress_page_{page_count}.csv")

                next_url = self.go_to_next_page(self.driver.current_url)
                if not next_url:
                    self.logger.info("No more pages available")
                    break


                page_count += 1
                time.sleep(1 if page_count % 10 != 0 else 3)

            self.logger.info(f"Scraping complete. Total records: {total_scraped}")

        except Exception as e:
            self.logger.error(f"Scraping failed: {str(e)}")
            raise
        finally:
            self.save_to_csv("final_results.csv")
        return next_url

    def save_to_csv(self, filename="/Users/Lenovo/Downloads/faculty_directory.csv"):
        """Save the scraped data to a CSV file"""
        try:
            if not self.faculty_data:
                self.logger.warning("No data to save - skipping CSV write")
                return

            df = pd.DataFrame(self.faculty_data)

            for col in ['staff_positions', 'keywords']:
                if col in df.columns:
                    df[col] = df[col].apply(lambda x: '; '.join(x) if isinstance(x, list) else x)

            df.to_csv(filename, index=False, encoding='utf-8')
            self.logger.info(f"Data saved to {filename} ({len(df)} records)")

        except Exception as e:
            self.logger.error(f"Error saving to CSV: {str(e)}")


    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {str(e)}")


if __name__ == "__main__":
    try:
        base_url = (
          "https://www.ualberta.ca/en/science/about-us/contact-us/faculty-directory/index.html#first=24&sort=relevancy&f:DepartmentFacet=[Computing%20Science,Chemistry,Physics,Mathematics%20%26%20Statistical%20Sciences]&f:RoleFacet=[Staff]"
    )

        scraper = FacultyDirectoryScraper(headless=True)
        scraper.scrape_directory(base_url)
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        if 'scraper' in locals():
            if scraper.faculty_data:
                scraper.save_to_csv("final_results.csv")
            scraper.close()

