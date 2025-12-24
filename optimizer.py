import sqlite3
import pandas as pd
import datetime

class ExamScheduler:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_data(self):
        # Fetch necessary data
        self.modules = pd.read_sql("SELECT * FROM modules", self.conn)
        self.rooms = pd.read_sql("SELECT * FROM lieux_examen", self.conn)
        self.profs = pd.read_sql("SELECT * FROM professeurs", self.conn)
        self.enrollments = pd.read_sql("SELECT * FROM inscriptions", self.conn)
        # Count students per module
        self.module_counts = self.enrollments.groupby('module_id').size().to_dict()

    def check_conflict(self, schedule, student_enrollments, date, time_slot):
        # A simple check: ensure no student has an exam at this slot
        # This requires tracking which student is in which scheduled exam
        # For prototype speed: we check if any student taking THIS module 
        # is already in another exam at THIS slot.
        return False # Placeholder for complex logic

    def generate_schedule(self, start_date, days=5):
        self.get_data()
        
        schedule = [] # List of tuples (module_id, room_id, prof_id, date, slot)
        
        # Exam slots per day: 08:30-10:00, 10:30-12:00, 13:00-14:30, 15:00-16:30
        slots = [
            ("08:30", "10:00"),
            ("10:30", "12:00"),
            ("13:00", "14:30"),
            ("15:00", "16:30")
        ]
        
        current_date = start_date
        slot_idx = 0
        
        sorted_modules = sorted(self.modules['id'].tolist(), key=lambda x: self.module_counts.get(x, 0), reverse=True)
        
        for module_id in sorted_modules:
            nb_students = self.module_counts.get(module_id, 0)
            if nb_students == 0:
                continue
                
            assigned = False
            
            # Try to find a slot
            # In a real constraint solver, we would use ortools. 
            # Here: Greedy approach
            
            # Simple heuristic: Just pick the next available slot/room that fits
            for day_offset in range(days):
                check_date = current_date + datetime.timedelta(days=day_offset)
                
                for start_time, end_time in slots:
                    # Find a room
                    fitting_rooms = self.rooms[self.rooms['capacite'] >= nb_students]
                    
                    if fitting_rooms.empty:
                        # Split module not handled in this simple prototype
                        print(f"Warning: No single room fits {nb_students} students for module {module_id}")
                        continue
                        
                    for _, room in fitting_rooms.iterrows():
                        room_id = room['id']
                        
                        # Check if room is free at this slot
                        is_room_free = True
                        for s in schedule:
                            if s['date'] == str(check_date) and s['start'] == start_time and s['room_id'] == room_id:
                                is_room_free = False
                                break
                        
                        if is_room_free:
                            # Assign
                            # Ideally pick a prof who is free
                            prof_id = self.profs.iloc[0]['id'] # simplistic assignment
                            
                            schedule.append({
                                'module_id': module_id,
                                'room_id': room_id,
                                'prof_id': prof_id,
                                'date': str(check_date),
                                'start': start_time,
                                'end': end_time
                            })
                            assigned = True
                            print(f"Assigned Module {module_id} to {room['nom']} on {check_date} {start_time}")
                            break
                    if assigned:
                        break
                if assigned:
                    break
            
            if not assigned:
                print(f"Could not assign module {module_id}")

        self.save_schedule(schedule)
        return len(schedule)

    def save_schedule(self, schedule):
        self.cursor.execute("DELETE FROM examens")
        for s in schedule:
            self.cursor.execute("""
                INSERT INTO examens (module_id, prof_surveillant_id, salle_id, date_examen, creneau_debut, creneau_fin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (s['module_id'], s['prof_id'], s['room_id'], s['date'], s['start'], s['end']))
        self.conn.commit()

if __name__ == "__main__":
    # Test
    scheduler = ExamScheduler("exams.db")
    scheduler.generate_schedule(datetime.date.today())
