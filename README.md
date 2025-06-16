# Welcome to the Jungle Job Scraper & Web App

Une application Python/Flask qui :

1. Scrape les offres d’emploi et données d’entreprises depuis Welcome to the Jungle via Selenium  
2. Stocke le résultat dans un CSV  
3. Propose une interface web pour rechercher, filtrer et télécharger les offres  

---

## Table des matières

- [Fonctionnalités](#fonctionnalités)  
- [Prérequis](#prérequis)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Utilisation](#utilisation)  
  - [1. Lancement du scraper](#1-lancement-du-scraper)  
  - [2. Lancement de l’application Flask](#2-lancement-de-lapplication-flask)  
- [Structure du projet](#structure-du-projet)  
- [Dépendances](#dépendances)  
- [Licence](#licence)  
- [Auteur / Contact](#auteur--contact)  

---

## Fonctionnalités

- **Scraping Selenium**  
  - Recherche de votre terme sur Welcome to the Jungle  
  - Récupération du titre, entreprise, lieu, type de contrat, salaire, remote, etc.  
  - Ouverture en parallèle des fiches entreprise pour récupérer tags (secteur, effectif, date de création, etc.)  
- **Stockage**  
  - Fusion des données job + entreprise  
  - Génère un fichier `offres_et_compagnies.csv`  
- **Interface Web (Flask)**  
  - Formulaire de recherche  
  - Vue des résultats avec filtres par ville, type de contrat, entreprise  
  - Aperçu des 5 premières lignes en tableau HTML stylé  
  - Téléchargement du CSV complet  

---

## Prérequis

- Python 3.8+  
- Google Chrome (ou Chromium) installé  
- (Optionnel) Virtualenv / venv pour isoler l’environnement  

---

## Installation

1. **Cloner le dépôt**  
   ```bash
   git clone https://github.com/Aymanehajli/Welcometothejungle-scraper
   

2. **Créer et activer un environnement virtuel**  
    ```bash
    python -m venv venv
    source venv/bin/activate       # Linux / macOS
    venv\Scripts\activate.bat      # Windows


3. **Installer les dépendances**  
    ```bash
    pip install -r requirements.txt



---

## Utilisation

1. **Lancement du scraper**  
   ```bash
   python welcome.py "data analyst"



2. **Lancement de l’application Flask**  
   ```bash
   python app.py



3. **Ouvrez le navigateur**  
   ```bash
   http://localhost:5000
   


---

## Auteur
Aymane Hajli
