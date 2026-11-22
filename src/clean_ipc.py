"""Préparer la série mensuelle d'IPC du HCP, base 100 en 2017."""

from pathlib import Path

import pandas as pd


RACINE = Path(__file__).resolve().parents[1]
DOSSIER_BRUT = RACINE / "data" / "raw"
SORTIE = RACINE / "data" / "processed" / "ipc_maroc_mensuel.csv"

# Les trois fichiers mensuels retenus. Le classeur annuel reste en dehors.
FICHIERS = {
    "IPC par grandes divisions - mensuel (Base 100 _ 2017).xlsx": 3,
    "IPC par divisions - mensuel (groupe 1) (Base 100 _ 2017).xlsx": 6,
    "IPC par divisions - mensuel (groupe 2) (Base 100 _ 2017).xlsx": 6,
}
MOIS_ATTENDUS = pd.date_range("2017-01-01", "2026-10-01", freq="MS")


def lire_ipc(chemin, nombre_series):
    """Lire un classeur et contrôler sa structure, ses dates et ses valeurs."""
    # La ligne 24 contient les libellés. Les lire comme des données permet
    # de vérifier les doublons avant que pandas renomme les colonnes.
    feuille = pd.read_excel(chemin, sheet_name=0, skiprows=23, header=None)
    feuille = feuille.dropna(axis="columns", how="all")
    entetes = feuille.iloc[0].astype("string").str.strip()
    if (
        entetes.isna().any()
        or entetes.eq("").any()
        or entetes.duplicated().any()
        or len(entetes) != nombre_series + 1
        or entetes.iloc[0] != "Mois"
        or "date" in entetes.tolist()
    ):
        raise ValueError(f"{chemin.name} : en-têtes inattendus ou en double.")

    donnees = feuille.iloc[1:].copy()
    donnees.columns = entetes.tolist()
    donnees = donnees.dropna(how="all")
    series = donnees.columns.drop("Mois")

    # Retirer la note de source uniquement quand la ligne ne porte aucun indice.
    mois_texte = donnees["Mois"].astype("string").str.strip()
    note = mois_texte.str.startswith("Source :", na=False)
    note = note & donnees[series].isna().all(axis="columns")
    donnees = donnees.loc[~note].copy()
    mois_texte = mois_texte.loc[~note]

    # Chaque mois est représenté par son premier jour pour la fusion.
    format_valide = mois_texte.str.fullmatch(r"[0-9]{4}/[0-9]{2}", na=False)
    dates = pd.to_datetime(mois_texte.where(format_valide), format="%Y/%m", errors="coerce")
    if dates.isna().any():
        raise ValueError(f"{chemin.name} : dates invalides {mois_texte[dates.isna()].tolist()}.")
    doublons = dates[dates.duplicated(keep=False)].dt.strftime("%Y-%m").unique()
    if len(doublons):
        raise ValueError(f"{chemin.name} : mois en double {list(doublons)}.")

    # Vérifier que les trois fichiers couvrent tous les mois annoncés.
    mois_observes = pd.DatetimeIndex(dates)
    absents = MOIS_ATTENDUS.difference(mois_observes).strftime("%Y-%m").tolist()
    hors_periode = mois_observes.difference(MOIS_ATTENDUS).strftime("%Y-%m").tolist()
    if absents or hors_periode:
        raise ValueError(
            f"{chemin.name} : mois absents {absents}, hors période {hors_periode}."
        )

    # Garder les cellules vides et signaler les valeurs invalides.
    for serie in series:
        valeurs = donnees[serie]
        indices = pd.to_numeric(valeurs, errors="coerce")
        invalides = (valeurs.notna() & indices.isna()) | (indices <= 0) | (indices == float("inf"))
        if invalides.any():
            mois_invalides = dates[invalides].dt.strftime("%Y-%m").tolist()
            raise ValueError(f"{chemin.name} : IPC invalide pour « {serie} » en {mois_invalides}.")
        donnees[serie] = indices

    donnees["Mois"] = dates
    donnees = donnees.rename(columns={"Mois": "date"}).sort_values("date")
    manquantes = donnees[series].isna().sum()
    print(f"{chemin.name}")
    print(f"  {len(donnees)} mois, {len(series)} séries, 0 mois en double, "
          f"{manquantes.sum()} valeurs manquantes.")
    for serie, nombre in manquantes[manquantes > 0].items():
        print(f"  {serie} : {nombre} valeurs manquantes.")
    return donnees


def main():
    """Fusionner les séries sur la date et enregistrer le résultat."""
    tableaux = [
        lire_ipc(DOSSIER_BRUT / nom, nombre_series)
        for nom, nombre_series in FICHIERS.items()
    ]

    # Conserver les libellés officiels. Un chevauchement exact demande un examen
    # des séries avant de décider si elles représentent le même indicateur.
    ipc = tableaux[0]
    for tableau in tableaux[1:]:
        communs = ipc.columns.intersection(tableau.columns).drop("date")
        if len(communs):
            raise ValueError(f"Catégories portant le même nom : {communs.tolist()}.")
        ipc = ipc.merge(tableau, on="date", how="inner", validate="one_to_one")

    ipc = ipc.sort_values("date")
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    ipc.to_csv(SORTIE, index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")

    debut = ipc["date"].min().strftime("%Y-%m")
    fin = ipc["date"].max().strftime("%Y-%m")
    print(f"Résultat : {len(ipc)} lignes × {len(ipc.columns)} colonnes, de {debut} à {fin}.")
    print(f"Valeurs manquantes conservées : {ipc.isna().sum().sum()}.")
    print(f"CSV : {SORTIE.relative_to(RACINE)}")


if __name__ == "__main__":
    main()
