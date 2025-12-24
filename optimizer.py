import sqlite3
import pandas as pd
import datetime

class ExamScheduler:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_data(self):
        # Fetch modules with their department IDs for prioritization
        self.modules = pd.read_sql("""
            SELECT m.*, f.dept_id 
            FROM modules m 
            JOIN formations f ON m.formation_id = f.id
        """, self.conn)
        self.rooms = pd.read_sql("SELECT * FROM lieux_examen", self.conn)
        self.profs = pd.read_sql("SELECT * FROM professeurs", self.conn)
        self.enrollments = pd.read_sql("SELECT * FROM inscriptions", self.conn)
        # Count students per module
        self.module_counts = self.enrollments.groupby('module_id').size().to_dict()
        # Map module to list of students for conflict checking
        self.module_students = self.enrollments.groupby('module_id')['etudiant_id'].apply(list).to_dict()

    def check_conflict(self, schedule, student_enrollments, date, time_slot):
        # A simple check: ensure no student has an exam at this slot
        # This requires tracking which student is in which scheduled exam
        # For prototype speed: we check if any student taking THIS module 
        # is already in another exam at THIS slot.
        return False # Placeholder for complex logic

    def generate_schedule(self, start_date, end_date, formation_ids=None, append=False):
        self.get_data()
        
        # Load existing exams to avoid conflicts
        existing_exams = pd.read_sql("SELECT * FROM examens", self.conn)
        
        # Trackers for constraints
        prof_total_load = {pid: 0 for pid in self.profs['id'].tolist()}
        student_daily_exam = {} # (student_id, date) -> bool
        
        # Current internal schedule (initially empty or existing for conflict checks)
        internal_schedule = []
        
        # Populate trackers from existing exams
        for _, ex in existing_exams.iterrows():
            date_str = str(ex['date_examen'])
            pid = ex['prof_surveillant_id']
            mid = ex['module_id']
            # Find students for this module
            students = self.module_students.get(mid, [])
            
            prof_total_load[pid] = prof_total_load.get(pid, 0) + 1
            for sid in students:
                student_daily_exam[(sid, date_str)] = True
            
            internal_schedule.append({
                'date': date_str,
                'start': ex['creneau_debut'],
                'room_id': ex['salle_id'],
                'prof_id': pid,
                'module_id': mid
            })

        new_exams = []
        
        # Calculate duration in days
        delta = (end_date - start_date).days + 1
        if delta < 1: delta = 1
        
        # Exam slots per day
        slots = [
            ("08:30", "10:00"),
            ("10:30", "12:00"),
            ("13:00", "14:30"),
            ("15:00", "16:30")
        ]
        
        # Filter modules if formations are selected
        all_modules = self.modules
        if formation_ids and len(formation_ids) > 0:
             all_modules = self.modules[self.modules['formation_id'].isin(formation_ids)]
        
        # Sort modules by complexity (student count)
        sorted_modules = sorted(all_modules['id'].tolist(), key=lambda x: self.module_counts.get(x, 0), reverse=True)
        
        for module_id in sorted_modules:
            nb_students = self.module_counts.get(module_id, 0)
            if nb_students == 0: continue
            
            # Skip if module already has an exam (optional, but good for "one by one" logic)
            if any(s['module_id'] == module_id for s in internal_schedule):
                print(f"Module {module_id} already scheduled, skipping.")
                continue

            m_dept_id = self.modules[self.modules['id'] == module_id]['dept_id'].values[0]
            m_students = self.module_students.get(module_id, [])
            assigned = False
            
            # Try each day/slot
            for day_offset in range(delta):
                check_date = start_date + datetime.timedelta(days=day_offset)
                date_str = str(check_date)
                
                # CONSTRAINT: Étudiants : Maximum 1 examen par jour
                student_conflict = False
                for sid in m_students:
                    if student_daily_exam.get((sid, date_str)):
                        student_conflict = True
                        break
                
                if student_conflict: continue
                
                for start_time, end_time in slots:
                    fitting_rooms = self.rooms[self.rooms['capacite'] >= nb_students]
                    for _, room in fitting_rooms.iterrows():
                        room_id = room['id']
                        
                        # Check room availability
                        is_room_free = True
                        for s in internal_schedule:
                            if s['date'] == date_str and s['start'] == start_time and s['room_id'] == room_id:
                                is_room_free = False
                                break
                        
                        if not is_room_free: continue
                        
                        # Pick a professor
                        available_profs = []
                        for _, prof in self.profs.iterrows():
                            pid = prof['id']
                            
                            # Check slot availability
                            if any(s['date'] == date_str and s['start'] == start_time and s['prof_id'] == pid for s in internal_schedule):
                                continue
                            
                            # Check daily limit (Max 3)
                            daily_count = len([s for s in internal_schedule if s['date'] == date_str and s['prof_id'] == pid])
                            if daily_count >= 3: continue
                                
                            available_profs.append(prof)
                        
                        if not available_profs: continue
                        
                        available_profs.sort(key=lambda x: (x['dept_id'] == m_dept_id, -prof_total_load[x['id']]), reverse=True)
                        
                        selected_prof = available_profs[0]
                        pid = selected_prof['id']
                        
                        # ASSIGN
                        exam_obj = {
                            'module_id': module_id,
                            'prof_id': pid,
                            'room_id': room_id,
                            'date': date_str,
                            'start': start_time,
                            'end': end_time
                        }
                        new_exams.append(exam_obj)
                        internal_schedule.append(exam_obj)
                        
                        # Update trackers
                        prof_total_load[pid] += 1
                        for sid in m_students:
                            student_daily_exam[(sid, date_str)] = True
                            
                        assigned = True
                        print(f"Assigned {module_id} on {date_str}")
                        break
                    
                    if assigned: break
                if assigned: break
            
            if not assigned:
                print(f"FAILED to assign module {module_id}")

        self.save_schedule(new_exams, append=append)
        return len(new_exams)

    def save_schedule(self, new_exams, append=False):
        if not append:
            self.cursor.execute("DELETE FROM examens")
            
        for s in new_exams:
            self.cursor.execute("""
                INSERT INTO examens (module_id, prof_surveillant_id, salle_id, date_examen, creneau_debut, creneau_fin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (s['module_id'], s['prof_id'], s['room_id'], s['date'], s['start'], s['end']))
        self.conn.commit()

if __name__ == "__main__":
    # Test
    scheduler = ExamScheduler("exams.db")
    scheduler.generate_schedule(datetime.date.today())
