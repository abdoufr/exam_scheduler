# University Exam Scheduler v2.2.0 🎓

An advanced automated exam scheduling system built with Python, Streamlit, and SQLite.

## ✨ New Features (v2.2.0)
- **Realistic Data**: 2,500 students with authentic Algerian names.
- **Explicit Assignment**: Students are assigned to specific rooms (max 20 capacity).
- **Dashboard**: New visualizations for student distribution.

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

### Méthode standard (si Python est dans le PATH)
```bash
streamlit run app.py
```

### Méthode spécifique (PowerShell Windows)
Si la commande ci-dessus ne fonctionne pas, utilisez le chemin complet :
```powershell
& "C:\Program Files\Python311\python.exe" -m streamlit run app.py
```

## Fonctionnalités

- **Génération automatique** des plannings via une heuristique gloutonne.
- **Détection des conflits** (étudiants ayant 2 examens en même temps).
- **Tableaux de bord** pour l'administration et les départements.
