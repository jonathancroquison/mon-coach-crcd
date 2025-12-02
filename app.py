import streamlit as st
import google.generativeai as genai
import time
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import io

# --- IMPORTATION DES DONNÉES EXTERNES ---
try:
    from prompts import SCENARIOS
    from glossaire_data import GLOSSAIRE
except ImportError:
    st.error("🚨 Erreur critique : Les fichiers 'prompts.py' ou 'glossaire_data.py' sont manquants sur GitHub.")
    st.stop()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur CRCD", layout="wide", page_icon="🎧")

# --- CSS / DESIGN ---
st.markdown("""
<style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .titre-accueil { font-size: 40px; font-weight: bold; color: #4F8BF9; text-align: center; margin-bottom: 20px;}
    .obj-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4F8BF9;}
    h3 { color: #31333F; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.warning("⚠️ Clé API manquante dans les Secrets.")

# --- FONCTIONS UTILITAIRES ---

@st.dialog("❓ Notice d'utilisation")
def afficher_notice():
    st.markdown("""
    ### Comment utiliser ce simulateur ?
    Ce simulateur est un **"Bac à sable"** pour vous entraîner sans risque.
    
    1. **Choisissez un Avatar** (Client) selon la difficulté voulue.
    2. **Cliquez sur 'Décrocher'** pour lancer l'appel.
    3. **Échangez avec le client** :
       - Soit par écrit (Clavier).
       - Soit à l'oral (Micro) pour plus de réalisme.
    4. **Raccrochez** quand vous avez fini.
    5. **Analysez votre performance** grâce au bilan du Coach IA.
    """)

def transcrire_audio(audio_bytes):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = "Tu es un expert en transcription. Écris EXACTEMENT ce que tu entends en français. Si silence/bruit, réponds '...'."
        config = genai.types.GenerationConfig(temperature=0.0)
        response = model.generate_content([prompt, {"mime_type": "audio/webm", "data": audio_bytes}], generation_config=config)
        texte = response.text.strip()
        return None if texte in ["...", ""] else texte
    except: return None

def parler(texte, langue='fr'):
    try:
        tts = gTTS(text=texte, lang=langue, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        return audio_fp
    except: return None

def obtenir_reponse_gemini(user_msg, hist, prompt_sys):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        history_gemini = [{"role": "user", "parts": [prompt_sys]}, {"role": "model", "parts": ["Compris."]}]
        for m in hist:
            if m["role"] != "system":
                history_gemini.append({"role": ("user" if m["role"] == "user" else "model"), "parts": [m["content"]]})
        return model.start_chat(history=history_gemini).send_message(user_msg).text
    except Exception as e: return f"Erreur IA : {e}"

def analyse_coach(transcript, prompt_coach):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt_coach + "\n\nTRANSCRIPTION:\n" + transcript).text
    except Exception as e: return f"Erreur Coach : {e}"

# --- GESTION ÉTAT ---
if "page" not in st.session_state: st.session_state.page = "home"
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# --- BARRE SUPÉRIEURE (MENU PERMANENT) ---
col_logo, col_vide, col_notice = st.columns([1, 4, 1])
with col_logo:
    if st.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
with col_notice:
    if st.button("❓ Aide / Notice"): afficher_notice()

st.markdown("---")

# =========================================================
# PAGE 1 : ACCUEIL & GLOSSAIRE (LANDING PAGE)
# =========================================================
if st.session_state.page == "home":
    st.markdown('<div class="titre-accueil">🎓 Simulateur CRCD</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: gray;'>La plateforme d'entraînement pour les futurs experts de la Relation Client</p>", unsafe_allow_html=True)
    
    col_gauche, col_droite = st.columns([1, 1], gap="large")

    with col_gauche:
        st.subheader("🎯 Vos Objectifs")
        st.markdown("""
        <div class="obj-card">
        <b>1. Droit à l'erreur</b><br>
        Entraînez-vous sans risque avant de prendre vos premiers vrais appels. Testez des approches, trompez-vous et apprenez.
        </div>
        <div class="obj-card">
        <b>2. Maîtrise de la Trame</b><br>
        Acquérez les réflexes verbaux (SBAM, 4C) pour dérouler un entretien fluide et professionnel.
        </div>
        <div class="obj-card">
        <b>3. Gestion du Stress & DMT</b><br>
        Apprenez à gérer votre temps et vos émotions face à des clients difficiles ou bavards.
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("🚀 LANCER LE SIMULATEUR", use_container_width=True):
            st.session_state.page = "choix_scenario"
            st.rerun()

    with col_droite:
        st.subheader("📚 Glossaire Technique")
        st.info("💡 Cliquez sur les termes pour voir la définition et les exemples.")
        
        for terme, data in GLOSSAIRE.items():
            with st.expander(f"📌 {terme}"):
                st.markdown(f"**Définition :** {data['definition']}")
                st.markdown(f"**Exemple :** *{data['exemple']}*")
                st.caption(f"🎯 **Intérêt Métier :** {data['interet']}")

# =========================================================
# PAGE 2 : CHOIX DU SCÉNARIO
# =========================================================
elif st.session_state.page == "choix_scenario":
    st.title("Choix de la simulation")
    st.markdown("Quel type de client souhaitez-vous affronter aujourd'hui ?")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.info(f"👶 **{SCENARIOS['SCENARIO_1']['titre']}**")
        if st.button("Choisir Théo"):
            st.session_state.selected = SCENARIOS["SCENARIO_1"]; st.session_state.page = "sim"; st.rerun()
    with c2:
        st.warning(f"😤 **{SCENARIOS['SCENARIO_2']['titre']}**")
        if st.button("Choisir Sarah"):
            st.session_state.selected = SCENARIOS["SCENARIO_2"]; st.session_state.page = "sim"; st.rerun()
    with c3:
        st.error(f"💼 **{SCENARIOS['SCENARIO_3']['titre']}**")
        if st.button("Choisir Marc"):
            st.session_state.selected = SCENARIOS["SCENARIO_3"]; st.session_state.page = "sim"; st.rerun()

# =========================================================
# PAGE 3 : SIMULATION
# =========================================================
elif st.session_state.page == "sim":
    scenario = st.session_state.selected
    
    with st.sidebar:
        st.header(f"Appel : {scenario['titre'].split(':')[1]}")
        
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER", use_container_width=True):
                st.session_state.appel_en_cours = True; st.session_state.start_time = time.time(); st.session_state.messages = []; st.rerun()
        else:
            st.metric("⏱️ Temps", f"{int(time.time() - st.session_state.start_time)} s")
            st.write("🎙️ **PARLER :**")
            audio = mic_recorder(start_prompt="🔴 Micro ON", stop_prompt="✋ Envoyer", key='rec', format="webm")
            st.write("")
            if st.button("🔴 RACCROCHER", use_container_width=True):
                st.session_state.appel_en_cours = False; st.session_state.analyse_demandee = True; st.rerun()
        
        st.markdown("---")
        if st.button("🔙 Changer de client"): st.session_state.page = "choix_scenario"; st.session_state.appel_en_cours = False; st.rerun()

    st.subheader(f"📞 {scenario['titre']}")

    for m in st.session_state.messages:
        if m["role"]!="system":
            with st.chat_message(m["role"], avatar=("🧑‍💻" if m["role"]=="user" else scenario['image'])):
                st.write(m["content"])
                if m.get("audio"): st.audio(m["audio"], format="audio/mp3", start_time=0)

    if st.session_state.appel_en_cours and audio and audio['id'] != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio['id']
        txt = transcrire_audio(audio['bytes'])
        if txt: st.session_state.messages.append({"role": "user", "content": txt}); st.rerun()
        else: st.toast("Audio non compris", icon="🔇")

    if st.session_state.appel_en_cours:
        if txt_in := st.chat_input("Message texte..."):
            st.session_state.messages.append({"role": "user", "content": txt_in}); st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=scenario['image']):
            with st.spinner("..."):
                rep = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1], scenario['client_prompt'])
                aud = parler(rep)
                st.write(rep)
                if aud: st.audio(aud, format='audio/mp3', start_time=0, autoplay=True)
        st.session_state.messages.append({"role": "assistant", "content": rep, "audio": aud})

    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider(); st.subheader("📝 Bilan du Coach")
        with st.spinner("Analyse..."):
            conv = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            res = analyse_coach(conv, scenario['coach_prompt'])
            st.info(res)
            dl_txt = f"DATE: {time.strftime('%d/%m/%Y')}\nSCENARIO: {scenario['titre']}\n\nBILAN:\n{res}\n\nTRANSCRIPTION:\n{conv}"
            st.download_button("📥 TÉLÉCHARGER LE BILAN", data=dl_txt, file_name="Bilan_CRCD.txt")
            st.session_state.analyse_demandee = False
