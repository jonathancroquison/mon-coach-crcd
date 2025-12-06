import streamlit as st
from audio_recorder_streamlit import audio_recorder
import google.generativeai as genai
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Campus CRCD - Sarah", page_icon="😠")

# Récupération de la clé depuis les secrets
try:
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ Clé API introuvable dans les secrets Streamlit.")
        st.stop()
except Exception as e:
    st.error(f"Erreur de configuration : {e}")
    st.stop()

# --- 2. DÉFINITION DU MODÈLE ---
# On essaie de charger le modèle. Si ça échoue, on affiche les modèles disponibles.
try:
    # On utilise 'gemini-1.5-flash' ou 'gemini-1.5-flash-latest'
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erreur chargement modèle : {e}")

# --- 3. PERSONA (SARAH) ---
SARAH_PERSONA = (
    "Tu es Sarah, une cliente très mécontente (Niveau Rétention). "
    "Tu es furieuse, impatiente et agressive. "
    "Réponds en français. Tes phrases sont courtes, sèches et percutantes. "
    "Ne te calme pas facilement. Tu veux des résultats, pas du blabla."
)

# --- 4. FONCTION APPEL IA ---
def get_sarah_response(user_content, input_type):
    try:
        if input_type == "audio":
            # Mode Audio (Multimodal)
            response = model.generate_content([
                SARAH_PERSONA,
                "L'utilisateur me dit ceci vocalement (réponds-lui sur le même ton) :",
                {
                    "mime_type": "audio/webm", 
                    "data": user_content
                }
            ])
        else:
            # Mode Texte
            response = model.generate_content([
                SARAH_PERSONA,
                f"L'utilisateur écrit : {user_content}"
            ])
        return response.text
    except Exception as e:
        return f"Erreur technique (Sarah est partie) : {e}"

# --- 5. INTERFACE ---
st.title("📞 Simulation Client")
st.markdown("**Interlocuteur :** Sarah (Niveau Rétention)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage historique
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- 6. INPUTS ---

# Zone texte (Bas de page)
text_input = st.chat_input("Votre réponse...")

# Zone Audio (Sidebar)
with st.sidebar:
    st.markdown("### 🎙️ Micro")
    # Le key="audio_recorder_unique" aide à éviter les conflits
    audio_bytes = audio_recorder(
        text="Cliquer pour parler",
        recording_color="#e8b62c",
        neutral_color="#6aa36f",
        icon_size="2x",
        key="audio_recorder_unique"
    )

# --- 7. TRAITEMENT ---

final_content = None
type_input = None

if text_input:
    final_content = text_input
    type_input = "text"

# Fix Firefox : on vérifie que l'audio fait plus de 500 octets
elif audio_bytes and len(audio_bytes) > 500:
    final_content = audio_bytes
    type_input = "audio"

# --- 8. RÉPONSE ---

if final_content:
    # 1. Afficher l'input utilisateur
    if type_input == "text":
        st.session_state.messages.append({"role": "user", "content": final_content})
        with st.chat_message("user"):
            st.write(final_content)
    else:
        note = "🎤 *[Audio envoyé]*"
        st.session_state.messages.append({"role": "user", "content": note})
        with st.chat_message("user"):
            st.markdown(note)

    # 2. Réponse de Sarah
    with st.chat_message("assistant"):
        with st.spinner("Sarah réfléchit..."):
            reply = get_sarah_response(final_content, type_input)
            st.write(reply)
            
    st.session_state.messages.append({"role": "assistant", "content": reply})
