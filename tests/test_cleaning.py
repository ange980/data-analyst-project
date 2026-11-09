import numpy as np
import pandas as pd

from dvf_analyse.data_cleaning import garder_mono_logement, garder_ventes, nettoyer_dvf


def ligne(id_mutation, type_local, **autres):
    base = {
        "id_mutation": id_mutation,
        "date_mutation": pd.Timestamp("2023-05-10"),
        "nature_mutation": "Vente",
        "valeur_fonciere": 200_000.0,
        "type_local": type_local,
        "surface_reelle_bati": np.nan,
        "surface_terrain": np.nan,
        "id_parcelle": "P1",
        "nombre_pieces_principales": np.nan,
        "code_commune": "69123",
        "nom_commune": "Lyon",
        "code_departement": "69",
        "code_postal": "69001",
        "longitude": 4.8,
        "latitude": 45.7,
    }
    base.update(autres)
    return base


def donnees_test():
    lignes = [
        # A : appartement + garage, valide
        ligne("A", "Appartement", surface_reelle_bati=50.0),
        ligne("A", "Dépendance"),
        # B : prix manquant
        ligne("B", "Appartement", surface_reelle_bati=60.0, valeur_fonciere=np.nan),
        # C : VEFA
        ligne(
            "C",
            "Appartement",
            surface_reelle_bati=60.0,
            nature_mutation="Vente en l'état futur d'achèvement",
        ),
        # D : deux logements dans la même vente
        ligne("D", "Appartement", surface_reelle_bati=40.0),
        ligne("D", "Appartement", surface_reelle_bati=40.0),
        # E : maison avec deux parcelles de terrain
        ligne("E", "Maison", surface_reelle_bati=100.0, valeur_fonciere=400_000.0),
        ligne("E", None, surface_terrain=300.0, valeur_fonciere=400_000.0),
        ligne(
            "E",
            None,
            surface_terrain=200.0,
            id_parcelle="P2",
            valeur_fonciere=400_000.0,
        ),
        # F : prix aberrant (5 000 €)
        ligne("F", "Appartement", surface_reelle_bati=50.0, valeur_fonciere=5_000.0),
    ]
    return pd.DataFrame(lignes)


def test_garder_ventes_exclut_vefa():
    df = garder_ventes(donnees_test())
    assert "C" not in set(df["id_mutation"])


def test_mono_logement_exclut_deux_logements():
    df = garder_mono_logement(donnees_test())
    assert "D" not in set(df["id_mutation"])


def test_pipeline_garde_uniquement_les_ventes_valides():
    propre, _ = nettoyer_dvf(donnees_test())
    assert set(propre["id_mutation"]) == {"A", "E"}


def test_pipeline_calculs():
    propre, _ = nettoyer_dvf(donnees_test())
    propre = propre.set_index("id_mutation")
    assert propre.loc["A", "nb_dependances"] == 1
    assert propre.loc["A", "prix_m2"] == 4000
    assert propre.loc["E", "surface_terrain"] == 500
    assert propre.loc["E", "prix_m2"] == 4000


def test_journal_decroissant():
    _, journal = nettoyer_dvf(donnees_test())
    assert journal["transactions"].is_monotonic_decreasing
