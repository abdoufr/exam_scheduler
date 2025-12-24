import sqlite3
import random
from faker import Faker
import datetime

fake = Faker('fr_FR')

# Configuration
NUM_DEPTS = 7
NUM_STUDENTS = 600
NUM_PROFS = 100
NUM_ROOMS = 30

DB_NAME = "exams.db"

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db(conn):
    cursor = conn.cursor()
    # SQL compatible with SQLite for the demo
    cursor.executescript("""
        DROP TABLE IF EXISTS examens;
        DROP TABLE IF EXISTS inscriptions;
        DROP TABLE IF EXISTS modules;
        DROP TABLE IF EXISTS etudiants;
        DROP TABLE IF EXISTS formations;
        DROP TABLE IF EXISTS professeurs;
        DROP TABLE IF EXISTS lieux_examen;
        DROP TABLE IF EXISTS departements;

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
    """)
    conn.commit()

def generate_data(conn):
    cursor = conn.cursor()
    
    # --- 1. Real UMBB Faculties & Their Specialties ---
    umbb_structure = {
        "Faculté des Sciences (FS)": {
            "Licence Informatique": ["Algorithmique 1", "Analyse 1", "Architecture des Ordinateurs", "Bases de Données 1", "Systèmes d'Exploitation 1", "Réseaux Locaux"],
            "Licence Mathématiques": ["Algèbre 1", "Analyse Réelle", "Probabilités", "Analyse Numérique", "Optimisation"],
            "Master Data Science": ["Machine Learning", "Big Data", "Visualisation de Données", "Deep Learning", "Ethique de l'IA"]
        },
        "Faculté de Technologie (FT)": {
            "Licence Génie Mécanique": ["Thermodynamique", "Mécanique du Solide", "Résistance des Matériaux", "Méc. des Fluides", "Construction Mécanique"],
            "Licence Génie Civil": ["Béton Armé", "Géotechnique", "Statique des Constructions", "Hydraulique Appliquée", "Topographie"],
            "Master Automatique": ["Commande Robuste", "Identification des Systèmes", "Robotique Industrielle", "Automates Programmables"]
        },
        "Faculté des Hydrocarbures et de la Chimie (FHC)": {
            "Licence Forage et Mécanique": ["Technologie de Forage", "Mécanique des Chantiers Pétroliers", "Fluides de Forage", "Equipements de Forage"],
            "Master Transport des Hydrocarbures": ["Réseaux de Transport", "Pompes et Compresseurs", "Corrosion et Protection", "Stockage et Distribution"],
            "Licence Génie des Procédés": ["Transfert de Chaleur", "Cinétique Chimique", "Opérations Unitaires", "Raffinage des Hydrocarbures"]
        },
        "Faculté des Sc. Économiques (FSESGC)": {
            "Licence Sciences Économiques": ["Microéconomie 1", "Macroéconomie 1", "Histoire des Faits Économiques", "Statistique Descriptive"],
            "Licence Sciences de Gestion": ["Management Général", "Comptabilité Générale", "Marketing de Base", "Gestion des Ressources Humaines"],
            "Master Finance et Comptabilité": ["Audit Financier", "Comptabilité Approfondie", "Finance de Marché", "Fiscalité des Entreprises"]
        },
        "Faculté de Droit": {
            "Licence Droit Public": ["Droit Constitutionnel", "Droit Administratif", "Libertés Publiques", "Relations Internationales"],
            "Licence Droit Privé": ["Droit Civil (Obligations)", "Droit Pénal Général", "Droit Commercial", "Droit de la Famille"]
        },
        "Faculté des Lettres et des Langues": {
            "Licence Anglais": ["Linguistics", "British Literature", "American Civilization", "Oral Expression", "Academic Writing"],
            "Licence Français": ["Linguistique Française", "Littérature Francophone", "Grammaire de la Phrase", "Phonétique et Phonologie"],
            "Licence Langue Arabe": ["Littérature Arabe Classique", "Grammaire Arabe", "Rhétorique", "Critique Littéraire"]
        },
        "Institut de Génie Électrique (IGEE)": {
            "B.Sc. Computer Engineering": ["Digital Systems", "Computer Architecture", "Object Oriented Programming", "Microprocessors"],
            "M.Sc. Power Engineering": ["Power Systems Analysis", "Renewable Energy", "Smart Grids", "High Voltage Engineering"]
        }
    }
    
    all_formations = [] # list of (id, spec_name, fac_name)
    
    for fac_name, specs in umbb_structure.items():
        # Insert Faculty as Department
        cursor.execute("INSERT INTO departements (nom) VALUES (?)", (fac_name,))
        fac_id = cursor.lastrowid
        
        for spec_name, modules_list in specs.items():
            # Insert Specialty as Formation
            cursor.execute("INSERT INTO formations (nom, dept_id) VALUES (?, ?)", (spec_name, fac_id))
            f_id = cursor.lastrowid
            all_formations.append((f_id, spec_name, fac_name))
            
            # Insert Modules
            for m_name in modules_list:
                cursor.execute("INSERT INTO modules (nom, credits, formation_id, sem) VALUES (?, ?, ?, ?)", 
                               (m_name, random.randint(3, 6), f_id, random.choice([1, 2, 3])))
    
    conn.commit()
    print(f"Generated {len(umbb_structure)} Faculties and {len(all_formations)} Specialties with their curricula.")

    # --- 2. Professors ---
    fac_ids = [row[0] for row in cursor.execute("SELECT id FROM departements").fetchall()]
    for _ in range(NUM_PROFS):
        cursor.execute("INSERT INTO professeurs (nom, prenom, dept_id) VALUES (?, ?, ?)",
                       (fake.last_name(), fake.first_name(), random.choice(fac_ids)))
    
    # --- 3. Students & Inscriptions ---
    for _ in range(NUM_STUDENTS):
        f_id, spec_name, fac_name = random.choice(all_formations)
        cursor.execute("INSERT INTO etudiants (nom, prenom, formation_id, promo) VALUES (?, ?, ?, ?)",
                       (fake.last_name(), fake.first_name(), f_id, f"L{random.randint(1,3)}"))
        s_id = cursor.lastrowid
        
        # Register to all modules of this formation
        f_modules = cursor.execute("SELECT id FROM modules WHERE formation_id = ?", (f_id,)).fetchall()
        for m in f_modules:
            cursor.execute("INSERT INTO inscriptions (etudiant_id, module_id) VALUES (?, ?)", (s_id, m[0]))
            
    conn.commit()
    print(f"Enrolled {NUM_STUDENTS} students across all UMBB programs.")

    # --- 4. Rooms ---
    types = ['Amphi', 'Salle', 'Labo']
    for i in range(NUM_ROOMS):
        r_type = random.choice(types)
        cap = random.choice([150, 200, 300]) if r_type == 'Amphi' else random.choice([30, 40])
        cursor.execute("INSERT INTO lieux_examen (nom, capacite, type) VALUES (?, ?, ?)",
                       (f"{r_type} {i+1:02d}", cap, r_type))
    conn.commit()
    print(f"Generated {NUM_ROOMS} rooms.")

if __name__ == "__main__":
    conn = create_connection()
    init_db(conn)
    generate_data(conn)
    conn.close()
    print("Database seeded successfully: exams.db")
