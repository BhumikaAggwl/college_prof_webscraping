from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--headless=new")  # Optional: Run in headless mode
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def accept_cookies(driver):
    try:
        agree_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "OK, I agree")]'))
        )
        agree_button.click()
    except TimeoutException:
        print("No cookie popup or it already disappeared.")


def extract_faculty_links(driver, url):
    driver.get(url)
    accept_cookies(driver)

    faculty_links = []
    try:
        people_divs = driver.find_elements(By.CSS_SELECTOR, 'div.clearfix.wysiwyg.field.field--name-field-basic-text-content.field--type-text-long.field--label-hidden.field__item')
        for div in people_divs:
            try:
                link = div.find_element(By.TAG_NAME, 'a').get_attribute('href')
                name = div.text.strip().split("\n")[0]
                faculty_links.append((name, link))
            except NoSuchElementException:
                continue
    except Exception as e:
        print(f"Error extracting faculty links: {e}")

    return faculty_links


def extract_faculty_info(driver, name, link):
    driver.get(link)
    time.sleep(1)  # Ensure page loads fully

    data = {'Name': name, 'H2 Headings': [], 'Paragraphs': [], 'Research Interests': []}

    try:
        main_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.clearfix.wysiwyg.field.field--name-field-basic-text-content.field--type-text-long.field--label-hidden.field__item'))
        )
        headings = main_div.find_elements(By.TAG_NAME, 'h2')
        paragraphs = main_div.find_elements(By.TAG_NAME, 'p')

        data['H2 Headings'] = [h.text.strip() for h in headings if h.text.strip()]
        data['Paragraphs'] = [p.text.strip() for p in paragraphs if p.text.strip()]

    except TimeoutException:
        print(f"Could not find main content div for {name}")

    # Scroll to research section
    try:
        research_section = driver.find_element(By.ID, 'research-and-teaching-interests')
        driver.execute_script("arguments[0].scrollIntoView();", research_section)
        research_div = research_section.find_element(By.CSS_SELECTOR, 'div.clearfix.wysiwyg.field.field--name-body.field--type-text-with-summary.field--label-hidden.field__item')
        items = research_div.find_elements(By.TAG_NAME, 'li')
        data['Research Interests'] = [li.text.strip() for li in items if li.text.strip()]
    except NoSuchElementException:
        print(f"No research section found for {name}")

    return data


def save_to_csv(data_list, filename):
    keys = ['Name', 'H2 Headings', 'Paragraphs', 'Research Interests']
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for entry in data_list:
            writer.writerow({
                'Name': entry['Name'],
                'H2 Headings': " | ".join(entry['H2 Headings']),
                'Paragraphs': " | ".join(entry['Paragraphs']),
                'Research Interests': " | ".join(entry['Research Interests'])
            })


def main():
    url = 'https://umanitoba.ca/science/directory/statistics'
    driver = setup_driver()

    try:
        faculty_links = extract_faculty_links(driver, url)
        print(f"Found {len(faculty_links)} faculty members.")

        all_data = []
        for name, link in faculty_links:
            print(f"Scraping: {name} => {link}")
            info = extract_faculty_info(driver, name, link)
            all_data.append(info)

        save_to_csv(all_data, 'umanitoba_faculty_full.csv')
        print("✅ All data saved to umanitoba_faculty_full_math1.csv")

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
