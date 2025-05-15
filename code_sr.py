from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException
from bs4 import BeautifulSoup
import time
import csv
import re

def extract_faculty_info(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    data = {
        "Name": "",
        "Designation": "",
        "Email": "",
        "Bio": "",
        "Research Interests": ""
    }

    name_el = soup.find(['h1', 'h2'], class_='elementor-heading-title')
    if name_el:
        data["Name"] = name_el.get_text(strip=True)

    heading_tags = soup.find_all(['h2', 'h3', 'h4'])
    for tag in heading_tags:
        if 'Professor' in tag.get_text() or 'Head' in tag.get_text():
            data["Designation"] = tag.get_text(strip=True)
            break

    email_tag = soup.find('a', href=re.compile(r'mailto:', re.I))
    if email_tag:
        data["Email"] = email_tag.get_text(strip=True)
    else:
        email_fallback = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', soup.get_text())
        if email_fallback:
            data["Email"] = email_fallback.group()

    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) > 100 and not re.search(r'@|research|course', text, re.I):
            data["Bio"] = text
            break

    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if 'research interest' in heading.get_text(strip=True).lower():
            interests = []
            next_tag = heading.find_next_sibling()
            while next_tag and next_tag.name in ['ul', 'ol', 'p']:
                if next_tag.name in ['ul', 'ol']:
                    interests += [li.get_text(strip=True) for li in next_tag.find_all('li')]
                elif next_tag.name == 'p':
                    interests.append(next_tag.get_text(strip=True))
                next_tag = next_tag.find_next_sibling()
            data["Research Interests"] = "; ".join(interests)
            break

    return data

# Setup
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 15)
base_url = "https://www.srmist.edu.in/staff-finder/?dept=13540"
driver.get(base_url)

faculty_data = []

for page_num in range(3, 8):
    print(f"\n🔄 Moving to Page {page_num}...")

    try:
        # Scroll to pagination section
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination-nav")))
        time.sleep(1)

        # Find pagination button with p="x"
        pagination_items = driver.find_elements(By.CSS_SELECTOR, "div.pagination-link li")
        found = False
        for li in pagination_items:
            if li.get_attribute("p") == str(page_num):
                driver.execute_script("arguments[0].scrollIntoView();", li)
                time.sleep(0.5)
                try:
                    li.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", li)
                found = True
                break

        if not found:
            print(f"❌ Pagination button for page {page_num} not found.")
            continue

        # Wait for profiles to load
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "h3.post-title a")))
        time.sleep(2)

        # Extract profile links
        links = [a.get_attribute("href") for a in driver.find_elements(By.CSS_SELECTOR, "h3.post-title a")]
        print(f"✅ Found {len(links)} profiles on Page {page_num}")

        for idx, link in enumerate(links, 1):
            print(f"→ Scraping Profile {idx} on Page {page_num}: {link}")
            try:
                driver.execute_script("window.open('');")
                driver.switch_to.window(driver.window_handles[1])
                driver.get(link)
                time.sleep(2)

                info = extract_faculty_info(driver)
                info["Profile URL"] = link
                faculty_data.append(info)

                print(f"Name: {info['Name']}")
                print(f"Designation: {info['Designation']}")
                print(f"Email: {info['Email']}")
                print(f"Research Interests: {info['Research Interests'][:60]}...")
                print("-" * 80)
            except Exception as e:
                print(f"⚠️ Error processing profile: {e}")
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(1)

    except TimeoutException:
        print(f"❌ Timeout waiting for elements on page {page_num}")
        continue
    except Exception as e:
        print(f"❌ Unexpected error on page {page_num}: {e}")
        continue

# Save to CSV
if faculty_data:
    csv_file = "srm_faculty_profiles_page3_to_7.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=faculty_data[0].keys())
        writer.writeheader()
        writer.writerows(faculty_data)

    print(f"\n✅ All data saved to {csv_file}")

driver.quit()
