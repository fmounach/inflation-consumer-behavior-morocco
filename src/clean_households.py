"""Extraire les coefficients budgétaires officiels de l’ENNVM 2022–2023."""

from pathlib import Path

import pandas as pd


RACINE = Path(__file__).resolve().parents[1]
TRAITE = RACINE / "data" / "processed"
CLASSEUR = RACINE / "data" / "raw" / (
    "Tabulation Rapport Enquête Nationale sur le Niveau de Vie des Ménages 2022-2023.xlsx"
)
FEUILLE = "Partie3-Structure de la DAMP"
QUINTILES = ["C1", "C2", "C3", "C4", "C5"]
# Lignes Excel, numérotées à partir de 1.
BLOCS = [("National", 294, 1), ("Urbain", 315, 6), ("Rural", 336, 11)]

# Le scénario prudent retient les fonctions dont les sous-groupes concordent.
# Les correspondances partielles ne servent qu’au scénario de sensibilité.
CORRESPONDANCES = [
    ("Produits alimentaires et boissons non alcoolisées", "proche",
     "DAMPG01 et IPC 011–012 : aliments (dont céréales, viandes et fruits) et boissons "
     "sans alcool. La division 01 est plus ciblée que l’agrégat Alimentation."),
    ("Boissons alcoolisées, tabac et stupéfiants", "partiel",
     "DAMPG02 publie une dépense de drogue (23), distincte de l’alcool et du tabac. "
     "Le détail IPC consulté montre 021 et 022, sans série identifiable pour les stupéfiants."),
    ("Articles d'habillement et chaussures", "proche",
     "DAMPG03 et IPC 031–032 : vêtements, chaussures et services associés "
     "comme le nettoyage, la réparation ou la cordonnerie."),
    ("Logement, eau, gaz, électricité et autres combustibles", "partiel",
     "DAMPG04 comprend les loyers imputés (42). L’IPC documente les loyers payés "
     "par les locataires (041), avec recoupement sur l’eau, l’énergie et l’entretien."),
    ("Meubles, articles de ménage et entretien courant du foyer", "proche",
     "DAMPG05 et IPC 051–056 : ameublement, textiles, appareils, vaisselle, outils "
     "et entretien courant."),
    ("Santé", "partiel",
     "Médicaments, soins ambulatoires et hospitaliers se recoupent. DAMPG06 inclut "
     "aussi les groupes 64 et 65 (dont médecine traditionnelle), sans équivalent "
     "identifiable pour l’ensemble de ces dépenses dans le détail IPC consulté."),
    ("Transports", "partiel",
     "Véhicules, utilisation et transport de voyageurs se recoupent. DAMPG07 inclut "
     "aussi le fret et les services postaux (74), ces derniers figurant dans l’IPC 081."),
    ("Communications", "partiel",
     "Recoupement sur la téléphonie. DAMPG08 comprend aussi le matériel informatique "
     "et audiovisuel que le détail IPC classe sous Loisirs et culture (091)."),
    ("Loisirs et culture", "partiel",
     "Le sport, la culture et la papeterie se recoupent. L’IPC 091 inclut le matériel "
     "audiovisuel et informatique qui relève de DAMPG08 dans l’enquête."),
    ("Enseignement", "proche",
     "DAMPG10 et IPC 101–105 : préscolaire et primaire, secondaire, postsecondaire "
     "non supérieur, supérieur et enseignement non défini par niveau."),
    ("Restaurants et hôtels", "partiel",
     "Restauration, cantines et hébergement figurent des deux côtés. DAMPG11 détaille "
     "aussi les repas livrés et divers services dont la couverture précise reste incertaine."),
    (None, "absent",
     "Aucune série mensuelle autonome. Le classeur IPC annuel de détail situe les "
     "assurances transports et l’intermédiation financière dans Biens et services divers."),
    ("Biens et services divers", "partiel",
     "Recoupement sur les soins et effets personnels. DAMPG13 inclut la protection "
     "sociale et la division IPC recoupe aussi le groupe 12."),
    (None, "absent",
     "Poste distinct exclu des deux scénarios. Les paiements fiscaux, transferts et "
     "remboursements ne sont pas nécessairement des achats de biens et services."),
]


def lire_bloc(feuille, premiere_ligne, profils):
    """Lire les lignes de postes et le total, en gardant les libellés publiés."""
    nombre_colonnes = 1 + 2 * len(profils)
    bloc = feuille.iloc[premiere_ligne - 1:premiere_ligne + 14, :nombre_colonnes].copy()
    unites = feuille.iloc[premiere_ligne - 2, 1:nombre_colonnes].tolist()
    if unites != ["DAMP", "CB"] * len(profils):
        raise ValueError(f"Colonnes DAMP/CB inattendues avant la ligne {premiere_ligne}.")
    categories = bloc.iloc[:14, 0].str.strip()
    codes = categories.str.extract(r"^(\d+)-", expand=False).astype(int)
    if codes.tolist() != list(range(1, 15)) or bloc.iloc[-1, 0] != "Dépense annuelle par personne":
        raise ValueError(f"Postes ou total inattendus à partir de la ligne {premiere_ligne}.")
    valeurs = bloc.iloc[:, 1:].apply(pd.to_numeric, errors="raise")
    if valeurs.isna().any().any() or valeurs.lt(0).any().any() or valeurs.eq(float("inf")).any().any():
        raise ValueError(f"Dépenses ou coefficients invalides à la ligne {premiere_ligne}.")

    for position, profil in enumerate(profils):
        damp = valeurs.iloc[:, 2 * position]
        cb = valeurs.iloc[:, 2 * position + 1]
        yield profil, pd.DataFrame({
            "code_groupe": codes.to_numpy(),
            "groupe_enquete": categories.to_numpy(),
            "damp_dh_courants_par_personne_an": damp.iloc[:-1].to_numpy(),
            "coefficient_budgetaire_pct": cb.iloc[:-1].to_numpy(),
            "ligne_excel": range(premiere_ligne, premiere_ligne + 14),
        }), damp.iloc[-1], cb.iloc[-1]


def main():
    with pd.ExcelFile(CLASSEUR, engine="openpyxl") as classeur:
        feuille = pd.read_excel(classeur, sheet_name=FEUILLE, header=None)
        notes = pd.read_excel(classeur, sheet_name="Considérations importantes", header=None)

    # SD 01 contrôle les trois ensembles. SD 12 donne les mêmes CB et publie
    # la DAMP avec davantage de décimales. On exporte les seuls profils uniques.
    sd01 = {
        milieu: (postes, damp, cb)
        for milieu, postes, damp, cb in lire_bloc(feuille, 8, ["Urbain", "Rural", "National"])
    }
    budgets, profils = [], []
    # Chaque CB est publié au dixième de point, soit au plus 0,05 par poste
    # sous l’hypothèse d’un arrondi au plus proche.
    tolerance = 14 * 0.05

    for milieu, debut, colonne_seuils in BLOCS:
        if feuille.iloc[debut - 5, 0] != milieu:
            raise ValueError(f"Milieu inattendu avant la ligne {debut}.")
        classes = QUINTILES + ["Total"]
        if feuille.iloc[debut - 3, 1:13:2].tolist() != classes:
            raise ValueError(f"Classes inattendues avant la ligne {debut}.")
        seuils = notes.iloc[31:36, colonne_seuils].tolist()
        for classe, postes, damp, cb in lire_bloc(feuille, debut, classes):
            profil = f"{milieu}_{classe}"
            somme = round(postes["coefficient_budgetaire_pct"].sum(), 3)
            if cb != 100 or abs(somme - cb) > tolerance + 1e-9:
                raise ValueError(f"{profil} : somme des CB inattendue ({somme} %).")
            if classe == "Total":
                postes_sd01, damp_sd01, cb_sd01 = sd01[milieu]
                if (
                    postes["coefficient_budgetaire_pct"].tolist()
                    != postes_sd01["coefficient_budgetaire_pct"].tolist()
                    or abs(damp - damp_sd01) > 0.5
                    or cb != cb_sd01
                ):
                    raise ValueError(f"{milieu} : les totaux de SD 01 et SD 12 divergent.")
            budgets.append(postes.assign(profil=profil, tableau_source="SD 12"))
            seuil = seuils[QUINTILES.index(classe)].strip() if classe in QUINTILES else None
            profils.append({
                "profil": profil,
                "milieu": milieu,
                "classe_depense": classe,
                "seuil_2022_libelle_hcp": seuil,
                "enquete": "ENNVM 2022-2023",
                "damp_totale_dh_courants_par_personne_an": damp,
                "total_cb_publie_pct": cb,
                "somme_cb_postes_pct": somme,
            })

    budgets = pd.concat(budgets, ignore_index=True)
    if budgets.duplicated(["profil", "code_groupe"]).any():
        raise ValueError("Un groupe apparaît deux fois pour le même profil.")
    profils = pd.DataFrame(profils)
    correspondance = sd01["National"][0][["code_groupe", "groupe_enquete"]].copy()
    correspondance[["colonne_ipc_candidate", "statut", "justification"]] = pd.DataFrame(
        CORRESPONDANCES, index=correspondance.index
    )
    colonnes_ipc = pd.read_csv(TRAITE / "ipc_maroc_mensuel.csv", nrows=0).columns
    candidates = correspondance["colonne_ipc_candidate"].dropna()
    if not candidates.isin(colonnes_ipc).all() or candidates.duplicated().any():
        raise ValueError("Colonnes IPC candidates absentes du CSV ou en double.")

    for nom, table in [
        ("depenses_menages_2022_2023.csv", budgets),
        ("profils_budgetaires_2022_2023.csv", profils),
        ("correspondance_depenses_ipc.csv", correspondance),
    ]:
        table.to_csv(TRAITE / nom, encoding="utf-8-sig", index=False)
    print(f"{len(profils)} profils, {len(budgets)} lignes de postes, {len(correspondance)} groupes.")
    print(profils[["profil", "somme_cb_postes_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
