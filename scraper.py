#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Selenium avancé pour la recherche d'emploi avec gestion améliorée des anti-bots
"""
import time
import random
import logging
import argparse
import sys
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (WebDriverException, 
                                      NoSuchElementException,
                                      TimeoutException)

# ----------------- CONFIGURATION ----------------- #
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

# Comportement humain
DELAY_CONFIG = {
    'typing': (0.08, 0.25),  # min/max delay entre caractères
    'action': (0.5, 2.5),     # délais entre actions
    'scroll': (0.3, 1.2),     # délais entre scrolls
    'read': (3.0, 8.0)        # pause lecture longue
}

SCROLL_CONFIG = {
    'steps': (5, 15),         # nombre de scroll steps
    'jitter': 0.3             # variation de scroll
}

# Configuration des sites
@dataclass
class SiteConfig:
    name: str
    url: str
    input_selectors: List[str]
    button_selectors: List[str]
    result_selectors: List[str]
    captcha_selectors: List[str] = None

SITES = {
    'monster': SiteConfig(
        name="Monster.fr",
        url="https://www.monster.fr/",
        input_selectors=[
            "input[placeholder*='Mots clés']",
            "input[placeholder*='Rechercher']",
            "input#search-input",
            "input[name='q']"
        ],
        button_selectors=[
            "button[data-testid='searchbar-submit-button-desktop']",
            "button[aria-label='Rechercher']",
            "button#searchButton", 
            "button[type='submit']"
        ],
        result_selectors=[
            "section.card-content",
            "div.card-content", 
            "div.job-card",
            "article.job-card"
        ],
        captcha_selectors=[
            "iframe[src*='captcha']",
            "div#captcha-container",
            "div.recaptcha"
        ]
    ),
    'indeed': SiteConfig(
        name="Indeed.fr",
        url="https://fr.indeed.com/",
        input_selectors=[
            "input[name='q']",
            "input#text-input-what"
        ],
        button_selectors=[
            "button[type='submit']",
            "button#jobsearch"
        ],
        result_selectors=[
            "div.job_seen_beacon",
            "div.jobCard"
        ]
    )
}

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("job_search.log")
    ]
)
logger = logging.getLogger(__name__)

# ----------------- UTILITAIRES ----------------- #
def random_delay(delay_type: str) -> None:
    """Pause aléatoire selon le type d'action."""
    min_d, max_d = DELAY_CONFIG[delay_type]
    time.sleep(random.uniform(min_d, max_d))

def human_typing(element, text: str) -> None:
    """Saisie humaine avec variations."""
    for char in text:
        element.send_keys(char)
        random_delay('typing')
        # 5% de chance de faire une erreur de frappe
        if random.random() < 0.05:
            element.send_keys(random.choice(['a', 'e', 'z']))
            random_delay('typing')
            element.send_keys(Keys.BACKSPACE)

def human_scroll(driver, scroll_distance: Optional[int] = None) -> None:
    """Défilement humain avec variations."""
    if not scroll_distance:
        scroll_distance = random.randint(*SCROLL_CONFIG['steps'])
    
    viewport_height = driver.execute_script("return window.innerHeight")
    jitter = int(viewport_height * SCROLL_CONFIG['jitter'])
    
    for _ in range(scroll_distance):
        # Scroll avec variation aléatoire
        scroll_step = random.randint(
            viewport_height - jitter, 
            viewport_height + jitter
        )
        driver.execute_script(f"window.scrollBy(0, {scroll_step});")
        random_delay('scroll')
        
        # 20% de chance de faire un petit scroll up
        if random.random() < 0.2:
            driver.execute_script(f"window.scrollBy(0, -{scroll_step//3});")
            random_delay('scroll')

def random_mouse_movement(driver, element=None) -> None:
    """Mouvements de souris aléatoires."""
    actions = ActionChains(driver)
    
    # Déplacement vers l'élément si spécifié
    if element:
        actions.move_to_element(element)
        random_delay('action')
    
    # Mouvements aléatoires
    for _ in range(random.randint(2, 5)):
        x_offset = random.randint(-50, 50)
        y_offset = random.randint(-50, 50)
        actions.move_by_offset(x_offset, y_offset)
        actions.pause(random.uniform(0.1, 0.5))
    
    actions.perform()

# ----------------- CORE ----------------- #
class JobScraper:
    def __init__(self, headless: bool = False):
        self.driver = self._init_driver(headless)
        self.wait = WebDriverWait(self.driver, 20)
    
    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        """Initialise le driver Chrome avec paramètres anti-détection."""
        options = Options()
        
        # Paramètres de base
        options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Mode fenêtré aléatoire
        if not headless:
            width = random.randint(1000, 1600)
            height = random.randint(700, 900)
            options.add_argument(f"--window-size={width},{height}")
        else:
            options.add_argument("--headless=new")
        
        # Masquage WebDriver
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        driver = webdriver.Chrome(options=options)
        
        # Scripts anti-détection
        stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(window, 'chrome', {get: () => undefined});
            window.navigator.chrome = undefined;
        """
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": stealth_script
        })
        
        return driver
    
    def solve_captcha(self) -> bool:
        """Tente de détecter et résoudre un captcha."""
        if not self.site_config.captcha_selectors:
            return False
            
        for selector in self.site_config.captcha_selectors:
            try:
                captcha = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if captcha.is_displayed():
                    logger.warning("Captcha détecté! Résolution manuelle requise.")
                    input("Appuyez sur Entrée après avoir résolu le captcha...")
                    return True
            except (NoSuchElementException, TimeoutException):
                continue
        return False
    
    def search(self, site: str, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Exécute une recherche sur le site spécifié."""
        self.site_config = SITES[site]
        results = []
        
        try:
            # Étape 1: Chargement initial
            self.driver.get(self.site_config.url)
            random_delay('action')
            human_scroll(self.driver)
            
            # Étape 2: Saisie de la recherche
            input_selector = self._find_first_visible(self.site_config.input_selectors)
            search_input = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, input_selector))
            )
            
            random_mouse_movement(self.driver, search_input)
            human_typing(search_input, keyword)
            random_delay('action')
            
            # Étape 3: Soumission
            button_selector = self._find_first_visible(self.site_config.button_selectors)
            search_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
                
            random_mouse_movement(self.driver, search_button)
            search_button.click()
            random_delay('action')
            
            # Étape 4: Gestion captcha
            if self.solve_captcha():
                random_delay('read')  # Pause après captcha
            
            # Étape 5: Collecte des résultats
            human_scroll(self.driver, scroll_distance=max_results//2)
            
            result_selector = self._find_first_visible(self.site_config.result_selectors)
            job_cards = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, result_selector))
            )[:max_results]
            
            for card in job_cards:
                try:
                    # Faire défiler jusqu'à la carte
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                        card
                    )
                    random_delay('action')
                    
                    # Extraction des données
                    result = {
                        'title': self._extract_text(card, ["h2", ".title", ".job-title"]),
                        'company': self._extract_text(card, [".company", ".employer"]),
                        'location': self._extract_text(card, [".location", ".job-loc"]),
                        'url': self._extract_link(card)
                    }
                    
                    if all(result.values()):  # Ne garder que les résultats complets
                        results.append(result)
                        logger.info(f"Trouvé: {result['title']}")
                    
                    # Pause occasionnelle plus longue
                    if random.random() < 0.2:
                        random_delay('read')
                        
                except Exception as e:
                    logger.warning(f"Erreur extraction carte: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur recherche: {str(e)}")
            self.driver.save_screenshot("error.png")
            logger.info("Capture d'écran sauvegardée (error.png)")
            
        return results
    
    def _find_first_visible(self, selectors: List[str]) -> str:
        """Trouve le premier sélecteur visible."""
        for selector in selectors:
            try:
                if self.driver.find_element(By.CSS_SELECTOR, selector).is_displayed():
                    return selector
            except NoSuchElementException:
                continue
        raise NoSuchElementException(f"Aucun sélecteur visible parmi: {selectors}")
    
    def _extract_text(self, element, selectors: List[str]) -> str:
        """Extrait le texte du premier sélecteur trouvé."""
        for selector in selectors:
            try:
                return element.find_element(By.CSS_SELECTOR, selector).text.strip()
            except NoSuchElementException:
                continue
        return ""
    
    def _extract_link(self, element) -> str:
        """Extrait le lien href en nettoyant les paramètres."""
        try:
            url = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            return urlparse(url)._replace(query="").geturl()
        except NoSuchElementException:
            return ""
    
    def close(self):
        """Ferme proprement le driver."""
        try:
            self.driver.quit()
        except Exception:
            pass

# ----------------- MAIN ----------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Recherche automatisée d'offres d'emploi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        'keyword', 
        nargs='?',
        help="Mot-clé à rechercher"
    )
    parser.add_argument(
        '-s', '--site',
        choices=SITES.keys(),
        default='monster',
        help="Site cible pour la recherche"
    )
    parser.add_argument(
        '-n', '--max-results',
        type=int,
        default=15,
        help="Nombre maximum de résultats à extraire"
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help="Exécuter en mode headless"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help="Activer le mode debug"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Saisie interactive si mot-clé manquant
    if not args.keyword:
        try:
            args.keyword = input("Mot-clé à rechercher : ").strip()
            if not args.keyword:
                raise ValueError("Mot-clé requis")
        except (EOFError, KeyboardInterrupt):
            logger.error("Interruption utilisateur")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Erreur saisie: {str(e)}")
            sys.exit(1)
    
    # Exécution de la recherche
    scraper = JobScraper(headless=args.headless)
    try:
        logger.info(f"Recherche '{args.keyword}' sur {SITES[args.site].name}...")
        results = scraper.search(args.site, args.keyword, args.max_results)
        
        # Affichage des résultats
        print(f"\n🔍 {len(results)} résultats trouvés:")
        for i, res in enumerate(results, 1):
            print(f"\n{i}. {res['title']}")
            print(f"   🏢 {res['company']}")
            print(f"   📍 {res['location']}")
            print(f"   🔗 {res['url']}")
        
    finally:
        scraper.close()

if __name__ == '__main__':
    main()