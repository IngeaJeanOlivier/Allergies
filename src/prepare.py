"""
Nettoyage des données sur les allergies
===========================================================
Script de préparation et nettoyage des données
Gestion des erreurs, logs, vérification d'intégrité.
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path


# RAW files
allergies_filepath = "../data/allergies.csv"
allergens_filepath = "../data/allergens.csv"

# CLEAN files
allergies_clean_filepath = "../data/allergies_clean.csv"

# Dictionnaires utilitaires à la préparation des données
d_age_apparition = {
        9:"Non renseigné",
        0:"Aucun",
        1:"0 - 2 ans",
        2:"0 - 2 ans",
        3:"2 - 3 ans",
        4:"3 - 10 ans",
        5:"10 - 20 ans",
        6:"20 ans et plus"
}

d_traitement_actuel_da = {
        9:"Non renseigné",
        0:"Pas de traitement",
        1:"Emollients",
        2:"Dermocorticoïdes",
        3:"Autres",
        4:"Ciclosporine",
        5:"Dupilumab",
        6:"Upadacitinib",
        7:"Autres"
}

d_facteurs = {
        9: "Non renseigné",
        0: "Aucun",
        1: "Effort/Activité sportive",
        2: "Autres",
        3: "Alcool",
        4: "Moisissures",
        5: "Acariens",
        6: "Animaux : chat/chien",
        7: "Animaux : chat/chien",
        8: "Animaux : cheval/rongeur",
        10: "Animaux : cheval/rongeur",
        11: "Autres",
        12: "Autres"
}

d_traitement_rhinite = {
        9: "Non renseigné",
        0: "Aucun",
        1: "Anti-H1, voie locale",
        2: "Anti-H1 voie générale",
        3: "Anti-H1 + CS voie locale",
        4: "CS voie générale"

}

# Fonction utilitaire pour l'âge
def age_to_categories(a: int) -> str:
    if a<20:
        return "0 à 20"
    elif a<40:
        return "20 à 40"
    elif a<60:
        return "40 à 60"
    else:
        return "60 à Plus"


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
# Nettoyage des données allergies
# ---------------------------------------------------------------------------

def clean_data_allergies(source: Path, dest: Path) -> bool:
    """
    Nettoyage des données allergies
    """

    logger.info(f"Nettoyage : {source.name}")

    df = pd.read_csv(filepath_or_buffer=source)

    # Dans certaines colonnes, parfois la réaction à l'allergène n'est pas saisie, on remplacera alors les valeurs nulles par zero.
    lst_col = []
    lst_col_replace_na = []
    r = df.shape[0]

    for c in df.columns:
        z = int(df[c].isna().sum())/r
        lst_col.append([z, c])
        if z >= 0.1:
            lst_col_replace_na.append(c)

    lst_col.sort(reverse=True)

    # Lorsque le test n'a pas de résultat saisi, on met par défaut zero (pour pas de réaction à l'allergène)

    df[lst_col_replace_na] = df[lst_col_replace_na].fillna(value=0)

    # Il reste très peu de valeurs nulles, on enlève les lignes correspondantes.

    df2 = df.dropna(axis=0, how="any")

    # Nous n'allons pas regarder les détails au niveau du département. Il y a de toute façon une anonymisation des départements et régions.

    df2 = df2.drop(columns=["French_Residence_Department"])

    # Application de catégories sur l'âge :
    df2["Age"] = df2["Age"].apply(lambda z: age_to_categories(z))

    # Correctifs sur les colonnes Oui / Non (t / f) : les valeurs seront 1 ou 0.

    df2["Gender"] = df2["Gender"].apply(lambda z: int(1) if z=="t" else int(0))
    df2["Gender"] = df2["Gender"].astype("int64")

    df2["Sensitization"] = df2["Sensitization"].apply(lambda z: int(1) if z=="t" else int(0))
    df2["Sensitization"] = df2["Sensitization"].astype("int64")

    # Simplification de la colonne Rural_or_urban_area (1, 0, 9), on ne gardera que (1, 0) :
    df2["Rural_or_urban_area"] = df2["Rural_or_urban_area"].apply(lambda z: 1 if int(z)==1 else 0)
    df2.rename(columns={"Rural_or_urban_area": "Urban_area"}, inplace=True)

    # Simplification pour la colonne Treatment_of_athsma (1, 0, 9), on ne gardera que (1, 0) :
    df2["Treatment_of_athsma"] = df2["Treatment_of_athsma"].apply(lambda z: int(str(z).split(",")[0]))
    df2["Treatment_of_athsma"] = df2["Treatment_of_athsma"].apply(lambda z: 1 if ((z!=0) and (z!=9)) else 0)
    df2.rename(columns={"Treatment_of_athsma": "Treatment_of_asthma"}, inplace=True)

    # Simplification pour la colonne Skin_Symptoms (1, 0, 9), on ne gardera que (1, 0) :
    df2["Skin_Symptoms"] = df2["Skin_Symptoms"].apply(lambda z: 1 if z==1 else 0)

    # Correctifs sur les colonnes ayant 0, 1, 2, ..., N (catégories) :

    df2["Treatment_of_rhinitis"] = df2["Treatment_of_rhinitis"].apply(lambda z:int(z))

    df2["General_cofactors"] = df2["General_cofactors"].apply(lambda z: int(z.split(",")[0]) if type(z)!=int else z)

    df2["Treatment_of_atopic_dematitis"] = df2["Treatment_of_atopic_dematitis"].apply(lambda z: int(z.split(",")[0]) if type(z)!=int else z)

    df2["Age_of_onsets"] = df2["Age_of_onsets"].apply(lambda z: int(z.split(",")[0]) if type(z)!=int else z)

    # Application du dictionnaire : rhinite, facteurs et dermatite atopique et age d'apparition des symptômes
    df2["Treatment_of_rhinitis"] = df2["Treatment_of_rhinitis"].apply(lambda z: d_traitement_rhinite.get(z, z))

    df2["General_cofactors"] = df2["General_cofactors"].apply(lambda z: d_facteurs.get(z, z))

    df2["Treatment_of_atopic_dematitis"] = df2["Treatment_of_atopic_dematitis"].apply(lambda z: d_traitement_actuel_da.get(z, z))

    df2["Age_of_onsets"] = df2["Age_of_onsets"].apply(lambda z: d_age_apparition.get(z, z))

    # Fichier clean
    df2.to_csv(path_or_buf=dest, index=False)

    nb_rows = df2.shape[0]
    logger.info(f"  ✓ Nettoyé : {dest.name} ({nb_rows} rows)")

    return True

if __name__ == "__main__":
    clean_data_allergies(Path(allergies_filepath), Path(allergies_clean_filepath))
