# =========================================================================
# MOTEUR D'OPTIMISATION DES EXAMENS - UMBB
# Algorithme de planification avec répartition nominative des étudiants
# =========================================================================

import sqlite3
import pandas as pd
import datetime
import random

class ExamScheduler:
    def __init__(self, db_path):
        """Initialisation avec chemin vers la base SQLite."""
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def get_data(self):
        """Charge les données nécessaires (Modules, Salles, Profs, Inscriptions) en mémoire."""
        self.modules = pd.read_sql("""
            SELECT m.*, f.dept_id 
            FROM modules m 
            JOIN formations f ON m.formation_id = f.id
        """, self.conn)
        self.rooms = pd.read_sql("SELECT * FROM lieux_examen", self.conn) 
        self.profs = pd.read_sql("SELECT * FROM professeurs", self.conn)
        
        # Nombre d'étudiants par module pour dimensionner les besoins en salles
        self.module_counts = pd.read_sql("SELECT module_id, COUNT(etudiant_id) as cnt FROM inscriptions GROUP BY module_id", self.conn).set_index('module_id')['cnt'].to_dict()
        
        # Liste complète des IDs étudiants par module
        self.inscriptions = pd.read_sql("SELECT module_id, etudiant_id FROM inscriptions", self.conn)
        self.module_students = self.inscriptions.groupby('module_id')['etudiant_id'].apply(list).to_dict()

    def generate_schedule(self, start_date, end_date, formation_ids=None, append=False):
        """
        Génère l'emploi du temps en équilibrant les charges et en évitant les conflits.
        Contraintes : 1 examen/jour/étudiant, Max 3 surveillances/jour/prof, Respect capacité salles.
        """
        self.get_data()
        existing_exams = pd.read_sql("SELECT * FROM examens", self.conn)
        
        # Trackers d'état pour le respect des contraintes en temps réel
        prof_daily_load = {}     # (ID Prof, Date) -> Compteur
        student_daily_load = {}  # (ID Étudiant, Date) -> Booléen
        room_schedule = {}      # (ID Salle, Date, Créneau) -> Occupé?
        
        # Définition des créneaux horaires standards
        slots = [("08:30", "10:00"), ("10:30", "12:00"), ("13:00", "14:30"), ("15:00", "16:30")]
        
        # Filtrage et tri des modules (Priorité aux plus gros effectifs)
        target_modules = self.modules
        if formation_ids:
            target_modules = target_modules[target_modules['formation_id'].isin(formation_ids)]
        sorted_mids = sorted(target_modules['id'].tolist(), key=lambda x: self.module_counts.get(x, 0), reverse=True)
        
        new_exams = []
        delta_days = (end_date - start_date).days + 1

        for mid in sorted_mids:
            n_students = self.module_counts.get(mid, 0)
            if n_students == 0: continue
            
            m_dept = target_modules[target_modules['id'] == mid]['dept_id'].values[0]
            m_students = self.module_students.get(mid, [])
            
            assigned = False
            
            # Recherche d'un jour disponible
            for day_off in range(delta_days):
                curr_date = start_date + datetime.timedelta(days=day_off)
                d_str = str(curr_date)
                
                # Vérification Conflit Étudiant : S'assurer qu'aucun étudiant n'a déjà un examen ce jour-là
                if any(student_daily_load.get((sid, d_str)) for sid in m_students):
                    continue
                
                # Recherche d'un créneau disponible dans la journée
                for start_t, end_t in slots:
                    # Trouver des salles libres pour ce créneau
                    all_available = [r for _, r in self.rooms.iterrows() if not room_schedule.get((r['id'], d_str, start_t))]
                    
                    # Stratégie de sélection : Priorité aux Amphis uniquement si l'effectif est > 30 (par exemple)
                    # Ou plus simplement, on trie par capacité CROISSANTE pour utiliser les petites salles en priorité
                    # s'ils peuvent contenir le groupe.
                    
                    if n_students > 45: # Si gros effectif, on veut des Amphis en priorité
                        available_rooms = sorted(all_available, key=lambda x: x['capacite'], reverse=True)
                    else: # Petit effectif, on veut des petites salles
                        available_rooms = sorted(all_available, key=lambda x: x['capacite'])

                    # Sélectionner le nombre minimum de salles nécessaires
                    selected_rooms = []
                    current_cap = 0
                    for r in available_rooms:
                        selected_rooms.append(r)
                        current_cap += r['capacite']
                        if current_cap >= n_students: break
                    
                    if current_cap < n_students: continue # Pas assez de place sur ce créneau
                        
                    # Trouver un professeur surveillant par salle
                    needed_profs = len(selected_rooms)
                    candidates = []
                    for _, p in self.profs.iterrows():
                        if prof_daily_load.get((p['id'], d_str), 0) < 3: # Max 3 gardes par jour
                            # Score de priorité (Même département = +10)
                            score = 10 if p['dept_id'] == m_dept else 0
                            score -= prof_daily_load.get((p['id'], d_str), 0) # Équilibrage
                            candidates.append((score, p['id']))
                    
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    if len(candidates) < needed_profs: continue # Pas assez de profs
                        
                    # --- AFFECTATION EFFECTIVE ---
                    final_profs = [c[1] for c in candidates[:needed_profs]]
                    random.shuffle(m_students) # Mélange pour la répartition
                    student_idx = 0
                    
                    for i, room in enumerate(selected_rooms):
                        pid = final_profs[i]
                        # Découpage de la liste des étudiants pour cette salle précise
                        room_cap = room['capacite']
                        assigned_students = m_students[student_idx : student_idx + room_cap]
                        student_idx += room_cap
                        
                        exam_entry = {
                            'module_id': mid,
                            'prof_surveillant_id': pid,
                            'salle_id': room['id'],
                            'date_examen': d_str,
                            'creneau_debut': start_t,
                            'creneau_fin': end_t,
                            'students': assigned_students # Étudiants rattachés à cette salle
                        }
                        new_exams.append(exam_entry)
                        
                        # Mise à jour de l'état de l'occupantion
                        prof_daily_load[(pid, d_str)] = prof_daily_load.get((pid, d_str), 0) + 1
                        room_schedule[(room['id'], d_str, start_t)] = True
                    
                    # Marquer les étudiants comme occupés ce jour-là
                    for sid in m_students: student_daily_load[(sid, d_str)] = True
                        
                    assigned = True
                    break # Créneau trouvé
                if assigned: break # Jour trouvé
            
            if not assigned:
                print(f"WARNING: Impossible de planifier Module {mid} ({n_students} étudiants)")

        self.save(new_exams, append)
        return len(new_exams)

    def save(self, exams, append):
        """Sauvegarde les examens et la répartition nominative dans la DB."""
        if not append:
            self.cursor.execute("DELETE FROM examen_etudiants")
            self.cursor.execute("DELETE FROM examens")
        
        for e in exams:
            # insertion du créneau d'examen
            self.cursor.execute("""
                INSERT INTO examens (module_id, prof_surveillant_id, salle_id, date_examen, creneau_debut, creneau_fin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (e['module_id'], e['prof_surveillant_id'], e['salle_id'], e['date_examen'], e['creneau_debut'], e['creneau_fin']))
            
            exam_id = self.cursor.lastrowid
            
            # Insertion en masse des liens Étudiant-Salle (Répartition nominative)
            student_rows = [(exam_id, sid) for sid in e.get('students', [])]
            if student_rows:
                self.cursor.executemany("INSERT INTO examen_etudiants (examen_id, etudiant_id) VALUES (?, ?)", student_rows)
                
        self.conn.commit()
