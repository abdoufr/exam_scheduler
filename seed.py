# =========================================================================
# GENERATEUR DE DONNEES REALISTES - UMBB
# Responsable de l'initialisation de la base de données avec 2500 étudiants
# =========================================================================

import sqlite3
import random
import datetime

# --- CONFIGURATION ---
NUM_STUDENTS = 2500       # Nombre total d'étudiants à simuler
NUM_PROFS = 200          # Nombre de professeurs surveillants
NUM_ROOMS_SMALL = 60      # Salles de classe (Capacité 20)
NUM_ROOMS_LARGE = 15      # Amphithéâtres (Capacité 150-200)
DB_NAME = "exams.db"

# Listes de noms réalistes (Contexte Algérien)
LAST_NAMES = [
    "Benali", "Saidi", "Djebbar", "Moussaoui", "Belkacem", "Brahimi", "Rahmani", "Touati", 
    "Zerrouki", "Boukhalfa", "Hamdi", "Amrani", "Slimani", "Dahmani", "Mezerai", 
    "Haddad", "Kherroubi", "Bouziane", "Mebarki", "Ouali", "Cherifi", "Mansouri", "Ayad",
    "Bouchareb", "Louanchi", "Sifi", "Derbal", "Ziane", "Mokhtari", "Guenane", "Hadjadj",
    "Khelifi", "Abed", "Yahia", "Bouzid", "Mekki", "Soudani"
]
FIRST_NAMES_M = [
    "Mohamed", "Amine", "Yacine", "Karim", "Walid", "Sofiane", "Adel", "Bilal", "Youcef",
    "Samir", "Nabil", "Hichem", "Fares", "Lotfi", "Mehdi", "Abdenour", "Ryad", "Hakim",
    "Khaled", "Mourad", "Tarek", "Zinedine", "Hamza", "Sidali", "Abderrahmane", "Ilyes"
]
FIRST_NAMES_F = [
    "Sarah", "Lydia", "Meriem", "Amel", "Yasmine", "Imene", "Rania", "Sabrina", "Hanane",
    "Nesrine", "Kenza", "Manel", "Melissa", "Chanez", "Nawel", "Fatima", "Zahra", "Leila",
    "Amina", "Safia", "Bouchra", "Asma", "Souad", "Karima", "Fella", "Nour", "Ines"
]

def create_connection():
    """Crée une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db(conn):
    """Initialise la structure de la base de données (Nettoyage et Création)."""
    cursor = conn.cursor()
    # Suppression des tables existantes pour repartir à zéro
    cursor.executescript("""
        DROP TABLE IF EXISTS examen_etudiants;
        DROP TABLE IF EXISTS examens;
        DROP TABLE IF EXISTS inscriptions;
        DROP TABLE IF EXISTS modules;
        DROP TABLE IF EXISTS etudiants;
        DROP TABLE IF EXISTS formations;
        DROP TABLE IF EXISTS professeurs;
        DROP TABLE IF EXISTS lieux_examen;
        DROP TABLE IF EXISTS departements;

        -- Création des tables selon le schéma défini
        CREATE TABLE departements (id INTEGER PRIMARY KEY, nom TEXT);
        CREATE TABLE formations (id INTEGER PRIMARY KEY, nom TEXT, dept_id INTEGER);
        CREATE TABLE professeurs (id INTEGER PRIMARY KEY, nom TEXT, prenom TEXT, dept_id INTEGER);
        CREATE TABLE etudiants (id INTEGER PRIMARY KEY, nom TEXT, prenom TEXT, formation_id INTEGER, promo TEXT);
        CREATE TABLE modules (id INTEGER PRIMARY KEY, nom TEXT, credits INTEGER, formation_id INTEGER, sem INTEGER);
        CREATE TABLE lieux_examen (id INTEGER PRIMARY KEY, nom TEXT, capacite INTEGER, type TEXT);
        CREATE TABLE inscriptions (etudiant_id INTEGER, module_id INTEGER, note REAL);
        CREATE TABLE examens (
            id INTEGER PRIMARY KEY, 
            module_id INTEGER, 
            prof_surveillant_id INTEGER, 
            salle_id INTEGER, 
            date_examen TEXT, 
            creneau_debut TEXT, 
            creneau_fin TEXT
        );
        CREATE TABLE examen_etudiants (
            examen_id INTEGER,
            etudiant_id INTEGER,
            seat_number INTEGER,
            PRIMARY KEY (examen_id, etudiant_id)
        );
    """)
    conn.commit()

def generate_data(conn):
    """Génère les données de test (UMBB) : Facultés, Modules, Profs, Étudiants."""
    cursor = conn.cursor()
    
    # --- 1. Structure Réelle de l'UMBB (Facultés et Spécialités) ---
    umbb_structure = {
        "Faculté des Sciences (FS)": {
            "Licence Informatique": ["Algorithmique 1", "Analyse 1", "Architecture", "BDD", "Sys. Exploit", "Réseaux", "Web Dev", "Logique Math"],
            "Licence Mathématiques": ["Algèbre 1", "Analyse Réelle", "Probabilités", "Analyse Numérique", "Optimisation", "Topologie", "Mesure et Intégration"],
            "Master Data Science": ["Machine Learning", "Big Data", "Visualisation", "Deep Learning", "Ethique IA", "NLP", "Cloud Computing"]
        },
        "Faculté de Technologie (FT)": {
            "Licence Génie Mécanique": ["Thermodynamique", "Méc. Solide", "RDM", "Méc. Fluides", "Construction Méc.", "Vibrations", "Fab. Assistée"],
            "Licence Génie Civil": ["Béton Armé", "Géotechnique", "Statique", "Hydraulique", "Topographie", "Matériaux", "Ponts"],
            "Master Automatique": ["Commande Robuste", "Ident. Systèmes", "Robotique", "Automates", "Capteurs", "Vision Artificielle"]
        },
        "Faculté FHC": {
            "Licence Forage": ["Forage", "Méc. Pétrole", "Fluides", "Equipements", "Géologie Pétrolière", "Sécurité Ind."],
            "Licence Procédés": ["Transfert Chaleur", "Cinétique", "Opérations", "Raffinage", "Thermodynamique Chim.", "Polymères"]
        },
        "Faculté FSESGC": {
            "Licence Eco": ["Microéco", "Macroéco", "Hist. Eco", "Stat. Desc.", "Math Fin.", "Comptabilité Nat."],
            "Licence Gestion": ["Management", "Compta Générale", "Marketing", "GRH", "Fiscalité", "Stratégie Entr.", "Droit des Affaires"]
        },
        "Faculté de Droit": {
            "Licence Public": ["Droit Constit.", "Droit Admin.", "Libertés", "Rel. Internat.", "Finances Pub.", "Droit Environnement"],
            "Licence Privé": ["Droit Civil", "Droit Pénal", "Droit Comm.", "Famille", "Travail", "Assurances"]
        },
        "Faculté Lettres": {
            "Licence Anglais": ["Linguistics", "Brit. Lit", "Amer. Civ", "Oral Exp.", "Writing", "Phonetics", "Translation"],
            "Licence Français": ["Linguistique", "Litt. Franco", "Grammaire", "Phonétique", "Technique Redac.", "Civilisation"]
        },
        "Institut IGEE": {
            "B.Sc. Comp Eng": ["Digital Sys", "Comp Arch", "OOP", "Microproc", "Signals", "Circuits", "Electronics"]
        }
    }
    
    all_formations = [] 
    
    # Insertion des Facultés, Formations et Modules
    for fac_name, specs in umbb_structure.items():
        cursor.execute("INSERT INTO departements (nom) VALUES (?)", (fac_name,))
        fac_id = cursor.lastrowid
        
        for spec_name, modules_list in specs.items():
            cursor.execute("INSERT INTO formations (nom, dept_id) VALUES (?, ?)", (spec_name, fac_id))
            f_id = cursor.lastrowid
            all_formations.append(f_id)
            
            for m_name in modules_list:
                cursor.execute("INSERT INTO modules (nom, credits, formation_id, sem) VALUES (?, ?, ?, ?)", 
                               (m_name, random.randint(3, 6), f_id, random.choice([1, 2])))
            
    conn.commit()

    # --- 2. Professeurs ---
    fac_ids = [row[0] for row in cursor.execute("SELECT id FROM departements").fetchall()]
    for _ in range(NUM_PROFS):
        nom = random.choice(LAST_NAMES)
        prenom = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
        cursor.execute("INSERT INTO professeurs (nom, prenom, dept_id) VALUES (?, ?, ?)",
                       (nom, prenom, random.choice(fac_ids)))
    
    # --- 3. Étudiants et Inscriptions ---
    # Distribution aléatoire des 2500 étudiants à travers les spécialités
    for _ in range(NUM_STUDENTS):
        f_id = random.choice(all_formations)
        nom = random.choice(LAST_NAMES)
        prenom = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
        
        cursor.execute("INSERT INTO etudiants (nom, prenom, formation_id, promo) VALUES (?, ?, ?, ?)",
                       (nom, prenom, f_id, "L3"))
        s_id = cursor.lastrowid
        
        # Inscrire l'étudiant à TOUS les modules de sa formation
        f_modules = cursor.execute("SELECT id FROM modules WHERE formation_id = ?", (f_id,)).fetchall()
        for m in f_modules:
            cursor.execute("INSERT INTO inscriptions (etudiant_id, module_id) VALUES (?, ?)", (s_id, m[0]))
            
    conn.commit()

    # --- 4. Lieux d'examen (Salles et Amphis) ---
    for i in range(NUM_ROOMS_SMALL):
        cursor.execute("INSERT INTO lieux_examen (nom, capacite, type) VALUES (?, ?, ?)",
                       (f"Salle {i+1:02d}", 20, 'Salle'))
    
    for i in range(NUM_ROOMS_LARGE):
        cursor.execute("INSERT INTO lieux_examen (nom, capacite, type) VALUES (?, ?, ?)",
                       (f"Amphi {chr(65+i)}", random.choice([150, 200]), 'Amphi'))
        
    conn.commit()
    print("Database seeded realistically for UMBB (2500 students distributed).")

if __name__ == "__main__":
    conn = create_connection()
    init_db(conn)
    generate_data(conn)
    conn.close()

if __name__ == "__main__":
    conn = create_connection()
    init_db(conn)
    generate_data(conn)
    conn.close()
