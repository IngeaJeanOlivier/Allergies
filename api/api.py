"""
API de diffusion des données sur les allergies, extraits de la base SQLite
Contrôle de clés d'API, gestion des erreurs, logs, vérifications
"""

from fastapi import FastAPI, HTTPException
from fastapi.security.api_key import APIKeyHeader
import sqlite3

from pydantic import BaseModel

# Exporter quoi : les données de allergies_clean_categories
# Colonnes : Patient_ID,Chip_Type,Age,Gender,Blood_Month_sample,Region,Urban_area,Sensitization,Treatment_of_rhinitis,Treatment_of_asthma,
# Age_of_onsets,Skin_Symptoms,General_cofactors,Treatment_of_atopic_dematitis,Acariens/Blattes,Aliments,Animaux,Moisissures/Autres,Pollens

class Patient(BaseModel):
    Patient_ID: str
    Chip_Type: str
    Age: str
    Gender: int
    Blood_Month_sample: float
    Region: str
    Urban_area: int
    Sensitization: int
    Treatment_of_rhinitis: str
    Treatment_of_asthma: int
    Age_of_onsets: str
    Skin_Symptoms: int
    General_cofactors: str
    Treatment_of_atopic_dematitis: str
    Acariens_Blattes: float
    Aliments: float
    Animaux: float
    Moisissures_Autres: float
    Pollens: float


import pandas as pd
import csv
import os

def load_patients_from_db(filepath: str = "../data/allergen_chip_challenge.db"):
    # On va lire les données allergies directement depuis la table dans la base de données :
    conn = sqlite3.connect(filepath)

    p = pd.read_sql("Select * From allergies_clean_categories", conn)
    conn.close()
    return p.to_dict(orient="records")

# Load all PATIENTS at startup
patients = load_patients_from_db()

# Here is the API
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the Data API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Data API"}

from typing import List, Optional

# On a ajouté les arguments "response_model=" aux fonctions suivantes : ça contrôle les données par rapport au modèle
# On a ajouté, après le "response_model", des arguments "summary" et "description" : but = pour expliquer la fonctionnalité (via DOCS)

@app.get("/patients", response_model=dict,
            summary="Get all patients",
    description="Retrieve a list of all patients. Optionally filter by Region using a query parameter.")
async def get_all_patients(region: Optional[str] = None):
    if region:
        filtered_patients = [p for p in patients if p["Region"].lower() == region.lower()]
        return {"patients": filtered_patients, "count": len(filtered_patients)}
    return {"patients": patients, "count": len(patients)}

# Sans gestion d'erreur, si on fait un GET sur un produit qui n'existe pas, on obtient "INTERNAL SERVER ERROR" :
# On a besoin de HTTP-Exception pour gérer cette erreur.
# On remplace le return par un RAISE.


@app.get("/patients/{patient_id}", response_model=Patient)
async def get_patient(patient_id: int):
    for patient in patients:
        if patient["Patient_ID"] == patient_id:
            return patient
    raise HTTPException(status_code=404, detail="Patient not found")

