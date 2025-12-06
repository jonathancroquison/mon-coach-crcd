import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Campus CRCD - Sarah", page_icon="😠")

# RÉCUPÉRATION DE LA CLÉ DEPUIS LES SECRETS STREAMLIT
# Cela remplace la clé "en dur" par la clé sécurisée
try:
    # Vérifiez que le nom ici ("GOOGLE_API_KEY") correspond à celui dans vos secrets Streamlit
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    
    # Modèle Gemini 1.5 Flash (Rapide, Gratuit & Multimodal)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("❌ Erreur de clé API. Vérifiez vos 'Secrets' dans Streamlit Cloud.")
    st.info("Assurez-vous d'avoir ajouté: GOOGLE_API_KEY = 'votre_clé' dans les réglages.")
    st.stop()

# --- 2. PERSONA (SARAH) ---
SARAH_PERSONA = (
    "Tu es Sarah, une cliente furieuse et impatiente (Niveau Rétention). "
    "Tu as eu une horrible expérience client. "
    "Tu parles français. Tes réponses sont courtes, sèches et directes. "
    "Tu ne te calmes pas facilement. Si on te parle, réponds du tac au tac."
)

# --- 3. FONCTION D'APPEL IA ---
def get_sarah_response(user_content, input_type):
    """Envoie le texte ou l'audio à Gemini"""
    try:
        if input_type == "audio":
            # Gemini écoute directement l'audio (pas de transcription nécessaire)
            response = model.generate_content([
                SARAH_PERSONA,
                "L'utilisateur vient de me dire ceci vocalement (réponds-lui) :",
                {
                    "mime_type": "audio/webm", # Format standard du web
                    "data": user_content
                }
            ])
        else:
            # Gemini lit le texte
            response = model.generate_content([
                SARAH_PERSONA,
                f"L'utilisateur me dit : {user_content}"
            ])
        return response.text
    except Exception as e:
        return f"Problème de connexion (Sarah ne répond pas) : {e}"

# --- 4. INTERFACE ---
st.title("🎓 Campus CRCD")
st.caption("Simulation : Client Mécontent (Mode Gratuit)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Afficher l'historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. ZONE DE SAISIE (AVEC FIX FIREFOX) ---

# Saisie Texte (Bas de page)
text_input = st.chat_input("Répondre à Sarah...")

# Saisie Audio (Sidebar pour stabilité)
with st.sidebar:
    st.markdown("### 🎙️ Réponse Vocale")
    audio_bytes = audio_recorder(
        text="Cliquez pour parler",
        recording_color="#e8b62c", 
        neutral_color="#6aa36f",
        icon_size="2x",
        key="audio_rec"
    )

# --- 6. LOGIQUE DE PRIORITÉ ---

final_content = None
type_input = None

# A. Priorité au texte écrit
if text_input:
    final_content = text_input
    type_input = "text"

# B. Sinon Audio (Si valide et > 500 octets pour éviter le bug Firefox)
elif audio_bytes and len(audio_bytes) > 500:
    final_content = audio_bytes
    type_input = "audio"

# --- 7. TRAITEMENT ---

if final_content:
    # 1. Message Utilisateur
    if type_input == "text":
        st.session_state.messages.append({"role": "user", "content": final_content})
        with st.chat_message("user"):
            st.markdown(final_content)
    else:
        # Note pour l'audio
        note = "🎤 *[Message Vocal envoyé]*"
        st.session_state.messages.append({"role": "user", "content": note})
        with st.chat_message("user"):
            st.markdown(note)

    # 2. Réponse de Sarah (Spinner pendant le calcul)
    with st.chat_message("assistant"):
        with st.spinner("Sarah réfléchit..."):
            ai_reply = get_sarah_response(final_content, type_input)
            st.markdown(ai_reply)
    
    # 3. Sauvegarde Réponse
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
