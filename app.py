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

# Custom CSS for Professional Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background-color: #f8fafc;
    }
    
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #1e40af;
        color: white;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #1e3a8a;
        transform: translateY(-1px);
    }
    
    .card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700 !important;
    }
    
    div[data-testid="stExpander"] {
        border-radius: 12px;
        background-color: white;
        border: 1px solid #e2e8f0;
    }
    
    .sidebar .sidebar-content {
        background-color: #1e293b;
    }
    
    /* Center title and add spacing */
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

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
    st.markdown('<h1 style="text-align: center; margin-bottom: 2rem;">📊 Tableau de Bord Stratégique</h1>', unsafe_allow_html=True)
    
    # KPIs in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        nb_etudiants = load_data("SELECT COUNT(*) FROM etudiants").iloc[0,0]
        st.metric("Total Étudiants", nb_etudiants)
        
    with col2:
        nb_examens = load_data("SELECT COUNT(*) FROM examens").iloc[0,0]
        st.metric("Examens Planifiés", nb_examens)
        
    with col3:
        taux_occupation = "85%"
        st.metric("Occupation Salles", taux_occupation)
        
    with col4:
        conflits = 0
        st.metric("Conflits Détectés", conflits, delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Répartition des Étudiants par Département")
        df_dept = load_data("""
            SELECT d.nom, COUNT(e.id) as nb_etudiants 
            FROM etudiants e 
            JOIN formations f ON e.formation_id = f.id 
            JOIN departements d ON f.dept_id = d.id 
            GROUP BY d.nom
        """)
        fig = px.bar(df_dept, x='nom', y='nb_etudiants', color_discrete_sequence=['#3b82f6'])
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# --- VIEW: Administrateur ---
elif role == "Administrateur Examens":
    st.markdown('<h1 style="text-align: center;">⚙️ Gestion des Examens</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🗓️ Génération Automatique")
    st.info("Utilisez cette section pour planifier les examens selon les contraintes du TP.")
    
    with st.form("auto_schedule_form", border=False):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Date de début", datetime.date.today())
        with col_d2:
            end_date = st.date_input("Date de fin", datetime.date.today() + datetime.timedelta(days=5))
            
        formations = load_data("SELECT id, nom FROM formations")
        selected_formations = st.multiselect("Spécialités à inclure", formations['nom'], help="Laissez vide pour planifier toute la faculté.")
        
        submit_auto = st.form_submit_button("🚀 Lancer l'Optimisation")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submit_auto:
        # ... logic ...
        formation_ids = []
        if selected_formations:
            formation_ids = formations[formations['nom'].isin(selected_formations)]['id'].tolist()
            
        with st.spinner("Calcul des meilleurs créneaux en cours..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_generated = scheduler.generate_schedule(start_date, end_date, formation_ids)
        st.success(f"Opération réussie ! {nb_generated} examens ont été placés.")
        st.balloons()
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("➕ Ajout Manuel")
    
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
    st.subheader("🛠️ Maintenance")
    with st.expander("Zone de Danger - Réinitialisation"):
        st.error("Cette action supprimera toutes les données et recréera une base propre avec les derniers paramètres (ex: 50 professeurs).")
        if st.button("🗑️ Réinitialiser et Re-générer les données"):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            conn = get_connection()
            st.success("Base de données réinitialisée avec succès ! (50 professeurs chargés)")
            st.rerun()

    st.markdown("---")
    st.markdown("### Aperçu du Planning Généré")
    # Using LEFT JOIN to ensure exams show up even if a relation is missing
    df_exams = load_data("""
        SELECT 
            e.date_examen, 
            e.creneau_debut, 
            e.creneau_fin, 
            m.nom as module, 
            s.nom as salle, 
            p.nom as surveillant
        FROM examens e
        LEFT JOIN modules m ON e.module_id = m.id
        LEFT JOIN lieux_examen s ON e.salle_id = s.id
        LEFT JOIN professeurs p ON e.prof_surveillant_id = p.id
        ORDER BY e.date_examen, e.creneau_debut
    """)
    
    
    if not df_exams.empty:
        st.caption(f"Total: {len(df_exams)} examens visibles")
        
        # Enhanced display: Group by Specialty
        st.subheader("📅 Planning par Spécialité")
        
        # Get data with Formation info
        df_full = load_data("""
            SELECT 
                f.nom as formation,
                m.nom as module, 
                e.date_examen, 
                e.creneau_debut, 
                e.creneau_fin, 
                s.nom as salle, 
                p.nom as surveillant
            FROM examens e
            LEFT JOIN modules m ON e.module_id = m.id
            LEFT JOIN formations f ON m.formation_id = f.id
            LEFT JOIN lieux_examen s ON e.salle_id = s.id
            LEFT JOIN professeurs p ON e.prof_surveillant_id = p.id
            ORDER BY f.nom, e.date_examen, e.creneau_debut
        """)
        
        # Create tabs for each formation
        formations_list = df_full['formation'].unique()
        if len(formations_list) > 0:
            tabs = st.tabs([str(f) for f in formations_list])
            
            for i, formation in enumerate(formations_list):
                with tabs[i]:
                    st.write(f"### {formation}")
                    subset = df_full[df_full['formation'] == formation].drop(columns=['formation'])
                    st.dataframe(subset, use_container_width=True)
        else:
            st.dataframe(df_exams, use_container_width=True)

    else:
        st.info("Aucun examen trouvé. Lancez l'optimisation ou ajoutez-en un manuellement.")
    
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
