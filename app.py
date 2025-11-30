import streamlit as st
import openai
import time
# On essaie d'importer les prompts, sinon on utilise des valeurs par défaut (sécurité)
try:
    from prompts import PROMPT_CLIENT, PROMPT_COACH
except ImportError:
    PROMPT_CLIENT = "Tu es un client."
    PROMPT_COACH = "Analyse l'appel."

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Simulateur CRCD", layout="wide")

# RECUPERATION DE LA CLE SECRETE (On gère les deux cas pour éviter les bugs)
if "OPENAI_API_KEY" in st.secrets:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
else:
    # Cas où la clé n'est pas encore configurée
    st.warning("⚠️ Clé API non trouvée. Configurez-la dans les 'Secrets' de Streamlit.")
    openai.api_key = "TA_CLE_API_OPENAI_ICI"

# --- 2. MÉMOIRE DE L'APPLICATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": PROMPT_CLIENT}]

if "appel_en_cours" not in st.session_state:
    st.session_state.appel_en_cours = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# --- 3. INTERFACE VISUELLE (SIDEBAR) ---
with st.sidebar:
    st.title("🎧 Coach CRCD")
    st.markdown("Entraînement : **Gestion de la Directivité**")
    
    if st.button("🟢 DÉCROCHER L'APPEL"):
        st.session_state.appel_en_cours = True
        st.session_state.start_time = time.time()
        st.session_state.messages = [{"role": "system", "content": PROMPT_CLIENT}]
        st.session_state.analyse_demandee = False 
        st.rerun()

    if st.session_state.appel_en_cours and st.session_state.start_time:
        duree = int(time.time() - st.session_state.start_time)
        st.metric("Temps d'appel (DMT)", f"{duree} sec")
        if duree > 180:
            st.warning("⚠️ Attention DMT !")

    if st.button("🔴 RACCROCHER & ANALYSER"):
        st.session_state.appel_en_cours = False
        st.session_state.analyse_demandee = True
        st.rerun()

# --- 4. LE CHAT ---
st.header("Simulation d'appel - Assurance Auto")

for msg in st.session_state.messages:
    if msg["role"] != "system":
        icone = "🧑‍💻" if msg["role"] == "user" else "👤"
        with st.chat_message(msg["role"], avatar=icone):
            st.write(msg["content"])

if st.session_state.appel_en_cours:
    reponse_apprenti = st.chat_input("Votre réponse au client...")
    if reponse_apprenti:
        st.session_state.messages.append({"role": "user", "content": reponse_apprenti})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.write(reponse_apprenti)

        with st.spinner("Le client répond..."):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=st.session_state.messages
                )
                msg_ia = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": msg_ia})
                with st.chat_message("assistant", avatar="👤"):
                    st.write(msg_ia)
            except Exception as e:
                st.error(f"Erreur : {e}")

# --- 5. LE FEEDBACK ---
if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
    st.divider()
    st.subheader("📝 Analyse de votre appel")
    with st.spinner("Le coach analyse..."):
        conversation_texte = ""
        for msg in st.session_state.messages:
            if msg["role"] != "system":
                conversation_texte += f"{msg['role']}: {msg['content']}\n"
        
        prompt_final = PROMPT_COACH + "\n\nTRANSCRIPTION:\n" + conversation_texte
        
        try:
            feedback = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt_final}]
            )
            st.success(feedback.choices[0].message.content)
            st.session_state.analyse_demandee = False 
        except Exception as e:
            st.error(f"Erreur coach : {e}")
