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

    /* Sidebar Styles Removed */

    /* Mobile Responsiveness moved to bottom of CSS to ensure overrides work */

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

    /* Mobile Responsiveness (Placed last to override other styles) */
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
        
        h2, h3 {
            margin-top: 1rem !important;
        }

        .card {
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            border-radius: 16px !important;
        }
        
        .stMetric {
            padding: 1rem !important;
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
        }
        
        .stButton>button {
            height: 3rem !important;
            font-size: 0.9rem !important;
        }
    }
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

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #1e1b4b; letter-spacing: -1px; line-height: 1.2;">
                🏛️ UMBB <span style="color: #4338ca;">SCHED</span>
            </div>
            <div style="font-size: 0.8rem; color: #64748b; font-weight: 700; margin-top: 0.4rem;">
                SYSTÈME DE PLANIFICATION
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 👤 Identification")
    role = st.selectbox(
        "Rôle", 
        ["Étudiant", "Professeur", "Chef de Département", "Administrateur Examens", "Vice-Doyen / Doyen"],
        index=0
    )

    # Authentication
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
            if st.button("Se connecter", use_container_width=True):
                if pwd_input == PASSWORDS.get(role):
                    st.session_state[f'auth_{role}'] = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        else:
            is_authenticated = True
            if st.button("Déconnexion", use_container_width=True):
                st.session_state[f'auth_{role}'] = False
                st.rerun()

    # Navigation Menu
    current_page = "Tableau de bord" # Default
    if is_authenticated:
        st.markdown("---")
        st.markdown("### 📌 Menu")
        
        nav_options = ["Tableau de bord", "Voir Emplois du temps"]
        
        if role in ["Administrateur Examens", "Vice-Doyen / Doyen"]:
            nav_options.insert(1, "Créer Emploi du temps")
            
        if role == "Professeur":
            nav_options.append("Mes Surveillances")
            
        if role == "Étudiant":
            nav_options.append("Mon Planning")
            
        current_page = st.radio("Navigation", nav_options, label_visibility="collapsed")


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
        nb_examens = pd.read_sql("SELECT COUNT(*) FROM examens", conn).iloc[0,0]
        st.metric("📝 Total Examens", f"{nb_examens:,}")
        
    with m3:
        nb_salles = pd.read_sql("SELECT COUNT(DISTINCT salle_id) FROM examens", conn).iloc[0,0]
        total_salles = pd.read_sql("SELECT COUNT(*) FROM lieux_examen", conn).iloc[0,0]
        st.metric("🏛️ Salles Utilisées", f"{nb_salles}/{total_salles}")
        
    with m4:
        # Exams Today
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        nb_today = pd.read_sql(f"SELECT COUNT(*) FROM examens WHERE date_examen = '{today_str}'", conn).iloc[0,0]
        st.metric("📅 Examens Aujourd'hui", nb_today)
        
    conn.close()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Graphs
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📈 Examens par Faculté")
        df_dept = load_data("""
            SELECT d.nom as Faculté, COUNT(ex.id) as Examens
            FROM examens ex
            JOIN modules m ON ex.module_id = m.id
            JOIN formations f ON m.formation_id = f.id
            JOIN departements d ON f.dept_id = d.id
            GROUP BY d.nom
        """)
        if not df_dept.empty:
            fig = px.bar(df_dept, x='Faculté', y='Examens', color='Faculté', template='plotly_white')
            fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None, margin=dict(l=0,r=0,t=0,b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible.")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("🏁 Statut")
        st.write("Planification globale")
        fig_pie = px.pie(values=[nb_examens, 100], names=['Planifié', 'Total'], hole=0.7, color_discrete_sequence=['#4338ca', '#e2e8f0'])
        fig_pie.update_layout(showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=300, 
                             annotations=[dict(text=f'{nb_examens}', x=0.5, y=0.5, font_size=30, showarrow=False)])
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Créer Emploi du temps ---
elif current_page == "Créer Emploi du temps":
    st.markdown('<h1 style="text-align: center;">⚡ Générateur d\'Emploi du Temps</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Configuration de la Génération")
    
    with st.form("auto_schedule_form", border=False):
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            start_date = st.date_input("Date de début", datetime.date.today())
        with col_d2:
            end_date = st.date_input("Date de fin", datetime.date.today() + datetime.timedelta(days=14))
            
        formations = load_data("SELECT id, nom FROM formations")
        selected_formations = st.multiselect("Filtrer par Spécialité (Optionnel)", formations['nom'])
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            append_mode = st.checkbox("Mode Sans Conflit (Incremental)", value=True)
        
        submitted = st.form_submit_button("🚀 Lancer la Génération", use_container_width=True)
    
    if submitted:
        formation_ids = []
        if selected_formations:
            formation_ids = formations[formations['nom'].isin(selected_formations)]['id'].tolist()
            
        with st.spinner("Optimisation en cours..."):
            scheduler = ExamScheduler(DB_PATH)
            nb_gen = scheduler.generate_schedule(start_date, end_date, formation_ids, append=append_mode)
        
        st.success(f"✅ Génération terminée ! {nb_gen} examens planifiés.")
        st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Voir Emplois du temps ---
elif current_page == "Voir Emplois du temps":
    st.markdown('<h1 style="text-align: center;">🗓️ Consultation des Plannings</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Filter by Specialty
    formations = load_data("SELECT id, nom FROM formations ORDER BY nom")
    all_formats = ["Toutes les spécialités"] + formations['nom'].tolist()
    
    c_filter1, c_filter2 = st.columns([1, 2])
    with c_filter1:
        st.markdown("### 🔍 Filtres")
    with c_filter2:
        selected_formation = st.selectbox("Sélectionner une Spécialité", all_formats)
    
    # Query Data
    base_query = """
        SELECT 
            e.date_examen as Date, 
            e.creneau_debut as Début, 
            e.creneau_fin as Fin, 
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
    
    df_planning = load_data(base_query)
    
    if df_planning.empty:
        st.warning("Aucun examen planifié pour cette sélection.")
    else:
        st.dataframe(df_planning, use_container_width=True, hide_index=True)
        
        # Download
        csv = df_planning.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Télécharger le Planning (CSV)", 
            csv, 
            f"planning_{datetime.date.today()}.csv", 
            "text/csv",
            key='download-csv'
        )
            
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Mon Planning (Student) ---
elif current_page == "Mon Planning" and role == "Étudiant":
    st.markdown('<h1 style="text-align: center;">👤 Mon Espace Étudiant</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("Retrouvez votre planning d'examens personnel.")
    
    search_name = st.text_input("Rechercher votre Nom", placeholder="Ex: Benali...")
    
    if search_name:
        students = load_data(f"SELECT id, nom, prenom, promo FROM etudiants WHERE nom LIKE '%{search_name}%' OR prenom LIKE '%{search_name}%' LIMIT 5")
        
        if not students.empty:
            for _, stu in students.iterrows():
                with st.expander(f"📅 Planning de {stu['prenom']} {stu['nom']} ({stu['promo']})"):
                    my_exams = load_data(f"""
                        SELECT m.nom as Module, s.nom as salle, e.date_examen, e.creneau_debut
                        FROM examens e
                        JOIN modules m ON e.module_id = m.id
                        JOIN inscriptions i ON m.id = i.module_id
                        JOIN lieux_examen s ON e.salle_id = s.id
                        WHERE i.etudiant_id = {stu['id']}
                        ORDER BY e.date_examen
                    """)
                    if my_exams.empty:
                        st.info("Aucun examen trouvé.")
                    else:
                        st.table(my_exams)
        else:
            st.warning("Aucun étudiant trouvé.")
            
    st.markdown('</div>', unsafe_allow_html=True)


# --- PAGE: Mes Surveillances (Prof) ---
elif current_page == "Mes Surveillances" and role == "Professeur":
    st.markdown('<h1 style="text-align: center;">👨‍🏫 Mes Surveillances</h1>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # In a real app, we would know the logged-in user's ID. 
    # Here we simulate finding the prof by name since we don't have real login accounts linked to DB IDs in this demo.
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
