import streamlit as st
import requests
import base64
import sqlite3
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# 1. Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Mushroom AI Classifier",
    page_icon="🍄",
    layout="wide"
)

# --------------------------------------------------
# 2. Database Logic
# --------------------------------------------------
def init_db():
    conn = sqlite3.connect('mushroom_stats.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (odor TEXT, spore TEXT, gill TEXT, ring TEXT, surface TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def save_log(odor, spore, gill, ring, surface, result):
    conn = sqlite3.connect('mushroom_stats.db')
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", (odor, spore, gill, ring, surface, result))
    conn.commit()
    conn.close()

def reset_db():
    conn = sqlite3.connect('mushroom_stats.db')
    c = conn.cursor()
    c.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

init_db()

# --------------------------------------------------
# 3. Azure Credentials
# --------------------------------------------------
ENDPOINT = st.secrets["AZURE_ENDPOINT"]
API_KEY = st.secrets["AZURE_API_KEY"]

# --------------------------------------------------
# 4. Background & Custom CSS
# --------------------------------------------------
def set_bg(bin_file):
    try:
        with open(bin_file, "rb") as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()

        st.markdown(f"""
        <style>
        /* Animacija za rezultate */
        @keyframes fadeInUp {{
            0% {{ opacity: 0; transform: translateY(20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}

        .stApp {{
            background-image:
                linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)),
                url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-attachment: fixed;
        }}
        .result-card {{
            background: rgba(0,0,0,0.85);
            padding: 25px;
            border-radius: 12px;
            border-left: 8px solid #2e7d32;
            color: white;
            animation: fadeInUp 0.8s ease-out forwards;
        }}
        .home-card {{
            background: rgba(0,0,0,0.7);
            padding: 30px;
            border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 20px;
        }}
        .poison {{
            border-left: 8px solid #d32f2f !important;
        }}
        h1, h2, h3, h4, label, p, .stTabs [data-baseweb="tab"] {{
            color: white !important;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p {{
            color: white !important;
        }}
        .main-content {{
            padding-top: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)
    except:
        pass

set_bg("pozadina.jpg")

# --------------------------------------------------
# 5. Maps
# --------------------------------------------------
odor_map = {"Almond": 0, "Anise": 3, "Creosote": 1, "Fishy": 8, "Foul": 2, "Musty": 4, "None": 5, "Pungent": 6, "Spicy": 7}
spore_map = {"Black": 2, "Brown": 3, "Buff": 0, "Chocolate": 1, "Green": 5, "Orange": 4, "Purple": 6, "White": 7, "Yellow": 8}
gill_map = {"Black": 4, "Brown": 5, "Gray": 2, "Pink": 7, "White": 10, "Chocolate": 3, "Purple": 9, "Red": 8, "Buff": 0, "Green": 1, "Yellow": 11, "Orange": 6}
ring_map = {"Pendant": 4, "Evanescent": 0, "Large": 2, "Flaring": 1, "None": 3}
surface_map = {"Smooth": 2, "Fibrous": 0, "Silky": 1, "Scaly": 3}

# --------------------------------------------------
# 6. SIDEBAR - ADMIN CONTROLS
# --------------------------------------------------
with st.sidebar:
    st.title("⚙️ Settings")
    st.write("Admin database controls")
    if st.button("🚨 RESET ALL DATA"):
        reset_db()
        st.success("Database cleared!")
        st.rerun()

# --------------------------------------------------
# 7. UI Logic & Tabs
# --------------------------------------------------
tab_home, tab_analysis, tab_stats = st.tabs(["HOME", "ANALYSIS", "STATISTICS"])

# --- TAB: HOME ---
with tab_home:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.markdown("""
        <div class="home-card">
            <h1>Welcome to Mushroom Classifier!</h1>
            <p>This system utilizes an SVM (Support Vector Machine) algorithm to predict mushroom edibility based on morphological features.</p>
            <hr>
            <h3>Instructions</h3>
            <p>Navigate to the <b>AI Analysis</b> tab to enter the characteristics of your specimen. 
            The system will query the Azure AI Endpoint in real-time to provide a classification.</p>
            <p style='color: #ffc107 !important;'><b>Warning:</b> Results are for educational purposes only. 
            Never consume mushrooms based solely on AI predictions.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB: ANALYSIS ---
with tab_analysis:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.title("Mushroom Classifier")
    col1, col2 = st.columns([2, 1.2], gap="large")

    with col1:
        with st.form("mushroom_form"):
            st.write("### Specimen Characteristics")
            c1, c2 = st.columns(2)
            with c1:
                u_odor = st.selectbox("Odor", list(odor_map.keys()))
                u_spore = st.selectbox("Spore Print Color", list(spore_map.keys()))
                u_gill = st.selectbox("Gill Color", list(gill_map.keys()))
            with c2:
                u_ring = st.selectbox("Ring Type", list(ring_map.keys()))
                u_surface = st.selectbox("Stalk Surface Above Ring", list(surface_map.keys()))
            submit = st.form_submit_button("RUN ANALYSIS")

    with col2:
        st.write("### Analysis Panel")
        if submit:
            row_values = [float(odor_map[u_odor]), float(spore_map[u_spore]), 
                          float(gill_map[u_gill]), float(ring_map[u_ring]), 
                          float(surface_map[u_surface])]
            
            payload = {"data": [row_values]}
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY.strip()}"}

            with st.spinner("Analyzing..."):
                try:
                    response = requests.post(ENDPOINT, json=payload, headers=headers)
                    result = response.json()
                    if "predictions" in result:
                        prediction = result["predictions"][0]
                        is_poison = prediction == "p"
                        res_text = "POISONOUS" if is_poison else "EDIBLE"
                        res_class = "result-card poison" if is_poison else "result-card"
                        
                        affirmation = (
                            "Specimen is classified as hazardous. The chosen characteristics are strong indicators of toxicity." 
                            if is_poison else 
                            "Specimen is classified as safe. The combination aligns with known edible mushroom patterns."
                        )

                        save_log(u_odor, u_spore, u_gill, u_ring, u_surface, res_text)

                        st.markdown(f"""
                            <div class="{res_class}">
                                <h2>{res_text}</h2>
                                <p style="font-size:1.1em; line-height:1.5;">{affirmation}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if not is_poison: st.balloons()
                    else: st.error("Error in model response.")
                except Exception as e: st.error(f"Azure Connection Error: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

# --- TAB: STATISTICS (S POPRAVLJENIM GRAFIKONIMA) ---
with tab_stats:
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.header("Global Specimen Insights")
    
    conn = sqlite3.connect('mushroom_stats.db')
    df = pd.read_sql_query("SELECT * FROM logs", conn)
    conn.close()

    if not df.empty:
        # 1. Red: Heatmap i Pie Chart
        r1_c1, r1_c2 = st.columns(2)
        with r1_c1:
            st.write("#### Odor vs. Result Density")
            heatmap_df = df.groupby(['odor', 'result']).size().reset_index(name='count')
            fig_heat = px.density_heatmap(heatmap_df, x="odor", y="result", z="count", 
                                         color_continuous_scale="Viridis", text_auto=True)
            fig_heat.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_heat, use_container_width=True)
        
        with r1_c2:
            st.write("#### Spore Print Composition")
            fig_pie = px.pie(df, names="spore", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig_pie, use_container_width=True)

        # 2. Red: Sunburst
        st.write("#### Ring Type Hijerarhija (Ring -> Result)")
        fig_sun = px.sunburst(df, path=['ring', 'result'], color='result',
                             color_discrete_map={"POISONOUS": "#d32f2f", "EDIBLE": "#2e7d32"})
        fig_sun.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig_sun, use_container_width=True)

        # 3. Red: Parallel Categories (ISPRAVLJENO)
        st.write("#### Multi-Feature Path (Odor -> Gill -> Result)")
        df_para = df.copy()
        df_para['color_numeric'] = df_para['result'].map({"POISONOUS": 1, "EDIBLE": 0})
        
        fig_para = px.parallel_categories(
            df_para, 
            dimensions=['odor', 'gill', 'result'],
            color="color_numeric",
            color_continuous_scale=[[0, "#2e7d32"], [1, "#d32f2f"]]
        )
        fig_para.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)', 
            font_color="white",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_para, use_container_width=True)
    else:
        st.info("The database is currently empty. Run an analysis to generate stats.")
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------------------------------------
# 8. Global Footer
# --------------------------------------------------
st.markdown("""
    <style>
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        border-top: 1px solid rgba(255,255,255,0.2);
        padding: 15px 0; text-align: center;
        background: rgba(0,0,0,0.8); color: rgba(255,255,255,0.6);
        font-size: 0.9em; z-index: 9999;
    }
    .main-content { padding-bottom: 100px; }
    </style>
    <div class="footer">
        Demo project. Never rely on AI alone for mushroom identification.<br>
        <b>© 2026 SVM Mushroom Intelligence System | All Rights Reserved</b>
    </div>
""", unsafe_allow_html=True)