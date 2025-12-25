import sqlite3
import pandas as pd

DB_PATH = "exams.db"

def run_debug():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- 1. Checking Table Counts ---")
    try:
        count_students = cursor.execute("SELECT COUNT(*) FROM etudiants").fetchone()[0]
        count_exams = cursor.execute("SELECT COUNT(*) FROM examens").fetchone()[0]
        count_links = cursor.execute("SELECT COUNT(*) FROM examen_etudiants").fetchone()[0]
        
        print(f"Students: {count_students}")
        print(f"Exams: {count_exams}")
        print(f"Student-Exam Links: {count_links}")
        
        if count_links == 0:
            print("CRITICAL: 'examen_etudiants' table is EMPTY. The scheduler might not be saving assignments.")
            conn.close()
            return
    except Exception as e:
        print(f"Error checking counts: {e}")
        conn.close()
        return

    print("\n--- 2. Checking Sample Data ---")
    # Get a sample exam that has assignments (if any)
    sample = pd.read_sql("""
        SELECT e.id, e.date_examen, m.nom as module, m.formation_id
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN examen_etudiants ee ON e.id = ee.examen_id
        LIMIT 1
    """, conn)
    
    if sample.empty:
        print("No exams found with student assignments.")
    else:
        print("Sample Exam with Students:")
        print(sample.to_string())
        
        exam_id = sample.iloc[0]['id']
        date_str = sample.iloc[0]['date_examen']
        mod_name = sample.iloc[0]['module']
        
        print(f"\n--- 3. Simulating App Query for Exam ID {exam_id} ({mod_name} on {date_str}) ---")
        
        # Simulate the query used in 'Répartition Salles'
        # First, find the module ID
        mod_id_query = f"SELECT id FROM modules WHERE nom = '{mod_name}'"
        mod_id = pd.read_sql(mod_id_query, conn).iloc[0]['id']
        print(f"Module ID: {mod_id}")
        
        query = f"""
            SELECT s.nom as Salle, s.capacite, COUNT(ee.etudiant_id) as assigned_count,
                   e.id as exam_id
            FROM examens e
            JOIN lieux_examen s ON e.salle_id = s.id
            LEFT JOIN examen_etudiants ee ON e.id = ee.examen_id
            WHERE e.module_id = {mod_id} AND e.date_examen = '{date_str}'
            GROUP BY s.nom
        """
        print("Query:")
        print(query)
        
        results = pd.read_sql(query, conn)
        print("\nResults:")
        print(results.to_string())
        
        # Check specific room students
        if not results.empty:
            first_exam_id = results.iloc[0]['exam_id']
            print(f"\nChecking students for specific Room Exam ID: {first_exam_id}")
            stu_query = f"""
                SELECT et.nom, et.prenom
                FROM examen_etudiants ee
                JOIN etudiants et ON ee.etudiant_id = et.id
                WHERE ee.examen_id = {first_exam_id}
                LIMIT 5
            """
            stus = pd.read_sql(stu_query, conn)
            print(stus)

    conn.close()

if __name__ == "__main__":
    run_debug()
