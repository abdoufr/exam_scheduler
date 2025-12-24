# Univ Exam Planner

Système d'optimisation des emplois du temps d'examens universitaires.

## Prérequis

- Python 3.8+
- PostgreSQL (Optionnel pour la démo, requis pour la production)

## Installation

1.  **Cloner le projet** (si ce n'est pas déjà fait) :
    ```bash
    git clone <votre-url-repo>
    cd exam_scheduler
    ```

2.  **Installer les dépendances** :
    ```bash
    pip install -r requirements.txt
    ```

## Initialisation de la Base de Données

Le projet peut fonctionner avec SQLite (par défaut pour la démo) ou PostgreSQL.

Pour générer des données de test (étudiants, profs, modules...) :

```bash
python seed.py
```
Cela créera un fichier `exams.db` localement.

Pour créer le schéma sur PostgreSQL, utilisez le fichier `schema.sql` :
```bash
psql -U votre_user -d votre_db -f schema.sql
```

## Lancer l'Application

```bash
streamlit run app.py
```

## Fonctionnalités

- **Génération automatique** des plannings via une heuristique gloutonne.
- **Détection des conflits** (étudiants ayant 2 examens en même temps).
- **Tableaux de bord** pour l'administration et les départements.
