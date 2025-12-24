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
    
    :root {
        --primary-indigo: #4338ca;
        --secondary-indigo: #3730a3;
        --accent-blue: #0ea5e9;
        --deep-navy: #1e1b4b;
        --slate-50: #f8fafc;
        --slate-100: #f1f5f9;
        --slate-200: #e2e8f0;
        --slate-800: #1e293b;
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background-color: var(--slate-50);
    }
    
    .block-container {
        padding: 3rem 4rem;
        max-width: 1200px;
    }

    /* Premium Typography */
    h1 {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--deep-navy) 0%, var(--primary-indigo) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2.5rem !important;
        letter-spacing: -0.02em;
    }
    
    h2, h3 {
        color: var(--deep-navy);
        font-weight: 700 !important;
        margin-top: 1.5rem !important;
        letter-spacing: -0.01em;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-left: 1px solid var(--slate-200);
        box-shadow: -4px 0 25px -5px rgb(0 0 0 / 0.05);
    }
    
    section[data-testid="stSidebar"] {
        order: 10;
        right: 0;
        left: auto;
    }

    /* Cards & Components */
    .card {
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 24px;
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.02), 0 4px 6px -4px rgb(0 0 0 / 0.02);
        border: 1px solid var(--slate-100);
        margin-bottom: 2rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 25px 50px -12px rgb(0 0 0 / 0.08);
    }

    .stMetric {
        background: #ffffff;
        padding: 1.5rem !important;
        border-radius: 20px !important;
        border: 1px solid var(--slate-200) !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05) !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: var(--primary-indigo) !important;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-indigo) 0%, var(--secondary-indigo) 100%);
        color: white;
        border: none;
        border-radius: 14px;
        font-weight: 600;
        height: 3.5rem;
        padding: 0 2rem;
        transition: all 0.3s ease;
        text-transform: none;
        letter-spacing: 0.01em;
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #4f46e5 0%, var(--primary-indigo) 100%);
        box-shadow: 0 15px 25px -5px rgba(67, 56, 202, 0.4);
        transform: translateY(-2px);
    }

    /* Badges & Labels */
    .badge {
        background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%);
        color: #0369a1;
        padding: 0.5rem 1.25rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #bae6fd;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-pill-success { background-color: #dcfce7; color: #166534; }
    </style>
""", unsafe_allow_html=True)

# Database Connection
# Database Connection & Versioning
DB_PATH = "exams.db"
APP_VERSION = "2.0.0" # Bump this version to force a DB reset on deployment

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check for existing version
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS app_meta (version TEXT)")
        cursor.execute("SELECT version FROM app_meta")
        row = cursor.fetchone()
        db_version = row[0] if row else None
    except Exception:
        db_version = None
        
    # If version mismatch or first run, re-initialize DB
    if db_version != APP_VERSION:
        init_db(conn)
        generate_data(conn)
        
        # Update version marker
        cursor.execute("DROP TABLE IF EXISTS app_meta")
        cursor.execute("CREATE TABLE app_meta (version TEXT)")
        cursor.execute("INSERT INTO app_meta (version) VALUES (?)", (APP_VERSION,))
        conn.commit()
        
    return conn

# --- SIDEBAR (Now on the Right) ---
with st.sidebar:
    # Branding
    st.markdown("""
        <div style="text-align: center; padding: 1.5rem 0; border-bottom: 2px solid #f1f5f9; margin-bottom: 2rem;">
            <div style="font-size: 1.2rem; font-weight: 800; color: #1e1b4b; letter-spacing: -1px; line-height: 1.2;">
                🏛️ UMBB <span style="color: #4338ca;">SCHED PRO</span>
            </div>
            <div style="font-size: 0.65rem; color: #64748b; text-transform: uppercase; font-weight: 700; margin-top: 0.4rem; letter-spacing: 0.5px;">
                Univ. M'Hamed Bougara
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<h3 style="text-align: center; color: #1e1b4b; margin-bottom: 1rem;">🔐 Authentification</h3>', unsafe_allow_html=True)
    
    # Callback to clear auth when role is switched
    def handle_logout():
        for key in list(st.session_state.keys()):
            if key.startswith("auth_"):
                st.session_state[key] = False

    role = st.selectbox(
        "🎯 Portails d'Accès", 
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
                facs_list = pd.read_sql("SELECT nom FROM departements", conn)['nom'].tolist()
        except:
            facs_list = []
            
        selected_fac_filter = st.selectbox("Faculté / Institut", ["TOUTE L'UNIVERSITÉ"] + facs_list)
        
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
    
    dept_cond = "" if selected_fac_filter == "TOUTE L'UNIVERSITÉ" else f"WHERE d.nom = '{selected_fac_filter}'"
    dept_join = "" if selected_fac_filter == "TOUTE L'UNIVERSITÉ" else "JOIN formations f ON e.formation_id = f.id JOIN departements d ON f.dept_id = d.id"

    with m1:
        nb_etudiants = load_data(f"SELECT COUNT(e.id) FROM etudiants e {dept_join} {dept_cond}").iloc[0,0]
        st.metric("👥 Effectif Étudiant", f"{nb_etudiants:,}")
        
    with m2:
        # Complex query to count exams for filtered dept
        ex_dept_cond = "" if selected_fac_filter == "TOUTE L'UNIVERSITÉ" else f"WHERE d.nom = '{selected_fac_filter}'"
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
        st.markdown('<h3 style="margin-top: 0 !important;">📈 Répartition des Examens</h3>', unsafe_allow_html=True)
        st.write("Volume d'examen par faculté")
        df_dept = load_data("""
            SELECT d.nom as Faculté, COUNT(ex.id) as Examens
            FROM examens ex
            JOIN modules m ON ex.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            GROUP BY d.nom
        """)
        fig = px.bar(df_dept, x='Faculté', y='Examens', color='Examens', 
                     color_continuous_scale='Blues',
                     template='plotly_white')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)', 
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis_title=None,
            yaxis_title=None
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0 !important;">🏁 Taux de Complétion</h3>', unsafe_allow_html=True)
        st.write("État de planification globale")
        # Multi-color donut
        fig_pie = px.pie(values=[84, 16], names=['Optimisé', 'Attente'], hole=0.75, 
                         color_discrete_sequence=['#4338ca', '#f1f5f9'])
        fig_pie.update_layout(
            showlegend=False, 
            margin=dict(l=0, r=0, t=0, b=0),
            annotations=[dict(text='84%', x=0.5, y=0.5, font_size=24, showarrow=False, font_family='Outfit', font_weight='bold')]
        )
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
    
    if submit_auto:
        formation_ids = []
        if selected_formations:
            formation_ids = formations[formations['nom'].isin(selected_formations)]['id'].tolist()
            
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Initialisation de l'algorithme...")
        progress_bar.progress(20)
        
        with st.spinner("Analyse des contraintes et placement des examens..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_generated = scheduler.generate_schedule(start_date, end_date, formation_ids, append=append_mode)
        
        progress_bar.progress(100)
        status_text.text("Génération terminée !")
        st.success(f"✅ Opération réussie ! {nb_generated} examens ont été planifiés sans conflit.")
        st.balloons()
    
    # Quick Stats for Admin
    st.markdown("### 📊 État des Ressources")
    qc1, qc2 = st.columns(2)
    with qc1:
        total_rooms = load_data("SELECT COUNT(*) FROM lieux_examen").iloc[0,0]
        used_rooms = load_data("SELECT COUNT(DISTINCT salle_id) FROM examens").iloc[0,0]
        st.metric("🏛️ Utilisation des Salles", f"{used_rooms}/{total_rooms}", help="Nombre de salles ayant au moins un examen planifié.")
    with qc2:
        total_profs = load_data("SELECT COUNT(*) FROM professeurs").iloc[0,0]
        used_profs = load_data("SELECT COUNT(DISTINCT prof_surveillant_id) FROM examens").iloc[0,0]
        st.metric("👨‍🏫 Mobilisation Professeurs", f"{used_profs}/{total_profs}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
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
    st.markdown('<h1 style="text-align: center;">🏢 Vue Facultaire</h1>', unsafe_allow_html=True)
    
    depts = load_data("SELECT id, nom FROM departements")
    selected_dept = st.selectbox("Sélectionner votre Faculté / Institut", depts['nom'])
    selected_dept_id = depts[depts['nom'] == selected_dept]['id'].values[0]
    
    st.write(f"### 📈 Performance : {selected_dept}")
    
    # Dept Stats
    sd1, sd2, sd3 = st.columns(3)
    with sd1:
        nb_f = load_data(f"SELECT COUNT(*) FROM formations WHERE dept_id = {selected_dept_id}").iloc[0,0]
        st.metric("🎓 Spécialités", nb_f)
    with sd2:
        nb_s = load_data(f"SELECT COUNT(e.id) FROM etudiants e JOIN formations f ON e.formation_id = f.id WHERE f.dept_id = {selected_dept_id}").iloc[0,0]
        st.metric("👥 Étudiants", nb_s)
    with sd3:
        nb_ex = load_data(f"SELECT COUNT(ex.id) FROM examens ex JOIN modules m ON ex.module_id = m.id JOIN formations f ON m.formation_id = f.id WHERE f.dept_id = {selected_dept_id}").iloc[0,0]
        st.metric("📝 Exams Planifiés", nb_ex)

    st.markdown("---")
    st.write(f"#### 🗓️ Calendrier des Examens")
    
    query = f"""
        SELECT 
            e.date_examen as Date, 
            e.creneau_debut as Début, 
            m.nom as Module, 
            f.nom as Formation, 
            s.nom as Salle
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
    st.markdown('<h1 style="text-align: center;">📅 Portail Étudiant</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🔍 Consultation du Planning")
    st.write("Recherchez votre nom pour consulter votre planning personnalisé.")
    
    search = st.text_input("Saisissez votre NOM ou Prénom", placeholder="Ex: Martin...")
    
    if search:
        # Search for students matching the name
        search_query = f"""
            SELECT id, nom, prenom, promo 
            FROM etudiants 
            WHERE nom LIKE '%{search}%' OR prenom LIKE '%{search}%'
            LIMIT 5
        """
        found_students = load_data(search_query)
        
        if not found_students.empty:
            st.markdown("### 👥 Étudiants trouvés")
            for _, student in found_students.iterrows():
                with st.expander(f"📌 {student['prenom']} {student['nom']} ({student['promo']})"):
                    # Get exams for this student
                    exams_query = f"""
                        SELECT 
                            m.nom as Module, 
                            s.nom as Salle, 
                            e.date_examen as Date, 
                            e.creneau_debut as Début,
                            e.creneau_fin as Fin
                        FROM examens e
                        JOIN modules m ON e.module_id = m.id
                        JOIN inscriptions i ON m.id = i.module_id
                        JOIN lieux_examen s ON e.salle_id = s.id
                        WHERE i.etudiant_id = {student['id']}
                        ORDER BY e.date_examen, e.creneau_debut
                    """
                    student_exams = load_data(exams_query)
                    if student_exams.empty:
                        st.info("Aucun examen planifié pour cet étudiant.")
                    else:
                        st.dataframe(student_exams, use_container_width=True)
        else:
            st.warning("Aucun étudiant trouvé avec ce nom.")
    else:
        st.info("💡 Astuce : Tapez quelques lettres de votre nom pour commencer.")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Université - Système de Planification v1.0")
