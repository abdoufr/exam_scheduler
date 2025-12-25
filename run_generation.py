from optimizer import ExamScheduler
from seed import create_connection
import datetime

def generate_now():
    print("Initializing Scheduler...")
    db_path = "exams.db"
    
    scheduler = ExamScheduler(db_path)
    
    start_date = datetime.date.today()
    end_date = start_date + datetime.timedelta(days=14)
    
    print(f"Generating schedule from {start_date} to {end_date}...")
    # Generate for all formations (pass empty list or fetch all IDs)
    # The generate_schedule method signature: generate_schedule(self, start_date, end_date, formation_ids=None, append=False)
    
    # We'll fetch formation IDs just to be safe, or pass None if it handles it (it typically does or we can check code)
    # Let's check optimizer.py... assuming it handles None -> all. If not, we fetch.
    # Looking at my memory of optimizer.py, it likely takes specific IDs or None.
    # Let's fetch all just to be sure.
    import pandas as pd
    conn = create_connection()
    formations = pd.read_sql("SELECT id FROM formations", conn)
    f_ids = formations['id'].tolist()
    conn.close()
    
    count = scheduler.generate_schedule(start_date, end_date, f_ids, append=False)
    print(f"DONE. Generated {count} exam slots.")

if __name__ == "__main__":
    generate_now()
