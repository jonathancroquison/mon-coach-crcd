
import streamlit as st
import google.generativeai as genai
import time
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import io

# --- IMPORTATION DES SCÉNARIOS ---
try:
    from prompts import SCENARIOS
except ImportError:
    st.error("Erreur : Le fichier prompts.py est introuvable.")
    st.stop()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur CRCD Audio", layout="wide", page_icon="🎧")

# --- CSS POUR LE STYLE ---
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; }
    .audio-player { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- CONNEXION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante. Configurez-la dans les Secrets.")

# --- FONCTIONS ---

def transcrire_audio(audio_bytes):
    """
    Envoie l'audio à Gemini pour transcription.
    CORRECTION : Utilise le format WebM (natif navigateur) pour éviter les erreurs.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt_transcription = """
        Tu es un expert en transcription phonétique.
        Ta tâche : Convertir cet audio en texte français.
        Règles IMPÉRATIVES :
        1. Écris EXACTEMENT ce que tu entends.
        2. Si le son est inaudible, s'il n'y a que du bruit de fond ou du silence, RÉPONDS UNIQUEMENT PAR "..." (trois points).
        3. N'invente AUCUN mot. Ne complète pas les phrases.
        """
        
        # On force la température à 0 pour la fidélité
        config = genai.types.GenerationConfig(temperature=0.0)
        
        # CORRECTION : On précise le mime_type audio/webm
        response = model.generate_content(
            [prompt_transcription, {"mime_type": "audio/webm", "data": audio_bytes}],
            generation_config=config
        )
        
        texte = response.text.strip()
        if texte == "..." or texte == "":
            return None
        return texte

    except Exception as e:
        st.error(f"Erreur technique lors de la transcription : {e}")
        return None

def parler(texte, langue='fr'):
    """Transforme le texte en fichier audio MP3 via Google TTS"""
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
        
        # Construction de l'historique pour Gemini
        history_gemini = []
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

# --- GESTION DE L'ÉTAT (SESSION STATE) ---
if "page" not in st.session_state: st.session_state.page = "notice"
if "selected_scenario" not in st.session_state: st.session_state.selected_scenario = None
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# =========================================================
# ÉCRAN 1 : LA NOTICE D'USAGE
# =========================================================
if st.session_state.page == "notice":
    st.title("🎧 Coach CRCD - Mode Vocal 🎙️")
    st.info("Système audio connecté et prêt.")
    
    with st.expander("📖 COMMENT UTILISER LA VOIX ?", expanded=True):
        st.markdown("""
        **Instructions :**
        1. Cliquez sur **"🔴 Enregistrer"** (Barre latérale).
        2. Parlez **distinctement**.
        3. Cliquez sur **"⏹️ Envoyer"** (Stop).
        4. Attendez que votre texte apparaisse.
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
        st.info(f"👶 **{SCENARIOS['SCENARIO_1']['titre']}**")
        st.write("Travail sur l'Identification & la Trame.")
        if st.button("Choisir Théo"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_1"]
            st.session_state.page = "simulation"
            st.rerun()

    with col2:
        st.header("Avatar 2")
        st.warning(f"😤 **{SCENARIOS['SCENARIO_2']['titre']}**")
        st.write("Travail sur la Rétention & Gestion de conflit.")
        if st.button("Choisir Sarah"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_2"]
            st.session_state.page = "simulation"
            st.rerun()

    with col3:
        st.header("Avatar 3")
        st.error(f"💼 **{SCENARIOS['SCENARIO_3']['titre']}**")
        st.write("Travail sur la Vente Additionnelle.")
        if st.button("Choisir Marc"):
            st.session_state.selected_scenario = SCENARIOS["SCENARIO_3"]
            st.session_state.page = "simulation"
            st.rerun()
            
    if st.button("⬅️ Retour"):
        st.session_state.page = "notice"
        st.rerun()

# =========================================================
# ÉCRAN 3 : LA SIMULATION (CHAT & VOIX)
# =========================================================
elif st.session_state.page == "simulation":
    scenario = st.session_state.selected_scenario
    
    # --- SIDEBAR DE CONTRÔLE ---
    with st.sidebar:
        st.title(f"{scenario['image']} Appel en cours")
        st.markdown(f"**{scenario['titre']}**")
        
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
            
            st.markdown("---")
            st.write("**🎙️ PARLER AU CLIENT :**")
            
            # --- BOUTON MICROPHONE CORRIGÉ (WEBM) ---
            audio_data = mic_recorder(
                start_prompt="🔴 Enregistrer (Parlez fort)",
                stop_prompt="⏹️ Envoyer",
                just_once=True,
                key='recorder',
                format="webm" # <--- IMPORTANT : Format WebM pour éviter les erreurs
            )
            
            st.markdown("---")
            if st.button("🔴 RACCROCHER & ANALYSER"):
                st.session_state.appel_en_cours = False
                st.session_state.analyse_demandee = True
                st.rerun()
        
        st.markdown("---")
        if st.button("🔙 Changer de scénario"):
            st.session_state.page = "choix_scenario"
            st.session_state.appel_en_cours = False
            st.rerun()

    # --- ZONE PRINCIPALE (CHAT) ---
    st.header(f"📞 {scenario['titre']}")

    # 1. Affichage historique
    for msg in st.session_state.messages:
        if msg["role"] != "system":
            with st.chat_message(msg["role"], avatar=("🧑‍💻" if msg["role"] == "user" else scenario['image'])):
                st.write(msg["content"])
                if "audio" in msg and msg["audio"] is not None:
                    st.audio(msg["audio"], format="audio/mp3")

    # 2. LOGIQUE MICROPHONE
    if st.session_state.appel_en_cours and audio_data is not None:
        current_audio_id = audio_data['id']
        if current_audio_id != st.session_state.last_audio_id:
            st.session_state.last_audio_id = current_audio_id
            
            with st.spinner("Transcription de votre voix..."):
                # On envoie les bytes directement (format WebM)
                texte_apprenant = transcrire_audio(audio_data['bytes'])
            
            if texte_apprenant:
                st.session_state.messages.append({"role": "user", "content": texte_apprenant})
                st.rerun()
            else:
                st.toast("⚠️ Audio non compris ou silencieux.", icon="🔇")

    # 3. LOGIQUE CLAVIER
    if st.session_state.appel_en_cours:
        reponse_texte = st.chat_input("Ou écrivez votre réponse ici...")
        if reponse_texte:
            st.session_state.messages.append({"role": "user", "content": reponse_texte})
            st.rerun()

    # 4. RÉPONSE IA
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=scenario['image']):
            with st.spinner(f"{scenario['titre'].split(':')[1]} réfléchit..."):
                rep_ia = obtenir_reponse_gemini(
                    st.session_state.messages[-1]["content"], 
                    st.session_state.messages[:-1],
                    scenario['client_prompt']
                )
                
                audio_file = parler(rep_ia)
                st.write(rep_ia)
                if audio_file:
                    st.audio(audio_file, format='audio/mp3', start_time=0)
        
        st.session_state.messages.append({"role": "assistant", "content": rep_ia, "audio": audio_file})

    # 5. FEEDBACK COACH & TÉLÉCHARGEMENT
    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Rapport du Coach")
        
        with st.spinner("Le coach analyse votre appel..."):
            txt_conversation = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            analyse_resultat = analyse_coach(txt_conversation, scenario['coach_prompt'])
            
            st.info(analyse_resultat)
            
            # Création du fichier Bilan
            rapport_complet = f"""
            BILAN DE FORMATION CRCD
            Date : {time.strftime("%d/%m/%Y à %H:%M")}
            Scénario : {scenario['titre']}
            DMT : {int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0} sec
            
            --- ANALYSE ---
            {analyse_resultat}
            
            --- TRANSCRIPTION ---
            {txt_conversation}
            """
            
            st.download_button(
                label="📥 TÉLÉCHARGER MON BILAN (TXT)",
                data=rapport_complet,
                file_name=f"Bilan_{scenario['titre'].split(':')[0].strip()}.txt",
                mime="text/plain"
            )
            
            st.session_state.analyse_demandee = False
