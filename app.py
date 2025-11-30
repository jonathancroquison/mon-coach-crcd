import streamlit as st
import google.generativeai as genai
import time

# --- CONFIG ET PROMPTS ---
try:
    from prompts import PROMPT_CLIENT, PROMPT_COACH
except ImportError:
    PROMPT_CLIENT = "Tu es un client."
    PROMPT_COACH = "Analyse l'appel."

st.set_page_config(page_title="Simulateur CRCD", layout="wide")

# --- MOTEUR IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante dans les Secrets.")

def obtenir_reponse_gemini(message_utilisateur, historique):
    try:
        # ON REVIENT SUR LE MODÈLE FLASH (LE PLUS FIABLE APRÈS VIDAGE CACHE)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        history_gemini = []
        # Initialisation forcée pour éviter les erreurs de contexte
        history_gemini.append({"role": "user", "parts": [PROMPT_CLIENT]})
        history_gemini.append({"role": "model", "parts": ["Compris."]})\
        
        for msg in historique:
            if msg["role"] != "system":
                r = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": r, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_gemini)
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        # Si Flash échoue, message d'erreur clair
        return f"Erreur IA : {e}"

def analyse_coach(transcription):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(PROMPT_COACH + "\n\nTRANSCRIPTION:\n" + transcription)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- INTERFACE ---
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None

with st.sidebar:
    st.title("🎧 Coach CRCD")
    st.success("Moteur : Gemini 1.5 Flash")
    
    if st.button("🟢 DÉCROCHER"):
        st.session_state.appel_en_cours = True
        st.session_state.start_time = time.time()
        st.session_state.messages = [] 
        st.session_state.analyse_demandee = False
        st.rerun()

    if st.session_state.appel_en_cours and st.session_state.start_time:
        st.metric("Temps", f"{int(time.time() - st.session_state.start_time)} sec")

    if st.button("🔴 RACCROCHER"):
        st.session_state.appel_en_cours = False
        st.session_state.analyse_demandee = True
        st.rerun()

st.header("Simulation d'appel")

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"], avatar=("🧑‍💻" if msg["role"] == "user" else "👤")):
            st.write(msg["content"])

if st.session_state.appel_en_cours:
    reponse = st.chat_input("Votre réponse...")
    if reponse:
        st.session_state.messages.append({"role": "user", "content": reponse})
        st.rerun()

# Réponse IA au rechargement
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.spinner("..."):
        rep_ia = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1])
        st.session_state.messages.append({"role": "assistant", "content": rep_ia})
        st.rerun()

if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
    st.divider()
    with st.spinner("Analyse..."):
        txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
        st.info(analyse_coach(txt))
        st.session_state.analyse_demandee = False
