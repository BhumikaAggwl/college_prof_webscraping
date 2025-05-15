from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import time
import csv
import os

# Setup Chrome options
options = Options()
# options.add_argument('--headless')  # Uncomment for headless mode
options.add_argument('--start-maximized')

# Path to ChromeDriver (update this to your system's path)
from webdriver_manager.chrome import ChromeDriverManager
driver_path = ChromeDriverManager().install()

driver = webdriver.Chrome(service=Service(driver_path), options=options)

url = "https://stage.vit.ac.in/school/allfaculty/sas/mathematics"
driver.get(url)
wait = WebDriverWait(driver, 30)

# Function to check if the document is ready
def is_document_ready(driver):
    return driver.execute_script("return document.readyState === 'complete';")

# Wait for the document to be ready
try:
    wait.until(is_document_ready)
except TimeoutException:
    print("Error: Document did not become ready in time. Exiting...")
    driver.quit()
    exit()

# Scroll to ensure all faculty cards load
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

faculty_data = []

# Initial wait to load all cards
try:
    wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "view-more-button"))) # changed to element_to_be_clickable
except TimeoutException:
    print("Error: view-more-button elements not found or not clickable after waiting. Exiting...")
    driver.quit()
    exit()

total_cards = len(driver.find_elements(By.CLASS_NAME, "view-more-button"))
print(f"Found {total_cards} faculty cards.")

for index in range(total_cards):
    try:
        # Re-locate the view more buttons each iteration to avoid stale reference
        buttons = driver.find_elements(By.CLASS_NAME, "view-more-button")
        wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "view-more-button")))
        driver.execute_script("arguments[0].click();", buttons[index])
        time.sleep(2)

        # Wait for modal to appear
        lightbox = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "lightbox_course")))

        # Scroll within the modal
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", lightbox)
        time.sleep(2)  # Add a short delay to allow content to load

        soup = BeautifulSoup(lightbox.get_attribute('innerHTML'), 'html.parser')

        # Extract information
        resume_section = soup.find('div', class_='resume-section-content')
        if resume_section:
            primary_text = resume_section.find('div', class_='text-primary').text.strip() if resume_section.find('div', class_='text-primary') else "Not Found"
            subheading_text = resume_section.find('div', class_='subheading mb-5').text.strip() if resume_section.find('div', class_='subheading mb-5') else "Not Found"
        else:
            primary_text = "Not Found"
            subheading_text = "Not Found"

        research_interest_section = soup.find('div', class_='resume-section-content table-responsive-sm')
        if research_interest_section:
            ul_element = research_interest_section.find('ul', class_='fa-ul mb-0')
            if ul_element:
                research_interests = [li.text.strip() for li in ul_element.find_all('li')]
            else:
                research_interests = ["Not Found"]
        else:
            research_interests = ["Not Found"]

        # Store the data
        faculty_data.append({
            "Name": primary_text,
            "Designation": subheading_text,
            "Research Interests": research_interests,
        })

        print(f"\nFaculty #{index+1}")
        print(f"Name: {primary_text}")
        print(f"Designation: {subheading_text}")
        print(f"Research Interests: {research_interests}")

        # Close the modal
        close_button = driver.find_element(By.CLASS_NAME, "fancybox-close-small")
        close_button.click()
        time.sleep(1)

    except Exception as e:
        print(f"⚠️ Error on faculty #{index+1}: {e}")
        continue

# Save results to CSV
csv_filename = "vit_mathematics_faculty.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=faculty_data[0].keys())
    writer.writeheader()
    writer.writerows(faculty_data)

print(f"\n✅ Data saved to {csv_filename}")

driver.quit()
