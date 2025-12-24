import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from optimizer import ExamScheduler
import datetime

import os
from seed import init_db, generate_data, create_connection

# Custom CSS for Right-Side Sidebar & Premium Institutional Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Content Styling */
    .main {
        background-color: #f8fafc;
        order: -1;
    }
    
    .block-container {
        padding: 3rem 4rem;
        max-width: 1200px;
    }

    /* Premium Typography */
    h1 {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem !important;
        text-align: center;
    }
    
    h2, h3 {
        color: #1e1b4b;
        font-weight: 700 !important;
        margin-top: 1rem !important;
        letter-spacing: -0.01em;
    }

    /* Right Sidebar Overhaul */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid #e2e8f0;
        box-shadow: -4px 0 15px -3px rgb(0 0 0 / 0.05);
    }
    
    section[data-testid="stSidebar"] {
        order: 10;
        right: 0;
        left: auto;
    }

    /* Global Sidebar Element Coloring */
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p, 
    [data-testid="stSidebar"] span {
        color: #1e293b !important;
    }

    /* Cards & Components */
    .card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
        border: 1px solid #f1f5f9;
        margin-bottom: 2rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
    }

    .stMetric {
        background: #ffffff;
        padding: 1.5rem !important;
        border-radius: 16px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05) !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #4338ca !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        height: 3.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.025em;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
        box-shadow: 0 10px 15px -3px rgba(67, 56, 202, 0.3);
        transform: scale(1.02);
    }

    /* Form Fields */
    div[data-baseweb="select"], div[data-baseweb="input"] {
        border-radius: 10px !important;
    }

    /* Utilities */
    .badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# Database Connection
DB_PATH = "exams.db"

def get_connection():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        init_db(conn)
        generate_data(conn)
        return conn
    return sqlite3.connect(DB_PATH)

# --- SIDEBAR (Now on the Right) ---
with st.sidebar:
    st.markdown('<h2 style="text-align: center; color: #1e1b4b;">🔐 Authentification</h2>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Callback to clear auth when role is switched
    def handle_logout():
        for key in list(st.session_state.keys()):
            if key.startswith("auth_"):
                st.session_state[key] = False

    role = st.selectbox(
        "🎯 Accès Portail", 
        ["Vice-Doyen / Doyen", "Administrateur Examens", "Chef de Département", "Professeur", "Étudiant"],
        index=4, # Default to public Student view
        on_change=handle_logout
    )
    
    # PASSWORDS
    PASSWORDS = {
        "Vice-Doyen / Doyen": "doyen123",
        "Administrateur Examens": "admin123",
        "Chef de Département": "chef123",
        "Professeur": "prof123",
    }
    
    # Authentication Check
    is_authenticated = False
    if role == "Étudiant":
        is_authenticated = True
    else:
        if f'auth_{role}' not in st.session_state:
            st.session_state[f'auth_{role}'] = False
        
        if not st.session_state[f'auth_{role}']:
            st.markdown(f"**Authentification : {role}**")
            pwd_input = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                if pwd_input == PASSWORDS.get(role):
                    st.session_state[f'auth_{role}'] = True
                    st.success("Accès autorisé !")
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect.")
        
        is_authenticated = st.session_state.get(f'auth_{role}', False)

    st.markdown("---")
    
    if is_authenticated:
        st.markdown('<h2 style="color: white; text-align: center;">📂 Filtres</h2>', unsafe_allow_html=True)
        # Load depts for filter
        try:
            with get_connection() as conn:
                depts_list = pd.read_sql("SELECT nom FROM departements", conn)['nom'].tolist()
        except:
            depts_list = []
            
        selected_dept_filter = st.selectbox("Département", ["TOUT"] + depts_list)
        
        if role != "Étudiant":
            if st.button("Déconnexion"):
                st.session_state[f'auth_{role}'] = False
                st.rerun()

    st.markdown("---")
    st.caption("Université - Système de Planification v1.0")

# --- MAIN CONTENT AREA ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 1rem;">
        <span class="badge">Session Académique 2024-2025</span>
    </div>
""", unsafe_allow_html=True)

# Helper functions
def load_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if not is_authenticated:
    st.markdown('<div class="card" style="text-align: center;">', unsafe_allow_html=True)
    st.warning("⚠️ Cet espace est protégé. Veuillez vous authentifier via la barre latérale pour accéder aux données.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- VIEW: Vice-Doyen / Doyen ---
if role == "Vice-Doyen / Doyen":
    st.markdown('<h1 style="text-align: center; margin-bottom: 2.5rem;">📊 Analyse & Pilotage Stratégique</h1>', unsafe_allow_html=True)
    
    # KPIs in a 2x2 grid for a tighter look
    m1, m2 = st.columns(2)
    m3, m4 = st.columns(2)
    
    dept_cond = "" if selected_dept_filter == "TOUT" else f"WHERE d.nom = '{selected_dept_filter}'"
    dept_join = "" if selected_dept_filter == "TOUT" else "JOIN formations f ON e.formation_id = f.id JOIN departements d ON f.dept_id = d.id"

    with m1:
        nb_etudiants = load_data(f"SELECT COUNT(e.id) FROM etudiants e {dept_join} {dept_cond}").iloc[0,0]
        st.metric("👥 Effectif Étudiant", f"{nb_etudiants:,}")
        
    with m2:
        # Complex query to count exams for filtered dept
        ex_dept_cond = "" if selected_dept_filter == "TOUT" else f"WHERE d.nom = '{selected_dept_filter}'"
        nb_examens = load_data(f"""
            SELECT COUNT(ex.id) 
            FROM examens ex 
            JOIN modules m ON ex.module_id = m.id 
            JOIN formations f ON m.formation_id = f.id 
            JOIN departements d ON f.dept_id = d.id
            {ex_dept_cond}
        """).iloc[0,0]
        st.metric("📝 Examens Planifiés", nb_examens)
        
    with m3:
        st.metric("🏛️ Salles Utilisées", "12 / 15")
        
    with m4:
        st.metric("✅ Conflits", "0", delta="Zéro Conflit", delta_color="normal")

    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Charge d'Examen par Département")
        df_dept = load_data("""
            SELECT d.nom as Département, COUNT(ex.id) as Examens
            FROM examens ex
            JOIN modules m ON ex.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            GROUP BY d.nom
        """)
        fig = px.bar(df_dept, x='Département', y='Examens', color='Examens', color_continuous_scale='Blues')
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🏁 État de Remplissage")
        # Dummy data for donut
        fig_pie = px.pie(values=[84, 16], names=['Assigné', 'Restant'], hole=0.7, color_discrete_sequence=['#1e40af', '#e2e8f0'])
        fig_pie.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
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
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            append_mode = st.checkbox("➕ Mode Incremental", value=True, help="Ajouter les examens sans supprimer ceux déjà existants.")
        
        submit_auto = st.form_submit_button("🚀 Lancer l'Optimisation")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if submit_auto:
        formation_ids = []
        if selected_formations:
            formation_ids = formations[formations['nom'].isin(selected_formations)]['id'].tolist()
            
        with st.spinner("Calcul des meilleurs créneaux en cours..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_generated = scheduler.generate_schedule(start_date, end_date, formation_ids, append=append_mode)
        st.success(f"Opération réussie ! {nb_generated} nouveaux examens ont été placés.")
        st.balloons()
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("➕ Ajout Manuel")
    
    with st.form("manual_exam_form", border=False):
        col_f1, col_f2 = st.columns(2)
        modules = load_data("SELECT id, nom FROM modules")
        rooms = load_data("SELECT id, nom FROM lieux_examen")
        profs = load_data("SELECT id, nom, prenom FROM professeurs")
        
        with col_f1:
            mod_choice = st.selectbox("Module", modules['nom'], key='m_sel')
            date_choice = st.date_input("Date", datetime.date.today(), key='d_sel_man')
            start_time = st.time_input("Heure Début", datetime.time(8, 30))
            
        with col_f2:
            room_choice = st.selectbox("Salle", rooms['nom'], key='r_sel')
            prof_choice = st.selectbox("Surveillant", [f"{r['nom']} {r['prenom']}" for _,r in profs.iterrows()], key='p_sel')
            end_time = st.time_input("Heure Fin", datetime.time(10, 0))
            
        submitted = st.form_submit_button("Enregistrer l'Examen")
        
        if submitted:
            m_id = modules[modules['nom'] == mod_choice].iloc[0]['id']
            r_id = rooms[rooms['nom'] == room_choice].iloc[0]['id']
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
                st.success(f"Examen ajouté !")
            except Exception as e:
                st.error(f"Erreur : {e}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🛠️ Maintenance")
    with st.expander("Zone de Danger - Réinitialisation"):
        st.error("Action irréversible.")
        if st.button("🗑️ Réinitialiser la base"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Aperçu du Planning Global")
    df_exams = load_data("""
        SELECT 
            e.date_examen, e.creneau_debut, e.creneau_fin, 
            m.nom as module, s.nom as salle, p.nom as surveillant
        FROM examens e
        LEFT JOIN modules m ON e.module_id = m.id
        LEFT JOIN lieux_examen s ON e.salle_id = s.id
        LEFT JOIN professeurs p ON e.prof_surveillant_id = p.id
        ORDER BY e.date_examen, e.creneau_debut
    """)
    st.dataframe(df_exams, use_container_width=True)
    
    if not df_exams.empty:
        # Specialty Tabs
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🏁 Planning par Spécialité")
        df_full = load_data("""
            SELECT f.nom as formation, m.nom as module, e.date_examen, e.creneau_debut, e.creneau_fin, s.nom as salle, p.nom as surveillant
            FROM examens e
            LEFT JOIN modules m ON e.module_id = m.id
            LEFT JOIN formations f ON m.formation_id = f.id
            LEFT JOIN lieux_examen s ON e.salle_id = s.id
            LEFT JOIN professeurs p ON e.prof_surveillant_id = p.id
            ORDER BY f.nom, e.date_examen, e.creneau_debut
        """)
        
        formations_list = df_full['formation'].unique()
        if len(formations_list) > 0:
            tabs = st.tabs([str(f) for f in formations_list])
            for i, formation in enumerate(formations_list):
                with tabs[i]:
                    subset = df_full[df_full['formation'] == formation].drop(columns=['formation'])
                    st.dataframe(subset, use_container_width=True)
    
    csv = df_exams.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Exporter en CSV", csv, f"planning_{datetime.date.today()}.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# --- VIEW: Chef de Département ---
elif role == "Chef de Département":
    st.markdown('<h1 style="text-align: center;">🏢 Vue Départementale</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    depts = load_data("SELECT nom FROM departements")
    selected_dept = st.selectbox("Sélectionner votre département", depts['nom'])
    
    st.write(f"### Planning pour le département {selected_dept}")
    
    query = f"""
        SELECT 
            e.date_examen, 
            e.creneau_debut, 
            m.nom as module, 
            f.nom as formation, 
            s.nom as salle
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN departements d ON f.dept_id = d.id
        JOIN lieux_examen s ON e.salle_id = s.id
        WHERE d.nom = '{selected_dept}'
        ORDER BY e.date_examen, e.creneau_debut
    """
    df_dept_exams = load_data(query)
    
    if df_dept_exams.empty:
        st.info("Aucun examen n'est encore planifié pour ce département.")
    else:
        st.dataframe(df_dept_exams, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- VIEW: Professeur ---
elif role == "Professeur":
    st.markdown('<h1 style="text-align: center;">👨‍🏫 Espace Surveillant</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    df_profs = load_data("SELECT id, nom, prenom FROM professeurs LIMIT 15")
    prof_names = [f"Pr. {r['nom']} {r['prenom']}" for _, r in df_profs.iterrows()]
    selected_prof = st.selectbox("Sélectionnez votre nom", prof_names)
    
    if selected_prof:
        p_name = selected_prof.split(" ")[1]
        st.info(f"Planning des surveillances pour {selected_prof}")
        
        df_surveillance = load_data(f"""
            SELECT m.nom as module, s.nom as salle, e.date_examen, e.creneau_debut, e.creneau_fin
            FROM examens e
            JOIN professeurs p ON e.prof_surveillant_id = p.id
            JOIN modules m ON e.module_id = m.id
            JOIN lieux_examen s ON e.salle_id = s.id
            WHERE p.nom = '{p_name}'
            ORDER BY e.date_examen
        """)
        if df_surveillance.empty:
            st.warning("Aucune surveillance ne vous a encore été attribuée.")
        else:
            st.table(df_surveillance)
    st.markdown('</div>', unsafe_allow_html=True)

# --- VIEW: Étudiant ---
elif role == "Étudiant":
    st.markdown('<h1 style="text-align: center;">📅 Planning Étudiant</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔍 Recherche Étudiant")
    search = st.text_input("Saisissez votre nom ou matricule")
    if search:
        st.success(f"Résultats pour '{search}' :")
        df_exams = load_data("""
            SELECT m.nom as module, s.nom as salle, e.date_examen, e.creneau_debut 
            FROM examens e 
            JOIN modules m ON e.module_id = m.id 
            JOIN lieux_examen s ON e.salle_id = s.id
            ORDER BY e.date_examen LIMIT 10
        """)
        st.table(df_exams)
    else:
        st.info("Entrez votre nom pour voir votre planning personnalisé.")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Université - Système de Planification v1.0")
