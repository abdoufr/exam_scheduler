import sqlite3
import pandas as pd

def verify():
    conn = sqlite3.connect("exams.db")
    depts = pd.read_sql("SELECT d.nom, COUNT(f.id) as specs FROM departements d JOIN formations f ON d.id = f.dept_id GROUP BY d.nom", conn)
    print("Faculties and Specialty count:")
    print(depts)
    
    count = pd.read_sql("SELECT COUNT(*) as count FROM etudiants", conn)
    print(f"\nTotal Students: {count['count'][0]}")
    
    modules = pd.read_sql("SELECT m.nom FROM modules m JOIN formations f ON m.formation_id = f.id WHERE f.nom = 'Licence Droit Public' LIMIT 5", conn)
    print("\nSample modules for Droit Public:")
    print(modules)
    
    conn.close()

if __name__ == "__main__":
    verify()
