# college_prof_webscraping
This is the code structure of scraping different types of website of various colleges for extracting the information of different professors for coldmailing 
Got it! Here's the complete `README.md` **content as code** (without any Python script—just paste this directly into your `README.md` file):

```markdown
# 🎓 College Faculty Web Scraper

This project is designed to scrape detailed faculty profile information from university or college department websites. It extracts information such as:

- Name  
- Designation  
- Email  
- Research Interests  
- Profile Bio  
- Section/Category (like Professors, Associate Professors, etc.)  
- Full Profile URL  

---

## 🔧 Technologies Used

- Python 3.9+
- `requests` & `BeautifulSoup` for static sites
- `Selenium` (with `webdriver-manager`) for JavaScript-heavy websites
- `re` (Regex) for parsing emails
- `pandas` for saving results to CSV

---

## 📁 Project Structure

```

college\_prof\_webscraping/
│
├── code\_uni.py              # Main scraper code (with cookie popup handler)
├── umanitoba\_faculty.csv    # Output CSV file with scraped data
├── README.md                # This file
└── ...

````

---

## 🚀 How to Use

1. **Clone the Repository:**

```bash
git clone https://github.com/BhumikaAggwl/college_prof_webscraping.git
cd college_prof_webscraping
````

2. **Install Dependencies:**

Install required Python packages:

```bash
pip install -r requirements.txt
```

3. **Run the Scraper:**

Make sure you are in the right environment and then run:

```bash
python code_uni.py
```

✅ It will:

* Automatically handle cookie popups.
* Extract faculty links from section blocks.
* Open each profile and parse details.
* Save all results into a CSV file.

---

## 🗂 Output

The scraper saves the faculty data into a CSV file:

* `umanitoba_faculty.csv`
  Each row corresponds to one faculty member.

---

## ⚠️ Notes

* For some pages like University of Manitoba, JavaScript dynamically loads the content, so we use `Selenium`.
* For static HTML pages (like SRM), we use simple `requests` + `BeautifulSoup` (no browser needed).
* Handle pop-ups like cookie consent automatically using `Selenium`.

---

## 👩‍💻 Author

**Bhumika Aggarwal**
If this project helped you, feel free to ⭐ the repo or contribute!

---



