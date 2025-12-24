import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from optimizer import ExamScheduler
import datetime

import os
from seed import init_db, generate_data, create_connection

# Page Config
st.set_page_config(page_title="Univ Exam Planner", layout="wide", page_icon="📅")

# Database Connection
DB_PATH = "exams.db"

def get_connection():
    # Auto-initialize DB if it doesn't exist (useful for Streamlit Cloud)
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)
        generate_data(conn)
        return conn
    return sqlite3.connect(DB_PATH)

# Sidebar - Role Selection
st.sidebar.title("Univ Exam Planner")
role = st.sidebar.selectbox("Rôle", ["Vice-Doyen / Doyen", "Administrateur Examens", "Chef de Département", "Étudiant / Professeur"])

# Helper functions
def load_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- VIEW: Vice-Doyen / Doyen ---
if role == "Vice-Doyen / Doyen":
    st.title("📊 Tableau de Bord Stratégique")
    
    # KPIs
    st.markdown("### Indicateurs Clés")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nb_etudiants = load_data("SELECT COUNT(*) FROM etudiants").iloc[0,0]
        st.metric("Total Étudiants", nb_etudiants)
        
    with col2:
        nb_examens = load_data("SELECT COUNT(*) FROM examens").iloc[0,0]
        st.metric("Examens Planifiés", nb_examens)
        
    with col3:
        taux_occupation = "85%" # Placeholder calculation
        st.metric("Taux Occupation Salles", taux_occupation)
        
    with col4:
        conflits = 0 # Placeholder
        st.metric("Conflits Détectés", conflits, delta_color="inverse")

    # Global Stats
    st.markdown("### Répartition par Département")
    df_dept = load_data("""
        SELECT d.nom, COUNT(e.id) as nb_etudiants 
        FROM etudiants e 
        JOIN formations f ON e.formation_id = f.id 
        JOIN departements d ON f.dept_id = d.id 
        GROUP BY d.nom
    """)
    fig = px.bar(df_dept, x='nom', y='nb_etudiants', title="Nombre d'étudiants par département")
    st.plotly_chart(fig, use_container_width=True)

# --- VIEW: Administrateur ---
elif role == "Administrateur Examens":
    st.title("⚙️ Gestion des Examens")
    
    st.warning("⚠️ Zone réservée à la planification")
    
    if st.button("🚀 Lancer l'Optimisation Automatique"):
        with st.spinner("Calcul en cours (Algorithme Glouton)..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_generated = scheduler.generate_schedule(datetime.date.today())
        st.success(f"Planning généré avec succès ! {nb_generated} examens placés.")
        st.balloons()
    
    st.markdown("---")
    st.subheader("➕ Ajout Manuel d'un Examen")
    
    with st.form("manual_exam_form"):
        col_f1, col_f2 = st.columns(2)
        
        # Load available options
        modules = load_data("SELECT id, nom FROM modules")
        rooms = load_data("SELECT id, nom FROM lieux_examen")
        profs = load_data("SELECT id, nom, prenom FROM professeurs")
        
        with col_f1:
            mod_choice = st.selectbox("Module", modules['nom'], key='m_sel')
            date_choice = st.date_input("Date", datetime.date.today())
            start_time = st.time_input("Heure Début", datetime.time(8, 30))
            
        with col_f2:
            room_choice = st.selectbox("Salle", rooms['nom'], key='r_sel')
            prof_choice = st.selectbox("Surveillant", profs['nom'] + " " + profs['prenom'], key='p_sel')
            end_time = st.time_input("Heure Fin", datetime.time(10, 0))
            
        submitted = st.form_submit_button("Enregistrer l'Examen")
        
        if submitted:
            # Resolve IDs
            m_id = modules[modules['nom'] == mod_choice].iloc[0]['id']
            r_id = rooms[rooms['nom'] == room_choice].iloc[0]['id']
            # Simple prof resolution (assuming unique name combination for demo)
            p_id = profs[(profs['nom'] + " " + profs['prenom']) == prof_choice].iloc[0]['id']
            
            try:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO examens (module_id, prof_surveillant_id, salle_id, date_examen, creneau_debut, creneau_fin)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (int(m_id), int(p_id), int(r_id), str(date_choice), str(start_time), str(end_time)))
                conn.commit()
                conn.close()
                st.success(f"Examen de {mod_choice} ajouté avec succès !")
            except Exception as e:
                st.error(f"Erreur lors de l'ajout : {e}")

    st.markdown("---")
    st.markdown("### Aperçu du Planning Généré")
    df_exams = load_data("""
        SELECT m.nom as module, s.nom as salle, p.nom as surveillant, e.date_examen, e.creneau_debut 
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN lieux_examen s ON e.salle_id = s.id
        JOIN professeurs p ON e.prof_surveillant_id = p.id
        ORDER BY e.date_examen, e.creneau_debut
    """)
    st.dataframe(df_exams, use_container_width=True)
    
    csv = df_exams.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exporter en CSV", csv, "planning.csv", "text/csv")

# --- VIEW: Chef de Département ---
elif role == "Chef de Département":
    st.title("🏢 Vue Départementale")
    
    depts = load_data("SELECT nom FROM departements")
    selected_dept = st.selectbox("Sélectionner un département", depts['nom'])
    
    st.markdown(f"### Planning pour {selected_dept}")
    
    # Filter exams for this dept
    query = f"""
        SELECT m.nom as module, f.nom as formation, s.nom as salle, e.date_examen, e.creneau_debut 
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departements d ON f.dept_id = d.id
        JOIN lieux_examen s ON e.salle_id = s.id
        WHERE d.nom = '{selected_dept}'
        ORDER BY e.date_examen
    """
    df_dept_exams = load_data(query)
    
    if df_dept_exams.empty:
        st.info("Aucun examen planifié pour ce département.")
    else:
        st.dataframe(df_dept_exams, use_container_width=True)

# --- VIEW: Étudiant / Professeur ---
elif role == "Étudiant / Professeur":
    st.title("📅 Mon Emploi du Temps")
    
    user_type = st.radio("Je suis :", ["Étudiant", "Professeur"])
    
    if user_type == "Étudiant":
        # Search by name logic (simplified for demo)
        search = st.text_input("Rechercher par nom (Simulation)")
        if search:
            st.info("Affichage du planning pour l'étudiant sélectionné...")
            # For demo, just show all exams or exams for a specific formation
            df_exams = load_data("""
                SELECT m.nom as module, s.nom as salle, e.date_examen, e.creneau_debut 
                FROM examens e 
                JOIN modules m ON e.module_id = m.id 
                JOIN lieux_examen s ON e.salle_id = s.id
                LIMIT 5
            """)
            st.table(df_exams)
            
    else:
        st.info("Espace Professeur : Voir mes surveillances")
        df_profs = load_data("SELECT * FROM professeurs LIMIT 1")
        if not df_profs.empty:
            prof_name = df_profs.iloc[0]['nom']
            st.write(f"Bonjour Pr. {prof_name}")
            
            df_surveillance = load_data(f"""
                SELECT m.nom as module, s.nom as salle, e.date_examen, e.creneau_debut
                FROM examens e
                JOIN professeurs p ON e.prof_surveillant_id = p.id
                JOIN modules m ON e.module_id = m.id
                JOIN lieux_examen s ON e.salle_id = s.id
                WHERE p.nom = '{prof_name}'
            """)
            st.table(df_surveillance)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Université - Système de Planification v1.0")
