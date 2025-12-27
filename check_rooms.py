import sqlite3
import pandas as pd

def check_rooms():
    conn = sqlite3.connect("exams.db")
    rooms = pd.read_sql("SELECT type, COUNT(*), AVG(capacite) as avg_cap FROM lieux_examen GROUP BY type", conn)
    print("Room types in database:")
    print(rooms)
    
    all_rooms = pd.read_sql("SELECT * FROM lieux_examen", conn)
    print("\nAll rooms sample:")
    print(all_rooms.head(10))
    
    conn.close()

if __name__ == "__main__":
    check_rooms()
