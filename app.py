import streamlit as st
import google.generativeai as genai
import time
import re
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import io

# --- IMPORTATION DES DONNÉES ---
try:
    from prompts import SCENARIOS
    from glossaire_data import GLOSSAIRE
except ImportError:
    st.error("🚨 Erreur critique : Les fichiers 'prompts.py' ou 'glossaire_data.py' sont manquants.")
    st.stop()

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur CRCD", layout="wide", page_icon="🎧")

# --- CSS / DESIGN ---
st.markdown("""
<style>
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .titre-accueil { font-size: 40px; font-weight: bold; color: #4F8BF9; text-align: center; margin-bottom: 10px;}
    .obj-card { background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #4F8BF9;}
    .big-score { font-size: 50px; font-weight: bold; text-align: center; color: #333; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FONCTIONS UTILITAIRES ---

def extraire_score(texte_coach):
    """Cherche le motif [SCORE:XX] dans le texte"""
    match = re.search(r"\[SCORE:(\d+)\]", texte_coach)
    if match:
        return int(match.group(1))
    return 0 

def afficher_barometre(score):
    """Affiche une jauge visuelle selon le score"""
    st.markdown("---")
    st.subheader("📊 Baromètre de Performance")
    col_jauge, col_verdict = st.columns([3, 1])
    with col_jauge:
        st.progress(score / 100)
        if score < 50:
            st.error(f"🔴 Score : {score}/100 - À revoir")
        elif score < 80:
            st.warning(f"🟠 Score : {score}/100 - En acquisition")
        else:
            st.success(f"🟢 Score : {score}/100 - Maîtrisé")
    with col_verdict:
        st.markdown(f"<div class='big-score'>{score}</div>", unsafe_allow_html=True)

def transcrire_audio(audio_bytes):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        config = genai.types.GenerationConfig(temperature=0.0)
        response = model.generate_content(
            ["Transcris exactement. Si silence, réponds '...'", {"mime_type": "audio/webm", "data": audio_bytes}], 
            generation_config=config
        )
        t = response.text.strip()
        return None if t in ["...", ""] else t
    except: return None

def parler(texte, langue='fr'):
    try:
        tts = gTTS(text=texte, lang=langue, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

def obtenir_reponse_gemini(msg, hist, prompt):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        h = [{"role": "user", "parts": [prompt]}, {"role": "model", "parts": ["Compris."]}]
        for m in hist:
            if m["role"]!="system": h.append({"role":("user" if m["role"]=="user" else "model"), "parts":[m["content"]]})
        return model.start_chat(history=h).send_message(msg).text
    except Exception as e: return f"Erreur : {e}"

def analyse_coach(txt, prompt):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        return model.generate_content(prompt + "\n\nTRANSCRIPTION:\n" + txt).text
    except: return "Erreur analyse."

@st.dialog("❓ Notice")
def afficher_notice():
    st.markdown("### Guide Simulateur\n1. Choisir Avatar\n2. Décrocher\n3. Parler\n4. Analyser.")

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# HEADER
c1, c2, c3 = st.columns([1,4,1])
with c1: 
    if st.button("🏠 Accueil"): st.session_state.page = "home"; st.rerun()
with c3: 
    if st.button("❓ Aide"): afficher_notice()
st.markdown("---")

# =========================================================
# PAGE ACCUEIL
# =========================================================
if st.session_state.page == "home":
    st.markdown('<div class="titre-accueil">🎓 Simulateur CRCD</div>', unsafe_allow_html=True)
    
    c_vide1, c_btn, c_vide2 = st.columns([1, 2, 1])
    with c_btn:
        st.markdown("###")
        if st.button("🚀 LANCER UNE SIMULATION MAINTENANT", use_container_width=True):
            st.session_state.page = "choix_scenario"
            st.rerun()
        st.markdown("###")

    col_g, col_d = st.columns([1, 1], gap="large")
    with col_g:
        st.subheader("🎯 Objectifs")
        st.markdown("""
        <div class="obj-card"><b>1. Droit à l'erreur :</b> Testez vos réflexes sans risque.</div>
        <div class="obj-card"><b>2. Trame d'appel :</b> Maîtrisez le SBAM et les 4C.</div>
        <div class="obj-card"><b>3. Gestion DMT :</b> Apprenez à être efficace et concis.</div>
        """, unsafe_allow_html=True)
    
    with col_d:
        st.subheader("📚 Glossaire")
        for k, v in GLOSSAIRE.items():
            with st.expander(f"📌 {k}"):
                st.write(f"**Déf :** {v['definition']}")
                st.caption(f"💡 {v['interet']}")

# =========================================================
# PAGE CHOIX
# =========================================================
elif st.session_state.page == "choix_scenario":
    st.title("Choix du Client")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("👶 **Théo**"); st.write("Débutant")
        if st.button("Théo"): st.session_state.selected = SCENARIOS["SCENARIO_1"]; st.session_state.page="sim"; st.rerun()
    with c2:
        st.warning("😤 **Sarah**"); st.write("Difficile")
        if st.button("Sarah"): st.session_state.selected = SCENARIOS["SCENARIO_2"]; st.session_state.page="sim"; st.rerun()
    with c3:
        st.error("💼 **Marc**"); st.write("Expert")
        if st.button("Marc"): st.session_state.selected = SCENARIOS["SCENARIO_3"]; st.session_state.page="sim"; st.rerun()

# =========================================================
# PAGE SIMULATION
# =========================================================
elif st.session_state.page == "sim":
    sc = st.session_state.selected
    
    with st.sidebar:
        st.header(sc['titre'])
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER"):
                st.session_state.appel_en_cours=True; st.session_state.start_time=time.time(); st.session_state.messages=[]; st.rerun()
        else:
            st.metric("Temps", f"{int(time.time()-st.session_state.start_time)}s")
            st.write("🎙️ **PARLER :**")
            au = mic_recorder(start_prompt="🔴 Micro", stop_prompt="✋ Envoyer", key='rec', format="webm")
            st.write("")
            if st.button("🔴 RACCROCHER & NOTER"):
                st.session_state.appel_en_cours=False; st.session_state.analyse_demandee=True; st.rerun()
        st.markdown("---")
        if st.button("🔙 Quitter"): st.session_state.page="choix_scenario"; st.session_state.appel_en_cours=False; st.rerun()

    st.subheader(f"📞 {sc['titre']}")
    
    # Chat
    for m in st.session_state.messages:
        if m["role"]!="system":
            with st.chat_message(m["role"], avatar=("🧑‍💻" if m["role"]=="user" else sc['image'])):
                st.write(m["content"])
                if m.get("audio"): st.audio(m["audio"], format="audio/mp3", start_time=0)

    # Logique Audio/Texte
    if st.session_state.appel_en_cours and au and au['id']!=st.session_state.last_audio_id:
        st.session_state.last_audio_id = au['id']
        txt = transcrire_audio(au['bytes'])
        if txt: st.session_state.messages.append({"role":"user", "content":txt}); st.rerun()
    
    if st.session_state.appel_en_cours:
        if ti := st.chat_input("Message..."):
            st.session_state.messages.append({"role":"user", "content":ti}); st.rerun()

    # Réponse IA
    if st.session_state.messages and st.session_state.messages[-1]["role"]=="user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=sc['image']):
            with st.spinner("..."):
                r = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1], sc['client_prompt'])
                a = parler(r)
                st.write(r)
                if a: st.audio(a, format='audio/mp3', start_time=0, autoplay=True)
        st.session_state.messages.append({"role":"assistant", "content":r, "audio":a})

    # --- ANALYSE & BAROMÈTRE ---
    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Bilan du Coach")
        
        with st.spinner("Analyse du verbatim et calcul du score..."):
            conv = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            res = analyse_coach(conv, sc['coach_prompt'])
            
            score_final = extraire_score(res)
            afficher_barometre(score_final)
            
            texte_propre = res.replace(f"[SCORE:{score_final}]", "")
            st.info(texte_propre)
            
            # Contenu des fichiers
            fb_txt = f"BILAN PÉDAGOGIQUE\nDate: {time.strftime('%d/%m/%Y')}\nNOTE: {score_final}/100\n\n{texte_propre}"
            vb_txt = f"VERBATIM APPEL\nDate: {time.strftime('%d/%m/%Y')}\n\n{conv}"
            
            st.write("### 💾 Sauvegarder votre travail")
            c_dl1, c_dl2 = st.columns(2)
            with c_dl1:
                st.download_button("📥 FEEDBACK (Bilan)", fb_txt, "Feedback.txt", use_container_width=True)
            with c_dl2:
                st.download_button("📜 VERBATIM (Script)", vb_txt, "Verbatim.txt", use_container_width=True)
            
            st.session_state.analyse_demandee = False
