import sqlite3
import random
from faker import Faker
import datetime

fake = Faker('fr_FR')

# Configuration
NUM_DEPTS = 7
NUM_STUDENTS = 200  # Small for demo speed (User asked for 13k scale, but we start small for dev)
NUM_PROFS = 50
NUM_ROOMS = 10

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
    
    # 1. Departments
    depts = [f"Dept {fake.word().capitalize()}" for _ in range(NUM_DEPTS)]
    for d in depts:
        cursor.execute("INSERT INTO departements (nom) VALUES (?)", (d,))
    conn.commit()
    print(f"Generated {NUM_DEPTS} departments.")

    # 2. Formations
    dept_ids = [row[0] for row in cursor.execute("SELECT id FROM departements").fetchall()]
    formations = []
    for d_id in dept_ids:
        # 2 formations per dept
        for _ in range(2):
            f_name = f"Licence {fake.job()}"
            cursor.execute("INSERT INTO formations (nom, dept_id) VALUES (?, ?)", (f_name, d_id))
            formations.append(cursor.lastrowid)
    conn.commit()
    print(f"Generated {len(formations)} formations.")

    # 3. Modules
    modules = []
    for f_id in formations:
        # 6 modules per formation
        for i in range(6):
            m_name = f"Module {fake.bs().split()[0]} {i+1}"
            cursor.execute("INSERT INTO modules (nom, credits, formation_id, sem) VALUES (?, ?, ?, ?)", 
                           (m_name, random.randint(2, 6), f_id, random.choice([1, 2, 3, 4, 5, 6])))
            modules.append(cursor.lastrowid)
    conn.commit()
    print(f"Generated {len(modules)} modules.")

    # 4. Professors
    profs = []
    for _ in range(NUM_PROFS):
        cursor.execute("INSERT INTO professeurs (nom, prenom, dept_id) VALUES (?, ?, ?)",
                       (fake.last_name(), fake.first_name(), random.choice(dept_ids)))
        profs.append(cursor.lastrowid)
    conn.commit()
    print(f"Generated {NUM_PROFS} professors.")

    # 5. Students & Inscriptions
    students = []
    for _ in range(NUM_STUDENTS):
        f_id = random.choice(formations)
        cursor.execute("INSERT INTO etudiants (nom, prenom, formation_id, promo) VALUES (?, ?, ?, ?)",
                       (fake.last_name(), fake.first_name(), f_id, f"L{random.randint(1,3)}"))
        s_id = cursor.lastrowid
        students.append(s_id)
        
        # Register student to all modules of their formation
        f_modules = cursor.execute("SELECT id FROM modules WHERE formation_id = ?", (f_id,)).fetchall()
        for m in f_modules:
            cursor.execute("INSERT INTO inscriptions (etudiant_id, module_id) VALUES (?, ?)", (s_id, m[0]))
            
    conn.commit()
    print(f"Generated {NUM_STUDENTS} students and their inscriptions.")

    # 6. Rooms
    types = ['Amphi', 'Salle', 'Labo']
    for i in range(NUM_ROOMS):
        r_type = random.choice(types)
        cap = random.choice([20, 30, 40, 100, 200]) if r_type == 'Amphi' else random.choice([20, 30])
        cursor.execute("INSERT INTO lieux_examen (nom, capacite, type) VALUES (?, ?, ?)",
                       (f"{r_type} {i+1}", cap, r_type))
    conn.commit()
    print(f"Generated {NUM_ROOMS} rooms.")

if __name__ == "__main__":
    conn = create_connection()
    init_db(conn)
    generate_data(conn)
    conn.close()
    print("Database seeded successfully: exams.db")
