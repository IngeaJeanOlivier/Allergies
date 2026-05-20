"""
Collecte de données sur les allergies
===========================================================
Script d'extraction automatisé depuis data.gouv.fr
Gestion des erreurs, logs, vérification d'intégrité.
"""

import sys
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pathlib import Path


# Quoi : obtenir les données à partir de https://www.data.gouv.fr/dataservices/api-tabulaire-data-gouv-fr-beta
# L'URL de base de l'API tabulaire est https://tabular-api.data.gouv.fr/api.
# /api/resources/7b55f69c-1773-4b98-9767-2301f71ff350/data/csv/

base_url_allergies = "https://tabular-api.data.gouv.fr/api"
id_data_allergies = "7b55f69c-1773-4b98-9767-2301f71ff350"
url_allergies = base_url_allergies + "/resources/" + id_data_allergies + "/data/csv/"
allergies_filepath = "../data/allergies.csv"

# Quoi : obtenir les données complémentaires pour les allergènes
# Aucun API disponible, donc utilisation du SCRAPING.
url_allergen_description = "https://allergen.org/search.php?allergenname=&allergensource=&TaxSource=&TaxOrder=&foodallerg=all&bioname=&browse=Browse"

allergens_filepath = "../data/allergens.csv"

timeout = 60

# ---------------------------------------------------------------------------
# Logging - chaque execution crée un nouveau fichier de log
# ---------------------------------------------------------------------------

log_file = f"../data/collect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Download using API - chaque execution crée un nouveau fichier de log
# ---------------------------------------------------------------------------

def download_file(url: str, dest: Path, timeout: int = 60) -> bool:
    """
    Télécharge un fichier avec gestion des erreurs HTTP et réseau.
    Retourne True si succès, False sinon.
    """
    logger.info(f"Téléchargement : {url}")
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        downloaded = 0
        #pour télécharger 8ko par 8ko : 
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

        size_mb = downloaded / (1024 * 1024)
        logger.info(f"  ✓ Téléchargé : {dest.name} ({size_mb:.1f} Mo)")
        return True

    except requests.exceptions.HTTPError as e:
        logger.error(f"  ✗ Erreur HTTP {e.response.status_code} : {url}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"  ✗ Erreur de connexion : impossible d'atteindre {url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"  ✗ Timeout ({timeout}s) dépassé pour : {url}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Erreur inattendue : {e}")
        return False
    
# ---------------------------------------------------------------------------
# Download using SCRAPING - chaque execution crée un nouveau fichier de log
# ---------------------------------------------------------------------------

def scrape_file(url: str, dest: Path, timeout: int = 60) -> bool:
    """
    Télécharge un fichier avec gestion des erreurs HTTP et réseau.
    Retourne True si succès, False sinon.
    """
    logger.info(f"Scraping : {url}")
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Status OK
        rows = []
        soup = BeautifulSoup(response.text)
        all_tr = soup.find_all("tr")
        rows_len = len(all_tr)
        for i in range(4, rows_len):
            tr = all_tr[i]
            # Working on a single row
            soup2 = BeautifulSoup(str(tr))
            all_a = soup2.find_all("td")
            all_a_contents = [z.contents for z in all_a]
            all_a_contents = all_a_contents[1:5]
            all_a_contents = [z[0] if z else None for z in all_a_contents]
            z = str(all_a_contents[0])
            z_start = z.find(">") + 1
            all_a_contents[0] = z[z_start:-4]
            rows.append(all_a_contents)
        # Writing down our data-file
        df = pd.DataFrame(rows, columns=["allergen", "name", "molecular_mass", "route"])
        df.to_csv(path_or_buf=dest)
        nb_rows = len(rows)
        logger.info(f"  ✓ Téléchargé : {dest.name} ({nb_rows} rows)")
        return True

    except requests.exceptions.HTTPError as e:
        logger.error(f"  ✗ Erreur HTTP {e.response.status_code} : {url}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"  ✗ Erreur de connexion : impossible d'atteindre {url}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"  ✗ Timeout ({timeout}s) dépassé pour : {url}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Erreur inattendue : {e}")
        return False

# ---------------------------------------------------------------------------
# Point d'entrée du module - collecte des données de façon automatisée
# ---------------------------------------------------------------------------
def do_collect():
    ok_allergies = download_file(url=url_allergies, dest=allergies_filepath)
    if ok_allergies:
        logger.info("Fichier allergies OK")
    else:
        logger.warning("Erreur lors du téléchargement du fichier des allergies")

    ok_allergenes = scrape_file(url=url_allergen_description, dest=allergens_filepath)
    if ok_allergenes:
        logger.info("Fichier allergènes OK")
    else:
        logger.warning("Erreur lors du téléchargement du fichier des allergènes")
    
    return True

if __name__ == "__main__":
    do_collect()