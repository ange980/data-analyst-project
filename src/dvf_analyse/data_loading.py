"""Chargement des fichiers DVF géolocalisées."""

from pathlib import Path

import pandas as pd

COLONNES_TEXTE = {
    "id_mutation": "string",
    "code_commune": "string",
    "code_postal": "string",
    "code_departement": "string",
    "id_parcelle": "string",
    "nom_commune": "string",
    "nature_mutation": "category",
    "type_local": "category",
}

COLONNES_UTILES = [
    "id_mutation",
    "date_mutation",
    "numero_disposition",
    "nature_mutation",
    "valeur_fonciere",
    "code_postal",
    "code_commune",
    "nom_commune",
    "code_departement",
    "id_parcelle",
    "type_local",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "surface_terrain",
    "longitude",
    "latitude",
]


def charger_fichier(chemin: Path | str) -> pd.DataFrame:
    """Charge un fichier DVF (CSV ou CSV compressé) en gardant les colonnes utiles.

    Les codes (commune, postal...) sont lus comme du texte pour conserver
    les zéros initiaux. Une colonne `annee_fichier` est ajoutée à partir de
    la date de mutation.

    Raises:
        FileNotFoundError: si le fichier n'existe pas.
    """
    chemin = Path(chemin)
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    df = pd.read_csv(
        chemin,
        usecols=lambda col: col in COLONNES_UTILES,
        dtype=COLONNES_TEXTE,
        parse_dates=["date_mutation"],
    )
    df["annee_fichier"] = df["date_mutation"].dt.year
    return df


def charger_dossier(dossier: Path | str, motif: str = "*.csv*") -> pd.DataFrame:
    """Charge tous les fichiers DVF d'un dossier et les concatène.

    Raises:
        FileNotFoundError: si aucun fichier ne correspond au motif.
    """
    dossier = Path(dossier)
    fichiers = sorted(dossier.glob(motif))
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier '{motif}' dans {dossier}")

    return pd.concat((charger_fichier(f) for f in fichiers), ignore_index=True)