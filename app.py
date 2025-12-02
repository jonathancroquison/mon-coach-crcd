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
st.set_page_config(
    page_title="Campus Relation Client",
    layout="wide",
    page_icon="🎧",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Simulateur pédagogique CRCD - @croquison 2025"
    }
)

# --- CSS / DESIGN & ACCESSIBILITÉ ---
st.markdown("""
<style>
    /* TYPOGRAPHIE & LISIBILITÉ */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Helvetica, sans-serif;
    }
    
    /* Titre Principal (H1) */
    .titre-accueil { 
        font-size: 42px; 
        font-weight: 800; 
        color: #0F172A; /* Contraste fort (WCAG AAA) */
        line-height: 1.2;
        margin-top: -20px;
        margin-bottom: 15px;
    }
    
    /* Sous-titre */
    .sous-titre {
        font-size: 18px;
        color: #334155; /* Gris foncé lisible */
        margin-bottom: 25px;
        line-height: 1.5;
    }

    /* Cartes Objectifs */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
        border-left: 6px solid #2563EB; /* Marqueur visuel fort */
    }
    .card h3 { margin: 0 0 8px 0; font-size: 18px; color: #1E40AF; font-weight: 700; }
    .card p { margin: 0; font-size: 16px; color: #1E293B; }

    /* Boutons : Focus visible et contraste */
    .stButton>button { 
        width: 100%;
        border-radius: 8px; 
        font-weight: bold; 
        height: 3.5em;
        border: none;
        background-color: #2563EB;
        color: white;
        font-size: 16px; /* Texte plus grand */
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        transform: scale(1.01);
    }
    .stButton>button:focus {
        outline: 3px solid #FCD34D; /* Focus visible pour navigation clavier */
    }
    
    /* FOOTER (Pied de page) */
    .footer {
        width: 100%;
        text-align: center;
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #E2E8F0;
        color: #64748B;
        font-size: 14px;
        font-style: italic;
    }
    
    /* Score */
    .big-score { font-size: 60px; font-weight: 900; text-align: center; color: #1E3A8A; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION IA ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# --- FONCTIONS UTILITAIRES ---
def extraire_score(texte_coach):
    match = re.search(r"\[SCORE:(\d+)\]", texte_coach)
    return int(match.group(1)) if match else 0 

def afficher_barometre(score):
    st.markdown("---")
    st.subheader("📊 Baromètre de Performance")
    col_jauge, col_verdict = st.columns([3, 1])
    with col_jauge:
        st.progress(score / 100)
        # Utilisation de couleurs standards pour daltoniens (Rouge/Orange/Vert reste standard mais le texte aide)
        if score < 50: st.error(f"🔴 {score}/100 - Insuffisant")
        elif score < 80: st.warning(f"🟠 {score}/100 - En acquisition")
        else: st.success(f"🟢 {score}/100 - Maîtrisé")
    with col_verdict:
        st.markdown(f"<div class='big-score'>{score}</div>", unsafe_allow_html=True)

def transcrire_audio(audio_bytes):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        config = genai.types.GenerationConfig(temperature=0.0)
        response = model.generate_content(
            ["Transcris exactement en français. Si silence, réponds '...'", {"mime_type": "audio/webm", "data": audio_bytes}], 
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

def afficher_footer():
    st.markdown('<div class="footer">@croquison Création pédagogique 2025 - Tous droits réservés</div>', unsafe_allow_html=True)

@st.dialog("❓ Guide Rapide")
def afficher_notice():
    st.markdown("### 🎧 Comment s'entraîner ?\n1. **Choisissez un client**.\n2. **Cliquez sur 'Décrocher'**.\n3. **Parlez au client**.\n4. **Analysez** vos résultats.")

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# --- SIDEBAR (NAVIGATION) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=70, output_format="PNG") # Logo décoratif
    st.markdown("### Campus CRCD")
    st.markdown("---")
    
    # LOGIQUE BOUTON ACCUEIL : N'apparaît PAS si on est déjà sur Home
    if st.session_state.page != "home":
        if st.button("🏠 Retour Accueil"): st.session_state.page = "home"; st.rerun()
        
    if st.button("❓ Aide"): afficher_notice()

# =========================================================
# PAGE ACCUEIL
# =========================================================
if st.session_state.page == "home":
    
    col_text, col_visual = st.columns([1.4, 1])
    
    with col_text:
        st.markdown('<h1 class="titre-accueil">Excellence en<br>Relation Client</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sous-titre">Entraînez-vous face à des clients virtuels.<br>Améliorez votre discours, votre ton et votre réactivité.</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card">
            <h3>🛡️ Pratiquez sans risque</h3>
            <p>Un espace d'entraînement sécurisé pour tester vos réflexes.</p>
        </div>
        <div class="card">
            <h3>🗣️ Automatisez votre Trame</h3>
            <p>Ancrez les réflexes verbaux (SBAM, 4C) pour gagner en fluidité.</p>
        </div>
        <div class="card">
            <h3>⏱️ Maîtrisez le Temps (DMT)</h3>
            <p>Apprenez à concilier écoute active et rapidité.</p>
        </div>
        """, unsafe_allow_html=True)

    with col_visual:
        # Image avec texte alternatif (Alt) pour l'accessibilité
        st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=1000&auto=format&fit=crop", 
                 use_container_width=True)
        
        st.markdown("###") 
        if st.button("🚀 DÉMARRER L'ENTRAÎNEMENT", use_container_width=True):
            st.session_state.page = "choix_scenario"
            st.rerun()
        st.caption("👆 Accès au simulateur")

    st.markdown("---")
    
    with st.expander("📚 Glossaire Technique & Compétences"):
        for k, v in GLOSSAIRE.items():
            st.markdown(f"**🔹 {k}** : {v['definition']}")
            
    afficher_footer()

# =========================================================
# PAGE CHOIX SCENARIO
# =========================================================
elif st.session_state.page == "choix_scenario":
    st.markdown('<h1 style="text-align:center; color:#0F172A;">Choisissez votre interlocuteur</h1>', unsafe_allow_html=True)
    st.markdown("###")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=80)
        st.info("**Théo (Niveau 1)**\n\nAppel simple. Idéal pour valider la trame de base.")
        if st.button("Appeler Théo"): st.session_state.selected=SCENARIOS["SCENARIO_1"]; st.session_state.page="sim"; st.rerun()
    
    with c2:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140047.png", width=80)
        st.warning("**Sarah (Niveau 2)**\n\nCliente mécontente. Travail sur la gestion de conflit.")
        if st.button("Appeler Sarah"): st.session_state.selected=SCENARIOS["SCENARIO_2"]; st.session_state.page="sim"; st.rerun()
        
    with c3:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140037.png", width=80)
        st.error("**Marc (Niveau 3)**\n\nClient pressé. Objectif : Rebond commercial.")
        if st.button("Appeler Marc"): st.session_state.selected=SCENARIOS["SCENARIO_3"]; st.session_state.page="sim"; st.rerun()
    
    st.markdown("---")
    if st.button("⬅️ Retour"): st.session_state.page="home"; st.rerun()
    
    afficher_footer()

# =========================================================
# PAGE SIMULATION
# =========================================================
elif st.session_state.page == "sim":
    sc = st.session_state.selected
    
    with st.sidebar:
        st.success(f"Client : {sc['titre']}")
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER"):
                st.session_state.appel_en_cours=True; st.session_state.start_time=time.time(); st.session_state.messages=[]; st.rerun()
        else:
            st.metric("Chrono", f"{int(time.time()-st.session_state.start_time)}s")
            st.write("🎙️ **MICROPHONE :**")
            au = mic_recorder(start_prompt="🔴 Parler", stop_prompt="✋ Envoyer", key='rec', format="webm")
            st.write("")
            if st.button("🔴 RACCROCHER"):
                st.session_state.appel_en_cours=False; st.session_state.analyse_demandee=True; st.rerun()
        st.markdown("---")
        if st.button("🔙 Quitter"): st.session_state.page="choix_scenario"; st.session_state.appel_en_cours=False; st.rerun()

    st.subheader(f"📞 {sc['titre']}")
    
    for m in st.session_state.messages:
        if m["role"]!="system":
            with st.chat_message(m["role"], avatar=("🧑‍💻" if m["role"]=="user" else sc['image'])):
                st.write(m["content"])
                if m.get("audio"): st.audio(m["audio"], format="audio/mp3", start_time=0)

    if st.session_state.appel_en_cours and au and au['id']!=st.session_state.last_audio_id:
        st.session_state.last_audio_id = au['id']
        txt = transcrire_audio(au['bytes'])
        if txt: st.session_state.messages.append({"role":"user", "content":txt}); st.rerun()
    
    if st.session_state.appel_en_cours:
        if ti := st.chat_input("Réponse texte..."):
            st.session_state.messages.append({"role":"user", "content":ti}); st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"]=="user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=sc['image']):
            with st.spinner("..."):
                r = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1], sc['client_prompt'])
                a = parler(r)
                st.write(r)
                if a: st.audio(a, format='audio/mp3', start_time=0, autoplay=True)
        st.session_state.messages.append({"role":"assistant", "content":r, "audio":a})

    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Bilan du Coach")
        with st.spinner("Analyse..."):
            conv = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            res = analyse_coach(conv, sc['coach_prompt'])
            score = extraire_score(res)
            afficher_barometre(score)
            clean_res = res.replace(f"[SCORE:{score}]", "")
            st.info(clean_res)
            
            fb = f"BILAN\nDate: {time.strftime('%d/%m/%Y')}\nNOTE: {score}/100\n\n{clean_res}"
            vb = f"SCRIPT\n\n{conv}"
            
            st.write("### 💾 Sauvegarder")
            c1, c2 = st.columns(2)
            with c1: st.download_button("📥 Feedback", fb, "Feedback.txt", use_container_width=True)
            with c2: st.download_button("📜 Script", vb, "Script.txt", use_container_width=True)
            st.session_state.analyse_demandee = False
            
    afficher_footer()
