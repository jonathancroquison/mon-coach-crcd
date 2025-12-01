import streamlit as st
import google.generativeai as genai
import time
from gtts import gTTS # Pour que l'IA parle
from streamlit_mic_recorder import mic_recorder # Pour le micro
import io

# --- IMPORT SCENARIOS ---
try:
    from prompts import SCENARIOS
except ImportError:
    st.error("Erreur prompts.py")
    st.stop()

st.set_page_config(page_title="Simulateur CRCD Audio", layout="wide", page_icon="🎧")

# --- CSS (Design) ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; }
    .audio-player { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante.")

# --- FONCTIONS ---

def transcrire_audio(audio_bytes):
    """Envoie l'audio à Gemini pour le transformer en texte"""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        # On demande à Gemini d'écouter et d'écrire
        prompt = "Écoute cet audio et transcris exactement ce qui est dit, sans ajouter de commentaires."
        response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": audio_bytes}])
        return response.text
    except Exception as e:
        return f"Erreur transcription : {e}"

def parler(texte, langue='fr'):
    """Transforme le texte en fichier audio MP3"""
    try:
        tts = gTTS(text=texte, lang=langue, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        return audio_fp
    except Exception as e:
        return None

def obtenir_reponse_gemini(message_utilisateur, historique, prompt_systeme):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        history_gemini = [{"role": "user", "parts": [prompt_systeme]}, 
                          {"role": "model", "parts": ["Compris."]}]
        
        for msg in historique:
            if msg["role"] != "system":
                r = "user" if msg["role"] == "user" else "model"
                history_gemini.append({"role": r, "parts": [msg["content"]]})
        
        chat = model.start_chat(history=history_gemini)
        response = chat.send_message(message_utilisateur)
        return response.text
    except Exception as e:
        return f"Erreur IA : {e}"

def analyse_coach(transcription, prompt_coach):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt_coach + "\n\nTRANSCRIPTION:\n" + transcription)
        return response.text
    except Exception as e:
        return f"Erreur Coach : {e}"

# --- STATE ---
if "page" not in st.session_state: st.session_state.page = "notice"
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None # Pour éviter les boucles du micro

# --- NAVIGATION ---

# 1. NOTICE
if st.session_state.page == "notice":
    st.title("🎧 Coach CRCD - Mode Vocal 🎙️")
    st.info("Nouveau : Vous pouvez maintenant PARLER au client !")
    st.markdown("""
    **Comment utiliser la voix ?**
    1. Dans la simulation, cliquez sur le bouton **Micro** dans la barre latérale.
    2. Parlez (votre navigateur demandera l'autorisation).
    3. Arrêtez l'enregistrement : l'IA vous répondra à l'oral !
    """)
    if st.button("JE SUIS PRÊT ➡️"):
        st.session_state.page = "choix_scenario"
        st.rerun()

# 2. CHOIX
elif st.session_state.page == "choix_scenario":
    st.title("Choix du Client")
    c1, c2, c3 = st.columns(3)
    
    with c1: 
        if st.button("👶 Théo (Facile)"): 
            st.session_state.selected = SCENARIOS["SCENARIO_1"]
            st.session_state.page = "simulation"
            st.rerun()
    with c2: 
        if st.button("😤 Sarah (Difficile)"): 
            st.session_state.selected = SCENARIOS["SCENARIO_2"]
            st.session_state.page = "simulation"
            st.rerun()
    with c3: 
        if st.button("💼 Marc (Expert)"): 
            st.session_state.selected = SCENARIOS["SCENARIO_3"]
            st.session_state.page = "simulation"
            st.rerun()

# 3. SIMULATION
elif st.session_state.page == "simulation":
    scenario = st.session_state.selected
    
    # SIDEBAR : Commandes
    with st.sidebar:
        st.title(f"{scenario['image']} {scenario['titre']}")
        
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER"):
                st.session_state.appel_en_cours = True
                st.session_state.start_time = time.time()
                st.session_state.messages = []
                st.session_state.analyse_demandee = False
                st.rerun()
        else:
            duree = int(time.time() - st.session_state.start_time)
            st.metric("⏱️ Temps", f"{duree} s")
            
            st.markdown("---")
            st.write("**🎙️ PARLER AU CLIENT :**")
            # Composant Micro
            audio_data = mic_recorder(
                start_prompt="🔴 Enregistrer",
                stop_prompt="⏹️ Envoyer",
                just_once=True,
                key='recorder'
            )
            
            st.markdown("---")
            if st.button("🔴 RACCROCHER"):
                st.session_state.appel_en_cours = False
                st.session_state.analyse_demandee = True
                st.rerun()

    # ZONE CENTRALE
    st.header(f"📞 Appel avec {scenario['titre'].split(':')[1]}")

    # Affichage Historique
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"], avatar=("🧑‍💻" if msg["role"] == "user" else scenario['image'])):
                st.write(msg["content"])
                # Si c'est un message audio de l'IA, on affiche le lecteur
                if "audio" in msg:
                    st.audio(msg["audio"], format="audio/mp3")

    # LOGIQUE MICROPHONE (Si audio reçu)
    if st.session_state.appel_en_cours and audio_data is not None:
        # On vérifie que c'est un nouvel enregistrement pour éviter les répétitions
        current_audio_id = audio_data['id']
        if current_audio_id != st.session_state.last_audio_id:
            st.session_state.last_audio_id = current_audio_id
            
            # 1. On transcrit l'audio
            with st.spinner("Transcription de votre voix..."):
                texte_apprenant = transcrire_audio(audio_data['bytes'])
            
            # 2. On ajoute le message de l'apprenant
            st.session_state.messages.append({"role": "user", "content": texte_apprenant})
            st.rerun()

    # LOGIQUE CLAVIER (Alternative)
    if st.session_state.appel_en_cours:
        reponse_texte = st.chat_input("Ou écrivez votre réponse ici...")
        if reponse_texte:
            st.session_state.messages.append({"role": "user", "content": reponse_texte})
            st.rerun()

    # RÉPONSE DE L'IA
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=scenario['image']):
            with st.spinner("Le client réfléchit..."):
                # A. Texte
                rep_ia = obtenir_reponse_gemini(
                    st.session_state.messages[-1]["content"], 
                    st.session_state.messages[:-1],
                    scenario['client_prompt']
                )
                
                # B. Audio (Synthèse vocale)
                audio_file = parler(rep_ia)
                
                st.write(rep_ia)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', start_time=0)
        
        # On sauvegarde le message ET l'audio dans l'historique
        st.session_state.messages.append({"role": "assistant", "content": rep_ia, "audio": audio_file})

    # COACH
    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Analyse du Coach")
        with st.spinner("Analyse..."):
            txt = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            st.info(analyse_coach(txt, scenario['coach_prompt']))
            st.session_state.analyse_demandee = False
