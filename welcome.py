import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager
import sys

# --- Parameters & constants ---
search_term = sys.argv[1] if len(sys.argv) > 1 else 'data analyst'
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)…Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_5)…Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64)…Chrome/119.0.0.0 Safari/537.36",
]
WHITELIST_TAGS = ["tag", "department", "date", "birthday", "female", "male"]

# --- 1) Setup Selenium ---
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 10)
actions = ActionChains(driver)

# Hide webdriver flag
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
})

# --- 2) Go to site & close cookies popup if present ---
driver.get("https://www.welcometothejungle.com/fr")
try:
    wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[aria-label='Refuser']"))
    ).click()
except:
    pass

# --- 3) Perform search ---
search_input = wait.until(EC.presence_of_element_located(
    (By.CSS_SELECTOR, "input[data-testid='homepage-search-field-query']")
))
search_input.send_keys(search_term)
time.sleep(random.uniform(1, 2))
driver.find_element(
    By.CSS_SELECTOR, "button[data-testid='homepage-search-button']"
).click()

# --- 4) Read total number of jobs ---
total_jobs_elem = wait.until(EC.presence_of_element_located((
    By.CSS_SELECTOR, 'div[data-testid="jobs-search-results-count"]'
)))
count_text = total_jobs_elem.text.replace("\u202f", "").replace(",", "")
total_jobs = int(count_text)
print(f"Total jobs to scrape: {total_jobs}")

job_results = []
company_infos = []

def click_next_page():
    """
    Finds and clicks the enabled “Next” arrow by:
    1) selecting the <svg alt='Right'> inside a[aria-disabled='false'],
    2) climbing up to its parent <a>,
    3) clicking (JS fallback if needed).
    Returns False if no such button exists or it's disabled.
    """
    try:
        # 1) Ensure pagination nav is present
        pagination = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "nav[aria-label='Pagination']"
        )))

        # 2) Grab the SVG inside an enabled arrow
        svg = pagination.find_element(
            By.CSS_SELECTOR,
            "a[aria-disabled='false'] svg[alt='Right']"
        )
        # 3) Parent <a>
        next_btn = svg.find_element(By.XPATH, "..")

        # 4) Scroll into view
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", next_btn)
        time.sleep(0.2)

        # 5) Click normally, else JS click fallback
        try:
            next_btn.click()
        except (ElementClickInterceptedException,
                TimeoutException,
                StaleElementReferenceException):
            driver.execute_script("arguments[0].click();", next_btn)

        return True

    except (NoSuchElementException, TimeoutException) as e:
        print(f"→ No next-page button found or click failed: {e}")
        return False

# --- 5) Pagination + scraping loop ---
while True:
    # 5.1) Wait for and collect all offers on current page
    wait.until(EC.presence_of_all_elements_located((
        By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"
    )))
    offers = driver.find_elements(
        By.CSS_SELECTOR, "li[data-testid='search-results-list-item-wrapper']"
    )
    print(f"\nFound {len(offers)} offers on this page.")

    # 5.2) Extract job info and company URL
    for offer in offers:
        try:
            job_company  = offer.find_element(
                By.CSS_SELECTOR, "span.sc-izXThL.fFdRYJ"
            ).text.strip()
            job_title    = offer.find_element(
                By.CSS_SELECTOR, "h4.sc-izXThL"
            ).text.strip()
            job_location = offer.find_element(
                By.CSS_SELECTOR, "i[name='location'] + p span"
            ).text.strip()
            job_contract = offer.find_element(
                By.CSS_SELECTOR, "i[name='contract'] + span"
            ).text.strip()
            job_salary   = offer.find_element(
                By.CSS_SELECTOR, "i[name='salary'] + span"
            ).text.strip() if offer.find_elements(
                By.CSS_SELECTOR, "i[name='salary'] + span"
            ) else ""
            job_remote   = offer.find_element(
                By.CSS_SELECTOR, "i[name='remote'] + span"
            ).text.strip() if offer.find_elements(
                By.CSS_SELECTOR, "i[name='remote'] + span"
            ) else ""
            href         = offer.find_element(
                By.CSS_SELECTOR, "a[href^='/fr/companies']"
            ).get_attribute("href")
            comp_link    = href if href.startswith("http") else \
                           "https://www.welcometothejungle.com" + href

            job_results.append({
                "Entreprise":      job_company,
                "Nom d'annonce":   job_title,
                "Localisation":    job_location,
                "Type Contrat":    job_contract,
                "Salaire":         job_salary,
                "Remote":          job_remote,
                "Lien d'annonce":  comp_link
            })
        except Exception as e:
            print(f"  • Error extracting job info: {e}")

    # 5.3) Open each company tab for the newly scraped offers
    start_idx = len(job_results) - len(offers)
    for job in job_results[start_idx:]:
        driver.execute_script("window.open(arguments[0]);", job["Lien d'annonce"])
    time.sleep(1)

    # 5.4) Scrape each company tab then close it
    for handle in driver.window_handles[1:]:
        driver.switch_to.window(handle)
        try:
            wait.until(EC.presence_of_element_located((By.ID, "the-company-section")))
            sec = driver.find_element(By.ID, "the-company-section")

            # Company name
            try:
                comp_name = sec.find_element(
                    By.CSS_SELECTOR, "a.sc-hpFWgi.hulYsC span"
                ).text.strip()
            except:
                wrapper = sec.find_element(By.CSS_SELECTOR, "div.sc-brzPDJ.kfIIlx")
                anchors = wrapper.find_elements(By.TAG_NAME, "a")
                comp_name = anchors[1].find_element(
                    By.TAG_NAME, "span"
                ).text.strip() if len(anchors) > 1 else ""

            # Tags
            comp_tags = {}
            for tag in sec.find_elements(
                By.CSS_SELECTOR, "div.sc-brzPDJ.cJytbT div[data-testid='job-company-tag']"
            ):
                key = tag.find_element(By.TAG_NAME, "i").get_attribute("name")
                if key in WHITELIST_TAGS:
                    comp_tags[key] = tag.find_element(By.TAG_NAME, "span").text.strip()

            company_infos.append({
                "Entreprise nom":      comp_name,
                "Secteur":             comp_tags.get("tag", ""),
                "Effectif":            comp_tags.get("department", ""),
                "Crée en":             comp_tags.get("date", ""),
                "Age Moyen":           comp_tags.get("birthday", ""),
                "Pourcentage Femmes":  comp_tags.get("female", ""),
                "Pourcentage Hommes":  comp_tags.get("male", "")
            })

        except Exception as e:
            print(f"  • Error scraping company tab: {e}")
            company_infos.append({
                "Entreprise nom":      "",
                "Secteur":             "",
                "Effectif":            "",
                "Crée en":             "",
                "Age Moyen":           "",
                "Pourcentage Femmes":  "",
                "Pourcentage Hommes":  ""
            })
        finally:
            driver.close()

    # 5.5) Return to the main (results) tab
    driver.switch_to.window(driver.window_handles[0])

    # 5.6) Check if we have all jobs
    # if len(job_results) >= total_jobs:
    if len(job_results) >= 70:          #limite dans 70 pour le test
        print("✔ Reached total_jobs — stopping pagination.")
        break

    # 5.7) Click the “next page” arrow
    if not click_next_page():
        break

    # 5.8) Human-like wait for content to load
    time.sleep(random.uniform(1, 2))

# --- 6) Merge results & save CSV ---
for job, comp in zip(job_results, company_infos):
    job.update(comp)

df = pd.DataFrame(job_results).fillna("non renseigné")
df.to_csv("offres_et_compagnies.csv", index=False)
print(f"\n✅ Fini ! {len(df)} lignes dans 'offres_et_compagnies.csv' — results page remains open.")
