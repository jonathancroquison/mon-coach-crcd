import streamlit as st
import google.generativeai as genai
import time

# --- 1. CONFIG ET PROMPTS ---
try:
    from prompts import PROMPT_CLIENT, PROMPT_COACH
except ImportError:
    PROMPT_CLIENT = "Tu es un client."
    PROMPT_COACH = "Analyse l'appel."

st.set_page_config(page_title="Simulateur CRCD", layout="wide")

# --- 2. CONNEXION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante. Configurez-la dans les Secrets.")

def obtenir_reponse_gemini(message_utilisateur, historique):
    try:
        # ON UTILISE LE MODÈLE QUI EST DANS TA LISTE
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Construction de l'historique pour Gemini
        history_gemini = []
        # On force le contexte initial
        history_gemini.append({"role": "user", "parts": [PROMPT_CLIENT]})
        history_gemini.append({"role": "model", "parts": ["C'est noté, je suis prêt."]})
        
        for msg in historique:
            if msg["role"] != "system":
                # On adapte les rôles pour Gemini (user/model)
                role_gemini = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role_gemini, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_gemini)
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

def analyse_coach(transcription):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        # Le prompt du coach + la transcription
        full_prompt = PROMPT_COACH + "\n\nTRANSCRIPTION DE L'APPEL:\n" + transcription
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- 3. MÉMOIRE DE L'APPLI ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None

# --- 4. INTERFACE ---
with st.sidebar:
    st.title("🎧 Coach CRCD")
    st.success("Moteur : Gemini 2.0 Flash") # On affiche le nouveau moteur
    
    if st.button("🟢 DÉCROCHER"):
        st.session_state.appel_en_cours = True
        st.session_state.start_time = time.time()
        st.session_state.messages = [] 
        st.session_state.analyse_demandee = False
        st.rerun()

    if st.session_state.appel_en_cours and st.session_state.start_time:
        duree = int(time.time() - st.session_state.start_time)
        st.metric("DMT (Temps)", f"{duree} sec")

    if st.button("🔴 RACCROCHER & ANALYSER"):
        st.session_state.appel_en_cours = False
        st.session_state.analyse_demandee = True
        st.rerun()

# --- 5. ZONE DE CHAT ---
st.header("Simulation d'appel")

# Afficher l'historique
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"], avatar=("🧑‍💻" if msg["role"] == "user" else "👤")):
            st.write(msg["content"])

# Zone de saisie (Active seulement si appel en cours)
if st.session_state.appel_en_cours:
    reponse = st.chat_input("Votre réponse...")
    if reponse:
        # 1. Message apprenti
        st.session_state.messages.append({"role": "user", "content": reponse})
        st.rerun()

# Logique de réponse automatique après rechargement
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.appel_en_cours:
    with st.chat_message("user", avatar="🧑‍💻"):
        st.write(st.session_state.messages[-1]["content"])
        
    with st.spinner("Le client répond..."):
        rep_ia = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1])
        st.session_state.messages.append({"role": "assistant", "content": rep_ia})
        st.rerun()

# --- 6. FEEDBACK ---
if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
    st.divider()
    st.subheader("📝 Rapport du Coach")
    with st.spinner("Analyse de ta technicité..."):
        txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
        st.info(analyse_coach(txt))
        st.session_state.analyse_demandee = False
