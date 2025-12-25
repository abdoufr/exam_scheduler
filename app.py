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

    /* Mobile Responsiveness */
    @media (max-width: 991px) {
        .block-container {
            padding: 2rem 1rem !important;
            max-width: 100%;
        }

        h1 {
            font-size: 2rem !important;
            margin-bottom: 1.5rem !important;
            text-align: center;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Database Connection
DB_PATH = "exams.db"
APP_VERSION = "2.3.0" # Version de l'application (Capacités: Salles 20, Amphis 50)

# --- GESTION DE LA CONNEXION DB ---
def get_connection():
    """Établit une connexion à la base de données SQLite."""
    conn = sqlite3.connect(DB_PATH)
    return conn

@st.cache_resource
def init_app():
    """Initialise l'application au premier lancement (Migration DB)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS app_meta (version TEXT)")
        cursor.execute("SELECT version FROM app_meta LIMIT 1")
        version_row = cursor.fetchone()
        db_version = version_row[0] if version_row else None
    except:
        db_version = None
        
    if db_version != APP_VERSION:
        # Si la version a changé, on réinitialise tout (Seed data)
        init_db(conn)
        generate_data(conn)
        cursor.execute("DROP TABLE IF EXISTS app_meta")
        cursor.execute("CREATE TABLE app_meta (version TEXT)")
        cursor.execute("INSERT INTO app_meta (version) VALUES (?)", (APP_VERSION,))
        conn.commit()
    return conn

# Initialisation de l'application au démarrage
init_app()

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #1e1b4b; letter-spacing: -1px; line-height: 1.2;">
                🏛️ UMBB <span style="color: #4338ca;">SCHED</span>
            </div>
            <div style="font-size: 0.8rem; color: #64748b; font-weight: 700; margin-top: 0.4rem;">
                SYSTÈME DE PLANIFICATION AVANCÉ
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👤 Identification")
    role = st.selectbox(
        "Rôle", 
        ["Étudiant", "Professeur", "Chef de Département", "Administrateur Examens", "Vice-Doyen / Doyen"],
        index=0
    )

    PASSWORDS = {
        "Vice-Doyen / Doyen": "doyen123",
        "Administrateur Examens": "admin123",
        "Chef de Département": "chef123",
        "Professeur": "prof123",
    }
    
    is_authenticated = False
    
    if role == "Étudiant":
        is_authenticated = True
    else:
        if f'auth_{role}' not in st.session_state:
            st.session_state[f'auth_{role}'] = False
            
        if not st.session_state[f'auth_{role}']:
            pwd_input = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                if pwd_input == PASSWORDS.get(role):
                    st.session_state[f'auth_{role}'] = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        else:
            is_authenticated = True
            if st.button("Déconnexion"):
                st.session_state[f'auth_{role}'] = False
                st.rerun()

    # Navigation Menu
    current_page = None 
    
    if is_authenticated:
        st.markdown("---")
        st.markdown("### 📌 Menu")
        
        # Base options available to everyone (or specific logic)
        nav_options = ["Voir Emplois du temps", "Répartition Salles"]
        
        # Dashboard only for Admin/Doyen/Chef
        if role in ["Administrateur Examens", "Vice-Doyen / Doyen", "Chef de Département"]:
            nav_options.insert(0, "Tableau de bord")
            current_page = "Tableau de bord"
            
        if role in ["Administrateur Examens", "Vice-Doyen / Doyen"]:
            if "Tableau de bord" in nav_options:
                idx = nav_options.index("Tableau de bord") + 1
            else:
                idx = 0
            nav_options.insert(idx, "Créer Emploi du temps")
            
        if role == "Professeur":
            nav_options.append("Mes Surveillances")
            current_page = "Mes Surveillances"
            
        if role == "Étudiant":
            nav_options.append("Mon Planning")
            current_page = "Mon Planning"
            
        # Fallback default if not set
        if current_page is None and nav_options:
            current_page = nav_options[0]
            
        current_page = st.radio("Navigation", nav_options, label_visibility="collapsed", index=nav_options.index(current_page) if current_page in nav_options else 0)


# --- MAIN CONTENT AREA ---

# Helper functions
def load_data(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

if not is_authenticated:
    st.markdown("""
        <div style="text-align: center; padding: 4rem 2rem;">
            <h1>🔒 Accès Restreint</h1>
            <p style="font-size: 1.2rem; color: #64748b;">Veuillez vous identifier dans la barre latérale pour accéder à l'application.</p>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# Header Display
st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2rem;">
        <div>
            <span class="badge">{role}</span>
        </div>
        <div style="font-weight: 600; color: #64748b;">
            {datetime.date.today().strftime('%d %B %Y')}
        </div>
    </div>
""", unsafe_allow_html=True)


# --- PAGE: Tableau de bord ---
if current_page == "Tableau de bord":
    st.markdown('<h1 style="text-align: center; margin-bottom: 2rem;">📊 Tableau de Bord</h1>', unsafe_allow_html=True)
    
    # Statistics
    m1, m2, m3, m4 = st.columns(4)
    
    conn = get_connection()
    
    with m1:
        nb_etudiants = pd.read_sql("SELECT COUNT(*) FROM etudiants", conn).iloc[0,0]
        st.metric("👥 Total Étudiants", f"{nb_etudiants:,}")
        
    with m2:
        # Unique exams (Modules scheduled)
        nb_examens = pd.read_sql("SELECT COUNT(DISTINCT module_id) FROM examens", conn).iloc[0,0]
        st.metric("📝 Examens Planifiés", f"{nb_examens}")
        
    with m3:
        nb_salles = pd.read_sql("SELECT COUNT(DISTINCT salle_id) FROM examens", conn).iloc[0,0]
        total_salles = pd.read_sql("SELECT COUNT(*) FROM lieux_examen", conn).iloc[0,0]
        st.metric("🏛️ Salles Utilisées", f"{nb_salles}/{total_salles}")
        
    with m4:
        st.metric("⚠️ Taux Conflits", "0.0%", delta="OK", delta_color="normal")
        
    conn.close()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphs
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Examens par Faculté")
        df_dept = load_data("""
            SELECT d.nom as Faculté, COUNT(DISTINCT ex.module_id) as Examens
            FROM examens ex
            JOIN modules m ON ex.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            GROUP BY d.nom
        """)
        if not df_dept.empty:
            fig = px.bar(df_dept, x='Faculté', y='Examens', color='Faculté', template='plotly_white')
            # Hide legend if it takes too much space
            fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,t=0,b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("👥 Étudiants par Spécialité")
        df_etu = load_data("""
            SELECT f.nom as Spécialité, COUNT(e.id) as Etudiants
            FROM etudiants e
            JOIN formations f ON e.formation_id = f.id
            GROUP BY f.nom
            ORDER BY Etudiants DESC
            LIMIT 10
        """)
        if not df_etu.empty:
            fig2 = px.bar(df_etu, x='Etudiants', y='Spécialité', orientation='h', template='plotly_white', color='Etudiants')
            fig2.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,t=0,b=0), height=300)
            st.plotly_chart(fig2, use_container_width=True)
        else:
             st.info("Aucune donnée.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Occupation Row
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🏁 Occupation Globale (Salles vs Amphis)")
    try:
        conn = get_connection()
        type_usage = pd.read_sql("""
            SELECT l.type, COUNT(DISTINCT e.salle_id) as used
            FROM lieux_examen l
            LEFT JOIN examens e ON l.id = e.salle_id
            GROUP BY l.type
        """, conn)
        if not type_usage.empty:
            fig_pie = px.pie(type_usage, values='used', names='type', hole=0.7, color_discrete_sequence=['#4338ca', '#0ea5e9', '#e2e8f0'])
            fig_pie.update_layout(showlegend=True, margin=dict(l=0,r=0,t=0,b=0), height=250)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
             st.info("Pas d'occupation.")
    except:
         st.info("No data")
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Créer Emploi du temps ---
elif current_page == "Créer Emploi du temps":
    st.markdown('<h1 style="text-align: center;">⚡ Générateur d\'Emploi du Temps</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Configuration de la Génération")
    
    with st.form("auto_schedule_form"):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Date de début", datetime.date.today())
        with col_d2:
            end_date = st.date_input("Date de fin", datetime.date.today() + datetime.timedelta(days=14))
            
        formations = load_data("SELECT id, nom FROM formations")
        selected_formations = st.multiselect("Filtrer par Spécialité (Optionnel)", formations['nom'])
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            append_mode = st.checkbox("Mode Sans Conflit (Incremental)", value=False, help="Décocher pour écraser")
        
        submitted = st.form_submit_button("🚀 Lancer la Génération")
    
    if submitted:
        formation_ids = []
        if selected_formations:
            formation_ids = formations[formations['nom'].isin(selected_formations)]['id'].tolist()
            
        with st.spinner("Optimisation en cours (Répartition et affectation nominative)..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_gen = scheduler.generate_schedule(start_date, end_date, formation_ids, append=append_mode)
        
        st.success(f"✅ Génération terminée ! {nb_gen} créneaux planifiés avec affectation des étudiants.")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Voir Emplois du temps ---
elif current_page == "Voir Emplois du temps":
    st.markdown('<h1 style="text-align: center;">🗓️ Consultation des Plannings</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    formations = load_data("SELECT id, nom FROM formations ORDER BY nom")
    all_formats = ["Toutes les spécialités"] + formations['nom'].tolist()
    
    c_filter1, c_filter2 = st.columns([1, 2])
    with c_filter1:
        st.markdown("### 🔍 Filtres")
    with c_filter2:
        selected_formation = st.selectbox("Sélectionner une Spécialité", all_formats)
    
    base_query = """
        SELECT 
            e.date_examen, 
            e.creneau_debut, 
            e.creneau_fin, 
            m.nom as Module, 
            f.nom as Spécialité,
            s.nom as Salle, 
            p.nom || ' ' || p.prenom as Surveillant
        FROM examens e
        JOIN modules m ON e.module_id = m.id
        JOIN formations f ON m.formation_id = f.id
        JOIN lieux_examen s ON e.salle_id = s.id
        LEFT JOIN professeurs p ON e.prof_surveillant_id = p.id
    """
    
    if selected_formation != "Toutes les spécialités":
        base_query += f" WHERE f.nom = '{selected_formation}'"
        
    base_query += " ORDER BY e.date_examen, e.creneau_debut"
    
    df_raw = load_data(base_query)
    
    if df_raw.empty:
        st.warning("Aucun examen planifié pour cette sélection.")
    else:
        df_display = df_raw.groupby(['date_examen', 'creneau_debut', 'creneau_fin', 'Module', 'Spécialité']).agg({
            'Salle': lambda x: ', '.join(sorted(list(set(x)))),
            'Surveillant': lambda x: ', '.join(sorted(list(set(x))))
        }).reset_index()
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        csv = df_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger le Planning", 
            csv, 
            f"planning_{datetime.date.today()}.csv", 
            "text/csv",
            key='download-csv'
        )
            
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: Répartition Salles ---
elif current_page == "Répartition Salles":
    st.markdown('<h1 style="text-align: center;">📍 Répartition des Étudiants</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Consultez la liste nominative des étudiants par salle d'examen.")
    
    # Cascade Filters
    conn = get_connection()
    depts = pd.read_sql("SELECT id, nom FROM departements", conn)
    dept_sel = st.selectbox("Faculté", depts['nom'])
    
    if dept_sel:
        dept_id = depts[depts['nom'] == dept_sel]['id'].values[0]
        formats = pd.read_sql(f"SELECT id, nom FROM formations WHERE dept_id = {dept_id}", conn)
        fmt_sel = st.selectbox("Spécialité", formats['nom'])
        
        if fmt_sel:
            # Get scheduled exams for this formation
            fmt_id = formats[formats['nom'] == fmt_sel]['id'].values[0]
            
            exams_list = pd.read_sql(f"""
                SELECT DISTINCT e.date_examen, m.nom, m.id as mid
                FROM examens e
                JOIN modules m ON e.module_id = m.id
                WHERE m.formation_id = {fmt_id}
                ORDER BY e.date_examen
            """, conn)
            
            if exams_list.empty:
                st.info("Aucun examen trouvé.")
            else:
                exam_choice_label = st.selectbox("Choisir l'Examen", 
                                                 exams_list.apply(lambda x: f"{x['date_examen']} - {x['nom']}", axis=1))
                
                if exam_choice_label:
                    selected_mid = exams_list[exams_list.apply(lambda x: f"{x['date_examen']} - {x['nom']}", axis=1) == exam_choice_label]['mid'].values[0]
                    selected_date = exam_choice_label.split(" - ")[0].strip()
                    
                    # Show Rooms and Students
                    room_assignments = pd.read_sql(f"""
                        SELECT s.nom as Salle, s.capacite, COUNT(ee.etudiant_id) as assigned_count,
                               e.id as exam_id
                        FROM examens e
                        JOIN lieux_examen s ON e.salle_id = s.id
                        LEFT JOIN examen_etudiants ee ON e.id = ee.examen_id
                        WHERE e.module_id = {selected_mid} AND e.date_examen = '{selected_date}'
                        GROUP BY s.nom
                    """, conn)
                    
                    for _, room_row in room_assignments.iterrows():
                        with st.expander(f"🚪 {room_row['Salle']} ({room_row['assigned_count']} étudiants)"):
                            students_in_room = pd.read_sql(f"""
                                SELECT et.nom, et.prenom, et.promo
                                FROM examen_etudiants ee
                                JOIN etudiants et ON ee.etudiant_id = et.id
                                WHERE ee.examen_id = {room_row['exam_id']}
                                ORDER BY et.nom
                            """, conn)
                            st.table(students_in_room)
    conn.close()
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Mon Planning (Student) ---
elif current_page == "Mon Planning" and role == "Étudiant":
    st.markdown('<h1 style="text-align: center;">👤 Mon Espace Étudiant</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Retrouvez votre planning avec **votre salle assignée**.")
    
    search_name = st.text_input("Rechercher votre Nom", placeholder="Ex: Benali...")
    
    if search_name:
        students = load_data(f"SELECT id, nom, prenom, promo FROM etudiants WHERE nom LIKE '%{search_name}%' OR prenom LIKE '%{search_name}%' LIMIT 5")
        
        if not students.empty:
            for _, stu in students.iterrows():
                with st.expander(f"📅 Planning de {stu['prenom']} {stu['nom']} ({stu['promo']})"):
                    # PRECISE ROOM ASSIGNMENT QUERY
                    my_exams = load_data(f"""
                        SELECT m.nom as Module, s.nom as "MA SALLE", e.date_examen, e.creneau_debut
                        FROM examen_etudiants ee
                        JOIN examens e ON ee.examen_id = e.id
                        JOIN modules m ON e.module_id = m.id
                        JOIN lieux_examen s ON e.salle_id = s.id
                        WHERE ee.etudiant_id = {stu['id']}
                        ORDER BY e.date_examen
                    """)
                    
                    if my_exams.empty:
                        st.info("Aucun examen trouvé (ou planning non généré avec affectation).")
                    else:
                        st.table(my_exams)
        else:
            st.warning("Aucun étudiant trouvé.")
            
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Mes Surveillances (Prof) ---
elif current_page == "Mes Surveillances" and role == "Professeur":
    st.markdown('<h1 style="text-align: center;">👨‍🏫 Mes Surveillances</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    profs = load_data("SELECT id, nom, prenom FROM professeurs ORDER BY nom")
    prof_names = [f"{p['nom']} {p['prenom']}" for _, p in profs.iterrows()]
    
    my_name = st.selectbox("Qui êtes-vous ?", prof_names)
    
    if my_name:
        p_id = profs[(profs['nom'] + " " + profs['prenom']) == my_name].iloc[0]['id']
        
        my_tasks = load_data(f"""
            SELECT e.date_examen, e.creneau_debut, e.creneau_fin, m.nom as Module, s.nom as Salle
            FROM examens e
            JOIN modules m ON e.module_id = m.id
            JOIN lieux_examen s ON e.salle_id = s.id
            WHERE e.prof_surveillant_id = {p_id}
            ORDER BY e.date_examen
        """)
        
        if my_tasks.empty:
            st.info("Vous n'avez aucune surveillance programmée.")
        else:
            st.dataframe(my_tasks, use_container_width=True)
            
    st.markdown('</div>', unsafe_allow_html=True)
