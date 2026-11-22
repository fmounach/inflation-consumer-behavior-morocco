# Inflation & Consumer Behavior Analysis – Morocco

Projet académique individuel de première année à l’INSEA, filière Économie Appliquée – Statistique et Big Data.

**Problématique.** Comment l’évolution des prix affecte-t-elle le coût de sous-paniers à composition fixe pour différents profils de dépenses au Maroc ? Dans quelles conditions des ressources nominales hypothétiques permettraient-elles de maintenir le nombre d’unités accessibles ?

## Données et méthode

- **Prix.** Trois séries de tableaux mensuels du Haut-Commissariat au Plan (HCP), en base 100 en 2017, fournissent 118 mois de janvier 2017 à octobre 2026 et 15 séries, dont l’IPC général. Le nettoyage vérifie les libellés et le calendrier, puis fusionne les classeurs sur le mois. L’analyse distingue variation mensuelle, glissement annuel et variation des moyennes annuelles. [Indicateurs IPC du HCP](https://www.hcp.ma/Indicateurs-Indices-des-prix-a-la-consommation-IPC_r351.html)
- **Dépenses.** Le tableau SD 12 de l’ENNVM 2022–2023 fournit 18 profils agrégés et 14 groupes de dépenses. SD 01 sert à contrôler les trois ensembles. Les quintiles portent sur les dépenses annuelles par personne et leurs seuils sont propres à chaque milieu. [Rapport et tabulation de l’ENNVM](https://www.hcp.ma/Rapport-des-resultats-de-l-Enquete-Nationale-sur-le-Niveau-de-Vie-des-Menages-2022-2023_a4062.html)
- **Simulation.** Le périmètre prudent retient les groupes 01, 03, 05 et 10. L’élargi retient les groupes 01 à 11 et 13, avec des correspondances partielles. Les poids sont normalisés dans chaque sous-panier, dont la couverture reste indiquée en proportion du budget total. Les scénarios aux prix historiques utilisent un panier fixe, et les chocs hypothétiques sont traités séparément.

## Obtenir les fichiers de données

Créer `data/raw/` à la racine et y déposer les classeurs HCP avec les noms suivants.

| Fichier attendu | Où l’obtenir |
| --- | --- |
| `IPC par grandes divisions - mensuel (Base 100 _ 2017).xlsx` | HCP, indicateurs IPC, grandes divisions, mensuel |
| `IPC par divisions - mensuel (groupe 1) (Base 100 _ 2017).xlsx` | HCP, indicateurs IPC, divisions groupe 1, mensuel |
| `IPC par divisions - mensuel (groupe 2) (Base 100 _ 2017).xlsx` | HCP, indicateurs IPC, divisions groupe 2, mensuel |
| `Tabulation Rapport Enquête Nationale sur le Niveau de Vie des Ménages 2022-2023.xlsx` | Page du rapport ENNVM, rubrique « Télécharger Tabulation Rapport ENNVM 2022-2023 » |

Les intitulés de navigation ci-dessus renvoient aux pages HCP citées dans la section précédente. Le classeur annuel détaillé « Biens & services divers » est disponible sur la page des indicateurs. Il sert à documenter des recoupements de catégories et reste facultatif pour l’exécution des scripts.

Les fichiers IPC attendus correspondent à l’édition se terminant en octobre 2026, avec les en-têtes à la ligne 24. Les téléchargements du HCP peuvent être actualisés. Si les fichiers proposés couvrent d’autres mois ou si leurs valeurs ont été révisées, obtenir l’édition correspondante pour reproduire exactement les résultats. Un échec du contrôle du calendrier signale un fichier hors du périmètre de cette étude.

Les classeurs et les CSV de travail sont conservés localement. Le dépôt conserve les analyses, les graphiques et la présentation académique avec attribution des sources. Le HCP autorise en principe la réutilisation de ses indicateurs selon les conditions CC BY 4.0, sauf mention contraire, avec attribution et indication des transformations. Les conditions générales ne valent pas confirmation d’une licence pour chaque classeur. [Conditions d’utilisation du HCP](https://www.hcp.ma/Conditions-generales-d-utilisation-Version-1-0_a2194.html)

## Organisation

| Chemin | Rôle |
| --- | --- |
| `src/` | Extraction et contrôle des séries IPC et des profils ENNVM |
| `data/raw/` et `data/processed/` | Classeurs locaux du HCP et CSV produits par le nettoyage |
| `notebooks/` | Six étapes d’analyse, avec les résultats enregistrés des étapes exécutées |
| `outputs/` et `outputs/robustesse/` | Graphiques du projet et tableaux CSV régénérés localement |
| `app.py` et `test_simulation.py` | Tableau de bord Streamlit et tests de cohérence |
| `report/latex/` | Rapport de 42 pages, sources LaTeX, bibliographie, tableaux et figures |

| Notebook | Contenu |
| --- | --- |
| [01 – Exploration](notebooks/01_exploration_inflation.ipynb) | Trame d’import, de nettoyage et d’exploration. L’entrée est à configurer pour une série à un mois par ligne. |
| [02 – Analyse statistique](notebooks/02_analyse_statistique_inflation.ipynb) | Statistiques, niveaux, taux mensuels, glissements annuels et comparaisons entre divisions. |
| [03 – Budgets des ménages](notebooks/03_impact_inflation_menages.ipynb) | Profils, correspondance ENNVM–IPC et mesures de couverture. |
| [04 – Simulations d’inflation](notebooks/04_simulations_inflation.ipynb) | Coûts à poids fixes aux prix historiques, hausse uniforme et choc alimentaire additionnel. |
| [05 – Pouvoir d’achat](notebooks/05_pouvoir_achat_scenarios.ipynb) | Variation des unités du sous-panier sous quatre hypothèses de ressources nominales. |
| [06 – Robustesse](notebooks/06_analyse_robustesse.ipynb) | Sensibilité aux dates de référence, aux périmètres et à deux variantes de pondération alimentaire. |

## Reproduire les analyses

Depuis la racine, sous PowerShell, avec une installation de Python accessible par `python` :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force -Path data/raw,data/processed
```

Une fois les fichiers HCP déposés dans `data/raw/`, exécuter :

```powershell
.\.venv\Scripts\python.exe src/clean_ipc.py
.\.venv\Scripts\python.exe src/clean_households.py
.\.venv\Scripts\python.exe -m jupyterlab
```

Exécuter les notebooks **02 à 06 dans l’ordre**. Le notebook 01 est facultatif. Pour le configurer sur la table préparée, sélectionner `data/processed/`, `ipc_maroc_mensuel.csv`, la colonne `date`, la colonne `Indice Général`, le format `%Y-%m-%d` et le séparateur `,`. Le notebook 04 génère les CSV de référence, le 05 produit les scénarios de ressources et le 06 écrit dans `outputs/robustesse/`. Les analyses utilisent les chemins du projet et peuvent démarrer depuis la racine ou depuis `notebooks/`. Une reproduction réécrit les exports correspondants. Pour garder intacts les exports déjà présents, reproduire dans une copie de travail.

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_simulation
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Ouvrir `http://127.0.0.1:8501`. L’application lit les CSV préparés et les exports des notebooks 04 et 05.

### Rapport LaTeX

Le [rapport compilé](report/latex/main.pdf) peut être lu directement. Pour compiler les sources, installer une distribution LaTeX avec pdfLaTeX, BibTeX et les paquets usuels, dont Latin Modern, Babel français et Hyperref. Les figures nécessaires sont déjà présentes. Compléter les champs étudiant, encadrant et année universitaire dans `main.tex` si nécessaire.

```powershell
Push-Location report/latex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
bibtex main
pdflatex -halt-on-error -interaction=nonstopmode main.tex
pdflatex -halt-on-error -interaction=nonstopmode main.tex
Pop-Location
```

## Résultats et limites

- Sur la période étudiée, la plus forte hausse mensuelle de l’IPC général est de **1,79 % en mars 2022**, et le pic en glissement annuel est de **10,08 % en février 2023**.
- De septembre 2022 à octobre 2026, le coût du sous-panier de l’ensemble national augmente de **9,22 % dans le prudent** et de **7,85 % dans l’élargi**, pour des couvertures de **41,4 %** et **93,2 %**.
- Sur un budget illustratif de 5 000 MAD, le choc alimentaire marginal ajoute **263,55 MAD pour Rural C1**, contre **129,15 MAD pour Urbain C5**, avec les poids publiés. Ce classement tient sous les variantes testées. Le classement historique des deux périmètres dépend de la fenêtre étudiée.

Les indices de prix sont à collecte urbaine et sont appliqués à tous les profils. Les comparaisons rurales mesurent une exposition sous prix communs. Les ressources nominales sont hypothétiques, les poids restent fixes et les substitutions ne sont pas estimées. Une variation du coût des postes couverts ou des unités accessibles d’un sous-panier ne mesure pas le pouvoir d’achat effectif du budget entier.
