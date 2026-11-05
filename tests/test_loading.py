import pandas as pd
import pytest

from dvf_analyse.data_loading import charger_dossier, charger_fichier

CSV_FACTICE = """id_mutation,date_mutation,nature_mutation,valeur_fonciere,code_commune,code_postal,type_local,surface_reelle_bati
2023-1,2023-03-15,Vente,250000.0,01004,01500,Appartement,65
2023-2,2023-06-20,Vente,180000.0,69123,69001,Maison,90
2023-2,2023-06-20,Vente,180000.0,69123,69001,Dépendance,
"""


@pytest.fixture
def fichier_dvf(tmp_path):
    chemin = tmp_path / "dvf_test.csv"
    chemin.write_text(CSV_FACTICE, encoding="utf-8")
    return chemin


def test_nombre_de_lignes(fichier_dvf):
    df = charger_fichier(fichier_dvf)
    assert len(df) == 3


def test_colonnes_attendues(fichier_dvf):
    df = charger_fichier(fichier_dvf)
    assert {"id_mutation", "valeur_fonciere", "annee_fichier"} <= set(df.columns)


def test_codes_gardent_leurs_zeros(fichier_dvf):
    df = charger_fichier(fichier_dvf)
    assert df.loc[0, "code_commune"] == "01004"


def test_date_et_annee(fichier_dvf):
    df = charger_fichier(fichier_dvf)
    assert pd.api.types.is_datetime64_any_dtype(df["date_mutation"])
    assert (df["annee_fichier"] == 2023).all()


def test_fichier_inexistant(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_fichier(tmp_path / "absent.csv")


def test_charger_dossier_concatene(fichier_dvf):
    df = charger_dossier(fichier_dvf.parent)
    assert len(df) == 3


def test_dossier_vide(tmp_path):
    with pytest.raises(FileNotFoundError):
        charger_dossier(tmp_path)