"""Téléchargement des DVF géolocalisées depuis files.data.gouv.fr."""

from pathlib import Path
from urllib.request import urlretrieve

URL_BASE = "https://files.data.gouv.fr/geo-dvf/latest/csv"


def download_dvf(
    departement: str, annees: list[int], dossier: Path = Path("data/raw")
) -> list[Path]:
    """Télécharge les fichiers DVF d'un département pour plusieurs années.

    Les fichiers déjà présents ne sont pas retéléchargés.
    """
    dossier.mkdir(parents=True, exist_ok=True)
    chemins = []
    for annee in annees:
        url = f"{URL_BASE}/{annee}/departements/{departement}.csv.gz"
        destination = dossier / f"dvf_{departement}_{annee}.csv.gz"
        if not destination.exists():
            print(f"Téléchargement de {url}")
            urlretrieve(url, destination)
        chemins.append(destination)
    return chemins
