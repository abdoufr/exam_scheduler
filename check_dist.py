import sqlite3
import pandas as pd

def check_exam_distribution():
    conn = sqlite3.connect("exams.db")
    distribution = pd.read_sql("""
        SELECT r.type, COUNT(e.id) as exam_count, AVG(r.capacite) as avg_cap
        FROM examens e
        JOIN lieux_examen r ON e.salle_id = r.id
        GROUP BY r.type
    """, conn)
    print("Exam distribution by room type:")
    print(distribution)
    
    # Check if there are any unassigned modules
    # (Examens table only has assigned ones)
    
    conn.close()

if __name__ == "__main__":
    check_exam_distribution()
