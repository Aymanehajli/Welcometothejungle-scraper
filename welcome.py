import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import sys
search_term = sys.argv[1] if len(sys.argv) > 1 else 'data analyst'



USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)…Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_5)…Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64)…Chrome/119.0.0.0 Safari/537.36",
]

# entreprise tags
WHITELIST_TAGS = ["tag","department","date","birthday","female","male"]

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


driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source":"Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
})

driver.get("https://www.welcometothejungle.com/fr")


try:
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[aria-label='Refuser']"))).click()
except:
    pass

# --- 2) Recherche  ---
search_input = wait.until(EC.presence_of_element_located(
    (By.CSS_SELECTOR,"input[data-testid='homepage-search-field-query']")
))
search_input.send_keys(search_term)
time.sleep(random.uniform(1,2))
driver.find_element(By.CSS_SELECTOR,"button[data-testid='homepage-search-button']").click()

# Attendre et compter les offres
wait.until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR,"li[data-testid='search-results-list-item-wrapper']")
))
count = len(driver.find_elements(By.CSS_SELECTOR,"li[data-testid='search-results-list-item-wrapper']"))
print(f"\n📋 {count} offres trouvées\n")

# --- 3) Première passe : extraire job info + lien d annonce ---
job_results = []
for idx in range(count): 
    offers = driver.find_elements(By.CSS_SELECTOR,"li[data-testid='search-results-list-item-wrapper']")
    offer = offers[idx]
    try:
        job_company  = offer.find_element(By.CSS_SELECTOR,"span.sc-izXThL.fFdRYJ").text.strip()
        job_title    = offer.find_element(By.CSS_SELECTOR,"h4.sc-izXThL").text.strip()
        job_location = offer.find_element(By.CSS_SELECTOR,"i[name='location'] + p span").text.strip()
        job_contract = offer.find_element(By.CSS_SELECTOR,"i[name='contract'] + span").text.strip()
        try:
            job_salary = offer.find_element(By.CSS_SELECTOR,"i[name='salary'] + span").text.strip()
        except:
            job_salary = ""
        try:
            job_remote = offer.find_element(By.CSS_SELECTOR,"i[name='remote'] + span").text.strip()
        except:
            job_remote = ""
        href = offer.find_element(By.CSS_SELECTOR,"a[href^='/fr/companies']").get_attribute("href")
        comp_link = href if href.startswith("http") else "https://www.welcometothejungle.com" + href

        job_results.append({
            "Entreprise":  job_company,
            "Nom d'annone":    job_title,
            "Localisation": job_location,
            "Type Contrat": job_contract,
            "Salaire":   job_salary,
            "Remote":   job_remote,
            "Lien d'annonce":    comp_link
        })
    except Exception as e:
        print(f" Erreur job #{idx+1}: {e}")

# --- 4) Ouvrir tous les onglets entreprises en parallèle ---
for r in job_results:
    driver.execute_script("window.open(arguments[0]);", r["Lien d'annonce"])
time.sleep(2)

# --- 5) Deuxième passe : scraper chaque onglet entreprise ---
company_infos = []
handles = driver.window_handles[1:] 
for handle in handles:
    driver.switch_to.window(handle)
    try:
        wait.until(EC.presence_of_element_located((By.ID,"the-company-section")))
        sec = driver.find_element(By.ID,"the-company-section")
        try:
            comp_name = sec.find_element(By.CSS_SELECTOR,"a.sc-hpFWgi.hulYsC span").text.strip()
        except:
            wrapper = sec.find_element(By.CSS_SELECTOR,"div.sc-brzPDJ.kfIIlx")
            anchors = wrapper.find_elements(By.TAG_NAME,"a")
            comp_name = anchors[1].find_element(By.TAG_NAME,"span").text.strip() if len(anchors)>1 else ""
        
        comp_tags = {}
        for tag in sec.find_elements(By.CSS_SELECTOR,"div.sc-brzPDJ.cJytbT div[data-testid='job-company-tag']"):
            key = tag.find_element(By.TAG_NAME,"i").get_attribute("name")
            if key in WHITELIST_TAGS:
                comp_tags[key] = tag.find_element(By.TAG_NAME,"span").text.strip()
        company_infos.append({
            "Entreprise nom":   comp_name,
            "Secteur":    comp_tags.get("tag",""),
            "Effectif":   comp_tags.get("department",""),
            "Crée en ":    comp_tags.get("date",""),
            "Age Moyen":   comp_tags.get("birthday",""),
            "Pourcentage Femmes":  comp_tags.get("female",""),
            "Pourcentage Hommes":  comp_tags.get("male","")
        })
    except Exception as e:
        print(f" Erreur entreprise onglet {handle}: {e}")
        company_infos.append({k:"" for k in ["Entreprise nom","Secteur","Effectif","Crée en ","Age Moyen","Pourcentage Femmes","Pourcentage Hommes"]})
    finally:
        driver.close()

# Revenir à l’onglet principal
driver.switch_to.window(driver.window_handles[0])
driver.quit()

# --- 6) Fusionner job + company, sauvegarder CSV ---
for job, comp in zip(job_results, company_infos):
    job.update(comp)

df = pd.DataFrame(job_results)
# remplacer éventuels NaN par "non renseigné"
df.fillna("non renseigné", inplace=True)

df.to_csv("offres_et_compagnies.csv", index=False)
print(f"\n✅ Fini ! {len(df)} lignes dans 'offres_et_compagnies.csv'")
