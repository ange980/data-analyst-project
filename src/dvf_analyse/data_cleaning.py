"""Nettoyage des DVF : de lignes brutes à une ligne par vente de logement."""

import pandas as pd

LOGEMENTS = ["Maison", "Appartement"]
LOCAL_COMMERCIAL = "Local industriel. commercial ou assimilé"


def garder_ventes(df: pd.DataFrame) -> pd.DataFrame:
    """Ne garde que la nature de mutation « Vente »."""
    return df[df["nature_mutation"] == "Vente"]


def exclure_sans_prix(df: pd.DataFrame) -> pd.DataFrame:
    """Exclut les lignes sans valeur foncière (variable cible, jamais imputée)."""
    return df[df["valeur_fonciere"].notna()]


def garder_mono_logement(df: pd.DataFrame) -> pd.DataFrame:
    """Garde les transactions comportant exactement un logement.

    Les transactions contenant un local industriel ou commercial sont aussi
    exclues : le prix ne peut pas être attribué au seul logement.
    """
    par_vente = df["id_mutation"]
    est_logement = df["type_local"].isin(LOGEMENTS)
    est_commerce = df["type_local"] == LOCAL_COMMERCIAL

    nb_logements = est_logement.groupby(par_vente).transform("sum")
    a_commerce = est_commerce.groupby(par_vente).transform("any")
    return df[(nb_logements == 1) & ~a_commerce]


def agreger_par_transaction(df: pd.DataFrame) -> pd.DataFrame:
    """Réduit chaque transaction à une ligne.

    Le prix est celui du logement (identique sur toutes les lignes de la vente,
    donc jamais sommé). Le terrain est la somme des surfaces par parcelle,
    avec une seule valeur par parcelle pour éviter les doubles comptages.
    Suppose que chaque transaction contient exactement un logement.
    """
    logements = df[df["type_local"].isin(LOGEMENTS)]
    colonnes = [
        "id_mutation",
        "date_mutation",
        "valeur_fonciere",
        "type_local",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "code_commune",
        "nom_commune",
        "code_departement",
        "code_postal",
        "longitude",
        "latitude",
    ]
    resultat = logements[colonnes].copy()
    resultat["type_local"] = resultat["type_local"].astype("string")
    resultat = resultat.set_index("id_mutation")

    resultat["nb_dependances"] = (
        (df["type_local"] == "Dépendance").groupby(df["id_mutation"]).sum()
    )
    resultat["surface_terrain"] = (
        df.groupby(["id_mutation", "id_parcelle"])["surface_terrain"]
        .max()
        .groupby("id_mutation")
        .sum(min_count=1)
    )

    resultat["prix_m2"] = resultat["valeur_fonciere"] / resultat["surface_reelle_bati"]
    resultat["annee"] = resultat["date_mutation"].dt.year
    return resultat.reset_index()


def filtrer_valeurs_aberrantes(
    df: pd.DataFrame,
    prix_min: float = 10_000,
    surface_min: float = 9,
    surface_max: float = 500,
    prix_m2_min: float = 500,
    prix_m2_max: float = 30_000,
) -> pd.DataFrame:
    """Exclut les prix, surfaces et prix au m² hors bornes (ou manquants)."""
    masque = (
        (df["valeur_fonciere"] >= prix_min)
        & df["surface_reelle_bati"].between(surface_min, surface_max)
        & df["prix_m2"].between(prix_m2_min, prix_m2_max)
    )
    return df[masque]


def nettoyer_dvf(
    df: pd.DataFrame, **seuils: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Applique toutes les règles de nettoyage.

    Returns:
        Le tableau propre (une ligne par vente) et un journal indiquant le
        nombre de lignes et de transactions restantes après chaque étape.
    """
    journal = [("Données brutes", len(df), df["id_mutation"].nunique())]

    etapes = [
        ("Ventes uniquement", garder_ventes),
        ("Prix renseigné", exclure_sans_prix),
        ("Un seul logement, sans local commercial", garder_mono_logement),
    ]
    for libelle, fonction in etapes:
        df = fonction(df)
        journal.append((libelle, len(df), df["id_mutation"].nunique()))

    df = agreger_par_transaction(df)
    journal.append(("Agrégation par transaction", len(df), len(df)))

    df = filtrer_valeurs_aberrantes(df, **seuils)
    journal.append(("Valeurs aberrantes exclues", len(df), len(df)))

    journal = pd.DataFrame(journal, columns=["etape", "lignes", "transactions"])
    return df.reset_index(drop=True), journal
