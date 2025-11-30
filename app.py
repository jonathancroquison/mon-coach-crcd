import streamlit as st
import google.generativeai as genai
import time

# On importe les scénarios (pas besoin de changer prompts.py, ça reste du texte)
try:
    from prompts import PROMPT_CLIENT, PROMPT_COACH
except ImportError:
    PROMPT_CLIENT = "Tu es un client."
    PROMPT_COACH = "Analyse l'appel."

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Simulateur CRCD", layout="wide")

# Configuration de la clé Google Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API non trouvée. Configurez-la dans les 'Secrets' de Streamlit.")

# --- 2. FONCTIONS UTILES ---
def obtenir_reponse_gemini(message_utilisateur, historique):
    """Envoie la conversation à Gemini et récupère la réponse"""
    try:
        # On prépare le modèle avec le rôle du client
        model = genai.GenerativeModel(
            'gemini-1.5-flash', 
            system_instruction=PROMPT_CLIENT
        )
        
        # On transforme l'historique Streamlit pour Gemini
        chat = model.start_chat(history=[
            {"role": "user" if msg["role"] == "user" else "model", "parts": msg["content"]}
            for msg in historique if msg["role"] != "system"
        ])
        
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        return f"Erreur : {e}"

def analyse_coach(transcription):
    """Demande à Gemini d'analyser l'appel"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt_complet = PROMPT_COACH + "\n\nTRANSCRIPTION:\n" + transcription
        response = model.generate_content(prompt_complet)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- 3. MÉMOIRE DE L'APPLICATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [] # Historique vide au début

if "appel_en_cours" not in st.session_state:
    st.session_state.appel_en_cours = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- 4. INTERFACE (SIDEBAR) ---
with st.sidebar:
    st.title("🎧 Coach CRCD (Google Version)")
    st.markdown("Moteur : **Gemini Flash (Gratuit)**")
    
    if st.button("🟢 DÉCROCHER L'APPEL"):
        st.session_state.appel_en_cours = True
        st.session_state.start_time = time.time()
        st.session_state.messages = [] # Reset
        st.session_state.analyse_demandee = False
        st.rerun()

    if st.session_state.appel_en_cours and st.session_state.start_time:
        duree = int(time.time() - st.session_state.start_time)
        st.metric("Temps d'appel", f"{duree} sec")

    if st.button("🔴 RACCROCHER & ANALYSER"):
        st.session_state.appel_en_cours = False
        st.session_state.analyse_demandee = True
        st.rerun()

# --- 5. ZONE DE CHAT ---
st.header("Simulation d'appel")

# Affichage des messages
for msg in st.session_state.messages:
    icone = "🧑‍💻" if msg["role"] == "user" else "👤"
    with st.chat_message(msg["role"], avatar=icone):
        st.write(msg["content"])

# Zone de saisie
if st.session_state.appel_en_cours:
    reponse_apprenti = st.chat_input("Votre réponse...")
    if reponse_apprenti:
        # 1. Afficher message apprenti
        st.session_state.messages.append({"role": "user", "content": reponse_apprenti})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(reponse_apprenti)

        # 2. Réponse IA (Gemini)
        with st.spinner("Le client répond..."):
            reponse_ia = obtenir_reponse_gemini(reponse_apprenti, st.session_state.messages[:-1])
            
            st.session_state.messages.append({"role": "assistant", "content": reponse_ia})
            with st.chat_message("assistant", avatar="👤"):
                st.write(reponse_ia)

# --- 6. FEEDBACK COACH ---
if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
    st.divider()
    st.subheader("📝 Analyse du Coach")
    with st.spinner("Analyse en cours..."):
        # On compile le texte pour le coach
        texte_appel = ""
        for msg in st.session_state.messages:
            role = "Conseiller" if msg["role"] == "user" else "Client"
            texte_appel += f"{role}: {msg['content']}\n"
            
        feedback = analyse_coach(texte_appel)
        st.info(feedback)
        st.session_state.analyse_demandee = False
            st.error(f"Erreur coach : {e}")
