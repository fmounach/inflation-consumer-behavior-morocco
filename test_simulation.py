"""Vérifier les formules du tableau de bord et les résultats de référence."""

import unittest

import pandas as pd

from app import SORTIES, lire_donnees, simuler_choc, taux_ipc


class TestSimulation(unittest.TestCase):
    def test_hausse_uniforme_et_compensation(self):
        resultat = simuler_choc(5000, 41.4, 33.4, 5, 0, 5)
        self.assertAlmostEqual(resultat["cout_initial_mad"], 2070)
        self.assertAlmostEqual(resultat["cout_apres_choc_mad"], 2173.50)
        self.assertAlmostEqual(resultat["supplement_mad"], 103.50)
        self.assertAlmostEqual(resultat["variation_cout_pct"], 5)
        self.assertAlmostEqual(resultat["variation_pouvoir_achat_pct"], 0)

    def test_choc_compose_et_contribution(self):
        resultat = simuler_choc(5000, 41.4, 33.4, 5, 10, 0)
        self.assertAlmostEqual(resultat["variation_prix_groupe_01_pct"], 15.5)
        self.assertAlmostEqual(resultat["contribution_budget_points"], 5.577)
        self.assertAlmostEqual(resultat["supplement_mad"], 278.85)
        seuil = resultat["seuil_nominal_pct"]
        self.assertAlmostEqual(simuler_choc(5000, 41.4, 33.4, 5, 10, seuil)
                               ["variation_pouvoir_achat_pct"], 0)

    def test_baisse_des_prix_et_ressources_nulles(self):
        self.assertGreater(simuler_choc(5000, 50, 20, -5, 0, 0)
                           ["variation_pouvoir_achat_pct"], 0)
        self.assertAlmostEqual(simuler_choc(5000, 50, 20, -5, 0, -100)
                               ["variation_pouvoir_achat_pct"], -100)

    def test_rejette_parametres_invalides(self):
        for i, valeur in [(0, 0), (1, 0), (1, 101), (2, 45), (3, -100),
                           (4, -100), (5, -101), (5, float("nan"))]:
            args = [5000, 41.4, 33.4, 5, 10, 0]
            args[i] = valeur
            with self.subTest(i=i, valeur=valeur), self.assertRaises(ValueError):
                simuler_choc(*args)

    def test_concorde_avec_les_288_resultats_valides(self):
        _, _, poids, _ = lire_donnees()
        coefficient = poids.loc[poids["code_groupe"].eq(1)].set_index(["perimetre", "profil"])
        chocs = pd.read_csv(SORTIES / "04_chocs_hypothetiques.csv").set_index(
            ["perimetre", "profil", "choc_hypothetique"]
        )
        pouvoir = pd.read_csv(SORTIES / "05_pouvoir_achat_chocs.csv")
        self.assertEqual(len(pouvoir), 288)
        for ligne in pouvoir.itertuples(index=False):
            cle = (ligne.perimetre, ligne.profil)
            precedent = chocs.loc[(*cle, ligne.choc_hypothetique)]
            alimentaire = 0 if ligne.choc_hypothetique == "uniforme_5pct" else 10
            resultat = simuler_choc(
                5000, ligne.couverture_budget_pct,
                coefficient.loc[cle, "coefficient_budget_initial_pct"], 5, alimentaire,
                ligne.croissance_nominale_hypothetique_pct,
            )
            self.assertAlmostEqual(resultat["variation_pouvoir_achat_pct"],
                                   ligne.variation_pouvoir_achat_sous_panier_pct, places=7)
            self.assertAlmostEqual(resultat["seuil_nominal_pct"],
                                   ligne.croissance_nominale_equilibre_pct, places=7)
            self.assertAlmostEqual(resultat["supplement_mad"],
                                   precedent.supplement_postes_couverts_mad, places=7)

    def test_variations_ipc_historiques(self):
        ipc, _, _, _ = lire_donnees()
        variations = taux_ipc(ipc)
        self.assertEqual(len(variations), 118)
        self.assertEqual(variations["Variation mensuelle (%)"].isna().sum(), 1)
        self.assertEqual(variations["Glissement annuel (%)"].isna().sum(), 12)
        self.assertAlmostEqual(variations["Variation mensuelle (%)"].max(), 1.790763, places=5)
        self.assertAlmostEqual(variations["Glissement annuel (%)"].max(), 10.084826, places=5)


if __name__ == "__main__":
    unittest.main()
