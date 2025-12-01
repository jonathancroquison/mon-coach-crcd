import streamlit as st
import google.generativeai as genai
import time

# --- IMPORTATION DES SCÉNARIOS ---
try:
    from prompts import SCENARIOS
except ImportError:
    st.error("Erreur : Le fichier prompts.py est introuvable ou mal configuré.")
    st.stop()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur CRCD Pro", layout="wide", page_icon="🎧")

# --- CSS POUR LE STYLE (Optionnel mais joli) ---
st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante. Configurez-la dans les Secrets.")

# --- FONCTIONS IA ---
def obtenir_reponse_gemini(message_utilisateur, historique, prompt_systeme):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash') # Ton modèle rapide
        
        history_gemini = []
        # On injecte le caractère spécifique de l'Avatar choisi
        history_gemini.append({"role": "user", "parts": [prompt_systeme]})
        history_gemini.append({"role": "model", "parts": ["C'est compris, je rentre dans le personnage."]})
        
        for msg in historique:
            if msg["role"] != "system":
                role_gemini = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role_gemini, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_gemini)
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

def analyse_coach(transcription, prompt_coach):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        full_prompt = prompt_coach + "\n\nTRANSCRIPTION DE L'APPEL:\n" + transcription
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- GESTION DE L'ÉTAT (NAVIGATION) ---
if "page" not in st.session_state: st.session_state.page = "notice"
if "selected_scenario" not in st.session_state: st.session_state.selected_scenario = None
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None

# =========================================================
# ÉCRAN 1 : LA NOTICE D'USAGE (ACCUEIL)
# =========================================================
if st.session_state.page == "notice":
    st.title("🎧 Bienvenue sur le Coach Virtuel CRCD")
    
    with st.expander("📖 LIRE LA NOTICE D'USAGE AVANT DE COMMENCER", expanded=True):
        st.markdown("""
        ### Objectifs Pédagogiques
        Cet outil est conçu pour vous entraîner aux fondamentaux de la Relation Client à Distance.
        
        **Les points clés évalués :**
        * ✅ **La Trame d'Appel :** Respect des étapes (SBAM, Découverte, Proposition, Congé).
        * ✅ **La Directivité :** Savoir garder le contrôle de l'entretien.
        * ✅ **La DMT :** Gérer son temps (le chronomètre tourne !).
        * ✅ **L'Écoute Active :** Reformulation et empathie.
        
        **Comment ça marche ?**
        1. Choisissez un **Avatar** (scénario).
        2. Cliquez sur **"Décrocher"**.
        3. Discutez avec le client (IA) comme au téléphone.
        4. Cliquez sur **"Raccrocher"** pour recevoir votre note et les conseils du Coach.
        """)
        
    if st.button("JE SUIS PRÊT - ACCÉDER AUX SCÉNARIOS ➡️"):
        st.session_state.page = "choix_scenario"
        st.rerun()

# =========================================================
# ÉCRAN 2 : LE CHOIX DES AVATARS
# =========================================================
elif st.session_state.page == "choix_scenario":
    st.title("Choisis ton client du jour")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.header("Avatar 1")
        st.info("👶 **Théo - Débutant**")
        st.write("Travail sur l'Identification & la Trame.")
        if st.button("Choisir Théo"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_1"]
            st.session_state.page = "simulation"
            st.rerun()

    with col2:
        st.header("Avatar 2")
        st.warning("😤 **Sarah - Difficile**")
        st.write("Travail sur la Rétention & Gestion de conflit.")
        if st.button("Choisir Sarah"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_2"]
            st.session_state.page = "simulation"
            st.rerun()

    with col3:
        st.header("Avatar 3")
        st.error("💼 **Marc - Expert**")
        st.write("Travail sur la Vente Additionnelle.")
        if st.button("Choisir Marc"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_3"]
            st.session_state.page = "simulation"
            st.rerun()

    if st.button("⬅️ Revenir à la notice"):
        st.session_state.page = "notice"
        st.rerun()

# =========================================================
# ÉCRAN 3 : LA SIMULATION (CHAT)
# =========================================================
elif st.session_state.page == "simulation":
    scenario = st.session_state.selected_scenario
    
    # Sidebar de contrôle
    with st.sidebar:
        st.title(f"{scenario['image']} Appel en cours")
        st.markdown(f"**{scenario['titre']}**")
        st.info(scenario['description'])
        
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER L'APPEL"):
                st.session_state.appel_en_cours = True
                st.session_state.start_time = time.time()
                st.session_state.messages = []
                st.session_state.analyse_demandee = False
                st.rerun()
        else:
            duree = int(time.time() - st.session_state.start_time)
            st.metric("⏱️ DMT", f"{duree} sec")
            
            if st.button("🔴 RACCROCHER & ANALYSER"):
                st.session_state.appel_en_cours = False
                st.session_state.analyse_demandee = True
                st.rerun()
        
        st.markdown("---")
        if st.button("🔙 Changer de scénario"):
            st.session_state.page = "choix_scenario"
            st.session_state.appel_en_cours = False
            st.rerun()

    # Zone de Chat
    st.header(f"📞 {scenario['titre']}")

    # Affichage historique
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"], avatar=("🧑‍💻" if msg["role"] == "user" else scenario['image'])):
                st.write(msg["content"])

    # Input User
    if st.session_state.appel_en_cours:
        reponse = st.chat_input("Votre réponse au client...")
        if reponse:
            st.session_state.messages.append({"role": "user", "content": reponse})
            st.rerun()

    # Réponse IA
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=scenario['image']):
            with st.spinner(f"{scenario['titre'].split(':')[1]} répond..."):
                rep_ia = obtenir_reponse_gemini(
                    st.session_state.messages[-1]["content"], 
                    st.session_state.messages[:-1],
                    scenario['client_prompt'] # On envoie le prompt spécifique de l'avatar choisi
                )
                st.write(rep_ia)
        st.session_state.messages.append({"role": "assistant", "content": rep_ia})

    # Feedback Coach
    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Analyse de ta performance")
        with st.spinner("Le coach relit la trame, vérifie la DMT et la directivité..."):
            txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            # On envoie le prompt spécifique du coach associé au scénario
            st.info(analyse_coach(txt, scenario['coach_prompt']))
            st.session_state.analyse_demandee = False
