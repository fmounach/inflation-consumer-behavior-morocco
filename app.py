"""Tableau de bord du projet INSEA sur l’inflation au Maroc."""

from math import isfinite
from pathlib import Path

import pandas as pd


RACINE = Path(__file__).resolve().parent
TRAITE = RACINE / "data" / "processed"
SORTIES = RACINE / "outputs"
MILIEUX = ["National", "Urbain", "Rural"]
CLASSES = ["Total", "C1", "C2", "C3", "C4", "C5"]
PERIMETRES = {"Prudent": "prudent", "Élargi": "elargi"}
TAUX_RESSOURCES = "croissance_nominale_hypothetique_pct"


def simuler_choc(budget, couverture_pct, alimentation_pct, uniforme_pct, additionnel_pct,
                 nominal_pct):
    """Évaluer un choc sur un sous-panier avec les formules des notebooks 04 et 05."""
    valeurs = [budget, couverture_pct, alimentation_pct, uniforme_pct,
               additionnel_pct, nominal_pct]
    if not all(isfinite(v) for v in valeurs):
        raise ValueError("Toutes les valeurs doivent être finies.")
    if budget <= 0 or not 0 < couverture_pct <= 100 or not 0 <= alimentation_pct <= couverture_pct:
        raise ValueError("Budget positif et parts budgétaires cohérentes requis.")
    if uniforme_pct <= -100 or additionnel_pct <= -100 or nominal_pct < -100:
        raise ValueError("Les prix doivent rester positifs et les ressources non négatives.")

    # Le second choc alimentaire s’applique au prix déjà modifié.
    taux_uniforme = uniforme_pct / 100
    taux_alimentaire = taux_uniforme + (1 + taux_uniforme) * additionnel_pct / 100
    contribution = (alimentation_pct * taux_alimentaire
                    + (couverture_pct - alimentation_pct) * taux_uniforme)
    taux_panier = contribution / couverture_pct
    # Rapporter la croissance des ressources à la croissance du coût couvert.
    variation_pa = (nominal_pct / 100 - taux_panier) / (1 + taux_panier)
    supplement = budget * contribution / 100
    cout_initial = budget * couverture_pct / 100
    return {
        "couverture_pct": couverture_pct,
        "alimentation_budget_pct": alimentation_pct,
        "variation_prix_groupe_01_pct": 100 * taux_alimentaire,
        "variation_cout_pct": 100 * taux_panier,
        "contribution_budget_points": contribution,
        "cout_initial_mad": cout_initial,
        "cout_apres_choc_mad": cout_initial + supplement,
        "supplement_mad": supplement,
        "variation_pouvoir_achat_pct": 100 * variation_pa,
        "seuil_nominal_pct": 100 * taux_panier,
    }


def lire_donnees():
    """Charger les séries et résultats validés, sans écrire dans le projet."""
    ipc = pd.read_csv(TRAITE / "ipc_maroc_mensuel.csv", parse_dates=["date"]).sort_values("date")
    calendrier = pd.date_range("2017-01-01", "2026-10-01", freq="MS")
    if not pd.DatetimeIndex(ipc["date"]).equals(calendrier):
        raise ValueError("Le CSV IPC ne contient pas le calendrier mensuel complet attendu.")
    profils = pd.read_csv(TRAITE / "profils_budgetaires_2022_2023.csv")
    poids = pd.read_csv(SORTIES / "04_ponderations_sous_paniers.csv")
    pouvoir = pd.read_csv(SORTIES / "05_pouvoir_achat_historique.csv", parse_dates=["date"])
    return ipc, profils, poids, pouvoir


def taux_ipc(ipc):
    """Retrouver les deux variations de l’IPC général calculées en phase 02."""
    tableau = ipc.set_index("date")[["Indice Général"]].rename(
        columns={"Indice Général": "IPC général"}
    )
    indice = tableau["IPC général"]
    tableau["Variation mensuelle (%)"] = 100 * (indice / indice.shift(1) - 1)
    tableau["Glissement annuel (%)"] = 100 * (indice / indice.shift(12) - 1)
    return tableau


def nom_classe(classe):
    return "Ensemble" if classe == "Total" else classe


def nombre(valeur, unite=""):
    if round(valeur, 2) == 0:
        valeur = 0.0
    return f"{valeur:,.2f}".replace(",", " ").replace(".", ",") + unite


def telecharger(st, table, nom):
    st.download_button("Télécharger le tableau en CSV",
                       table.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=nom, mime="text/csv")


def accueil(st, ipc, profils):
    st.title("Inflation et budgets des ménages au Maroc")
    st.write("Projet académique individuel à l’INSEA · Inflation & Consumer Behavior Analysis – Morocco")
    a, b, c = st.columns(3)
    a.metric("Mois d’IPC", len(ipc))
    b.metric("Séries d’IPC", len(ipc.columns) - 1)
    c.metric("Profils de dépenses", len(profils))
    st.subheader("Explorer les données")
    st.write(
        "L’IPC du HCP couvre janvier 2017 à octobre 2026. Les budgets agrégés de "
        "l’ENNVM 2022–2023 décrivent la structure annuelle des dépenses par personne. "
        "Le menu permet de comparer les séries de prix, de consulter les résultats validés "
        "par profil et d’expérimenter des chocs hypothétiques."
    )
    st.info("Le simulateur mesure le coût et le pouvoir d’achat des seuls postes couverts. "
            "Les ressources saisies sont hypothétiques et la collecte des prix du HCP est urbaine.")


def historique(st, ipc):
    st.title("IPC national et inflation")
    st.caption("HCP · Janvier 2017 à octobre 2026 · IPC en base 100 en 2017")
    tableau = taux_ipc(ipc)
    debut, fin = st.slider("Années affichées", 2017, 2026, (2017, 2026))
    extrait = tableau.loc[str(debut):str(fin)]
    st.subheader("Niveau de l’indice")
    st.line_chart(extrait[["IPC général"]], color="#17566F", y_label="Points d’indice")
    st.subheader("Variations de l’indice")
    st.line_chart(extrait.iloc[:, 1:], color=["#00776E", "#A95129"], y_label="Variation (%)")
    st.caption("La variation mensuelle compare au mois précédent. Le glissement annuel compare "
               "au même mois un an plus tôt. Les taux sont calculés avant le filtre d’affichage.")
    with st.expander("Tableau des observations"):
        st.dataframe(extrait.round(2))
    telecharger(st, extrait.rename_axis("Date").reset_index(), "ipc_national_historique.csv")


def choisir_profil(st):
    a, b, c = st.columns(3)
    milieu = a.selectbox("Milieu", MILIEUX, key="milieu")
    classe = b.selectbox("Quintile de dépenses", CLASSES, format_func=nom_classe, key="classe")
    titre = c.selectbox("Périmètre", list(PERIMETRES), key="perimetre")
    return f"{milieu}_{classe}", PERIMETRES[titre]


def profils_historiques(st, profils, poids, pouvoir):
    st.title("Profils et coûts aux prix historiques")
    st.caption("Poids fixes de l’ENNVM 2022–2023 · Septembre 2022 comme référence")
    profil, perimetre = choisir_profil(st)
    lignes = pouvoir.loc[pouvoir["profil"].eq(profil) & pouvoir["perimetre"].eq(perimetre)]
    details = poids.loc[poids["profil"].eq(profil) & poids["perimetre"].eq(perimetre)]
    budget = profils.set_index("profil").loc[profil]
    a, b = st.columns(2)
    a.metric("Couverture budgétaire", nombre(details["couverture_budget_pct"].iloc[0], " %"))
    b.metric("Dépense annuelle moyenne par personne",
             nombre(budget["damp_totale_dh_courants_par_personne_an"], " MAD"))
    if not profil.endswith("_Total"):
        st.caption(f"Seuil de dépense du profil selon le HCP · {budget['seuil_2022_libelle_hcp']}")
    st.subheader("Indice de coût du sous-panier")
    cout = lignes.loc[lignes[TAUX_RESSOURCES].eq(0)].set_index("date")["variation_cout_sous_panier_pct"]
    st.line_chart((100 + cout).rename("Indice du sous-panier").sort_index(),
                  color="#17566F", y_label="Base 100 en septembre 2022")
    st.subheader("Pouvoir d’achat du sous-panier sous ressources hypothétiques")
    st.caption("Les taux de ressources sont des variations totales par rapport à septembre 2022. "
               "Les dates antérieures sont des comparaisons rétrospectives.")
    courbes = lignes.pivot(index="date", columns=TAUX_RESSOURCES,
                           values="variation_pouvoir_achat_sous_panier_pct")
    courbes.columns = [f"Ressources {g:+g} %" if g else "Ressources 0 %" for g in courbes.columns]
    st.line_chart(courbes, y_label="Variation des unités accessibles (%)")
    with st.expander("Pondérations et catégories couvertes"):
        st.dataframe(details[["groupe_enquete", "division_ipc", "statut_correspondance",
                              "coefficient_budget_initial_pct", "poids_sous_panier_pct"]].rename(columns={
            "groupe_enquete": "Groupe ENNVM", "division_ipc": "Division IPC",
            "statut_correspondance": "Correspondance",
            "coefficient_budget_initial_pct": "Part du budget total (%)",
            "poids_sous_panier_pct": "Poids dans le sous-panier (%)",
        }), hide_index=True)
    telecharger(st, lignes, "profil_cout_et_pouvoir_achat_historique.csv")


def simulation(st, poids):
    st.title("Simuler un choc de prix")
    st.caption("Scénarios hypothétiques · Quantités fixes · Ressources affectées au sous-panier")
    profil, perimetre = choisir_profil(st)
    a, b, c, d = st.columns(4)
    budget = a.number_input("Budget initial (MAD)", min_value=0.01, value=5000.0, step=100.0,
                            format="%.2f", key="budget")
    uniforme = b.number_input("Variation uniforme (%)", min_value=-99.0, max_value=300.0,
                              value=5.0, step=0.5, key="uniforme")
    additionnel = c.number_input("Choc alimentaire additionnel (%)", min_value=-99.0,
                                 max_value=300.0, value=10.0, step=0.5, key="additionnel")
    nominal = d.number_input("Croissance nominale des ressources (%)", min_value=-100.0,
                             max_value=300.0, value=0.0, step=0.5, key="nominal")

    # Le groupe 01 est inclus dans les deux périmètres. Son coefficient est celui du budget total.
    alimentaires = poids.loc[poids["perimetre"].eq(perimetre) & poids["code_groupe"].eq(1)]
    resultats = []
    for ligne in alimentaires.itertuples(index=False):
        for nom, choc in [("Uniforme", 0.0), ("Combiné", additionnel)]:
            resultat = simuler_choc(budget, ligne.couverture_budget_pct,
                                    ligne.coefficient_budget_initial_pct, uniforme, choc, nominal)
            milieu, classe = ligne.profil.split("_")
            resultats.append({
                "profil": ligne.profil, "milieu": milieu, "classe": nom_classe(classe),
                "perimetre": perimetre, "scenario": nom, "budget_initial_mad": budget,
                "hausse_uniforme_pct": uniforme, "choc_alimentaire_additionnel_pct": choc,
                "croissance_nominale_hypothetique_pct": nominal, **resultat,
            })
    tableau = pd.DataFrame(resultats)
    choisi = tableau.loc[tableau["profil"].eq(profil)].set_index("scenario")
    combine = choisi.loc["Combiné"]
    st.caption(f"Dans le choc combiné, la variation totale du prix alimentaire est de "
               f"{nombre(combine.variation_prix_groupe_01_pct, ' %')}. "
               "Le choc additionnel s’applique après la variation uniforme.")
    a, b, c, d = st.columns(4)
    a.metric("Couverture budgétaire", nombre(combine.couverture_pct, " %"))
    b.metric("Coût après le choc combiné", nombre(combine.cout_apres_choc_mad, " MAD"))
    c.metric("Supplément sur les postes couverts", nombre(combine.supplement_mad, " MAD"))
    d.metric("Variation des unités accessibles", nombre(combine.variation_pouvoir_achat_pct, " %"))
    st.write(f"Pour maintenir le nombre d’unités accessibles après le choc combiné, "
             f"la croissance nominale doit atteindre **{nombre(combine.seuil_nominal_pct, ' %')}**.")
    resume = ["cout_initial_mad", "cout_apres_choc_mad", "supplement_mad", "variation_cout_pct",
              "contribution_budget_points", "variation_pouvoir_achat_pct", "seuil_nominal_pct"]
    libelles = {
        "cout_initial_mad": "Coût initial (MAD)", "cout_apres_choc_mad": "Coût après choc (MAD)",
        "supplement_mad": "Supplément (MAD)", "variation_cout_pct": "Variation du coût (%)",
        "contribution_budget_points": "Contribution au budget initial (points)",
        "variation_pouvoir_achat_pct": "Variation des unités accessibles (%)",
        "seuil_nominal_pct": "Seuil nominal (%)", "couverture_pct": "Couverture (%)",
        "milieu": "Milieu", "classe": "Quintile de dépenses", "scenario": "Choc",
    }
    st.dataframe(choisi[resume].rename(columns=libelles).round(2))
    st.subheader("Comparer les 18 profils")
    graphique = tableau.pivot(index="profil", columns="scenario", values="variation_pouvoir_achat_pct")
    ordre = [f"{m}_{q}" for m in MILIEUX for q in CLASSES]
    graphique = graphique.reindex(ordre)[["Uniforme", "Combiné"]]
    graphique.index = [f"{m} · {nom_classe(q)}" for m in MILIEUX for q in CLASSES]
    st.bar_chart(graphique, horizontal=True, stack=False, color=["#00776E", "#A95129"],
                 x_label="Variation des unités accessibles (%)", height=530)
    st.dataframe(tableau[["milieu", "classe", "scenario", "couverture_pct", *resume]]
                 .rename(columns=libelles).round(2), hide_index=True)
    telecharger(st, tableau, "simulations_18_profils.csv")
    st.caption("La contribution rapporte le supplément au budget initial total. Le taux de coût et "
               "la variation des unités accessibles concernent uniquement le sous-panier.")


def sources(st):
    st.title("Sources, hypothèses et limites")
    st.markdown(
        "- [Séries d’IPC du Haut-Commissariat au Plan](https://www.hcp.ma/"
        "Indicateurs-Indices-des-prix-a-la-consommation-IPC_r351.html) · Base 100 en 2017.\n"
        "- [Méthodologie de l’IPC du HCP](https://m.hcp.ma/"
        "Note-methodologique-sur-l-Indice-des-Prix-a-la-Consommation-Base-100-2017_a4095.html)"
        " · Collecte dans 18 villes.\n"
        "- [Rapport ENNVM 2022–2023 du HCP](https://www.hcp.ma/"
        "Rapport-des-resultats-de-l-Enquete-Nationale-sur-le-Niveau-de-Vie-des-Menages-2022-2023_a4062.html)"
        " · Collecte du 15 mars 2022 au 14 mars 2023."
    )
    st.subheader("Périmètres et profils")
    st.write("Le prudent retient les groupes 01, 03, 05 et 10. L’élargi retient les groupes "
             "01 à 11 et 13, avec des correspondances partielles. Les groupes 12 et 14 sont exclus. "
             "C1 à C5 classent les dépenses annuelles par personne, selon des seuils propres à chaque milieu.")
    st.subheader("Interpréter la simulation")
    st.latex(r"\Delta_{\mathrm{PA}} = \frac{1+g_R}{1+\pi_h}-1")
    st.write("Le taux nominal hypothétique g_R s’applique aux ressources affectées au sous-panier. "
             "Son égalité avec le taux de coût π_h permet de maintenir le nombre d’unités accessibles. "
             "Les quantités restent fixes et les substitutions ne sont pas modélisées.")
    st.write("Les prix communs utilisés pour les profils ruraux sont issus d’une collecte urbaine. "
             "La comparaison entre milieux traduit les structures budgétaires sous cette hypothèse. "
             "L’analyse ne dispose pas de trajectoires de revenus observées et couvre une partie du budget.")


def main():
    import streamlit as st

    st.set_page_config(page_title="Inflation et budgets au Maroc", layout="wide")
    st.sidebar.header("Inflation au Maroc")
    page = st.sidebar.radio("Navigation", [
        "Accueil", "IPC historique", "Profils budgétaires", "Simulation", "Sources et limites"
    ])
    if page == "Sources et limites":
        sources(st)
        return
    try:
        ipc, profils, poids, pouvoir = st.cache_data(lire_donnees)()
    except (OSError, ValueError) as erreur:
        st.error(f"Impossible de charger les CSV du projet. {erreur}")
        return

    if page == "Accueil":
        accueil(st, ipc, profils)
    elif page == "IPC historique":
        historique(st, ipc)
    elif page == "Profils budgétaires":
        profils_historiques(st, profils, poids, pouvoir)
    else:
        simulation(st, poids)


if __name__ == "__main__":
    main()
