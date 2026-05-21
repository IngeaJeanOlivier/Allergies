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

    # Correctifs sur les colonnes Oui / Non (t / f) : les valeurs seront 1 ou 0.

    df2["Gender"] = df2["Gender"].apply(lambda z: int(1) if z=="t" else int(0))
    df2["Gender"] = df2["Gender"].astype("int64")

    df2["Sensitization"] = df2["Sensitization"].apply(lambda z: int(1) if z=="t" else int(0))
    df2["Sensitization"] = df2["Sensitization"].astype("int64")

    # Correctifs sur les colonnes ayant 1, 0, 9 pour (oui, non, non connu) :

    df2["Treatment_of_rhinitis"] = df2["Treatment_of_rhinitis"].apply(lambda z:int(z))

    df2["Treatment_of_athsma"] = df2["Treatment_of_athsma"].apply(lambda z: int(z) if str(z).isnumeric() else 1)
    df2["Treatment_of_athsma"] = df2["Treatment_of_athsma"].apply(lambda z: z if (z==0) or (z==9) else 1)

    # Correctifs sur les colonnes ayant 0, 1, 2, ..., N (catégories) :

    df2["General_cofactors"] = df2["General_cofactors"].apply(lambda z: int(z.split(",")[0]) if type(z)!=int else z)

    df2["Treatment_of_atopic_dematitis"] = df2["Treatment_of_atopic_dematitis"].apply(lambda z: int(z.split(",")[0]) if type(z)!=int else z)

    # Fichier clean
    df2.to_csv(path_or_buf=dest, index=False)

    nb_rows = df2.shape[0]
    logger.info(f"  ✓ Nettoyé : {dest.name} ({nb_rows} rows)")

    return True

if __name__ == "__main__":
    clean_data_allergies(Path(allergies_filepath), Path(allergies_clean_filepath))
