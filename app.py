import streamlit as st
import google.generativeai as genai
import time

# Import des prompts
try:
    from prompts import PROMPT_CLIENT, PROMPT_COACH
except ImportError:
    PROMPT_CLIENT = "Tu es un client."
    PROMPT_COACH = "Analyse l'appel."

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Simulateur CRCD", layout="wide")

# Configuration de la clé
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API non trouvée.")

# --- 2. FONCTIONS IA ---
def obtenir_reponse_gemini(message_utilisateur, historique):
    try:
        # ON UTILISE LE MODÈLE STANDARD (PLUS SÛR)
        model = genai.GenerativeModel('gemini-pro')
        
        # On construit l'historique manuellement pour Gemini Pro
        history_gemini = []
        # On injecte le rôle caché
        history_gemini.append({"role": "user", "parts": [PROMPT_CLIENT]})
        history_gemini.append({"role": "model", "parts": ["D'accord, je suis prêt à jouer le rôle du client."]})
        
        for msg in historique:
            if msg["role"] != "system":
                role_gemini = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": role_gemini, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_gemini)
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        return f"Erreur technique : {e}"

def analyse_coach(transcription):
    try:
        # ON UTILISE LE MODÈLE STANDARD ICI AUSSI
        model = genai.GenerativeModel('gemini-pro')
        prompt_complet = PROMPT_COACH + "\n\nTRANSCRIPTION:\n" + transcription
        response = model.generate_content(prompt_complet)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- 3. MÉMOIRE ---
if "messages" not in st.session_state:
    st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state:
    st.session_state.appel_en_cours = False
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- 4. INTERFACE ---
with st.sidebar:
    st.title("🎧 Coach CRCD")
    st.info("Moteur : Gemini Pro (Stable)")
    
    if st.button("🟢 DÉCROCHER"):
        st.session_state.appel_en_cours = True
        st.session_state.start_time = time.time()
        st.session_state.messages = [] 
        st.session_state.analyse_demandee = False
        st.rerun()

    if st.session_state.appel_en_cours and st.session_state.start_time:
        duree = int(time.time() - st.session_state.start_time)
        st.metric("DMT", f"{duree} sec")

    if st.button("🔴 RACCROCHER"):
        st.session_state.appel_en_cours = False
        st.session_state.analyse_demandee = True
        st.rerun()

# --- 5. CHAT ---
st.header("Simulation d'appel")

for msg in st.session_state.messages:
    if msg["role"] != "system":
        icone = "🧑‍💻" if msg["role"] == "user" else "👤"
        with st.chat_message(msg["role"], avatar=icone):
            st.write(msg["content"])

if st.session_state.appel_en_cours:
    reponse_apprenti = st.chat_input("Votre réponse...")
    if reponse_apprenti:
        st.session_state.messages.append({"role": "user", "content": reponse_apprenti})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(reponse_apprenti)

        with st.spinner("Le client répond..."):
            reponse_ia = obtenir_reponse_gemini(reponse_apprenti, st.session_state.messages[:-1])
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
            with st.chat_message("assistant", avatar="👤"):
                st.write(reponse_ia)

# --- 6. FEEDBACK ---
if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
    st.divider()
    st.subheader("📝 Rapport du Coach")
    with st.spinner("Analyse en cours..."):
        texte_appel = ""
        for msg in st.session_state.messages:
            role = "Conseiller" if msg["role"] == "user" else "Client"
            texte_appel += f"{role}: {msg['content']}\n"
        feedback = analyse_coach(texte_appel)
        st.markdown(feedback)
        st.session_state.analyse_demandee = False
