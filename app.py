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
    initial_sidebar_state="expanded"
)

# --- CSS / DESIGN AVANCÉ ---
st.markdown("""
<style>
    /* Style général */
    .main { background-color: #f8f9fa; }
    
    /* Titre Principal */
    .titre-accueil { 
        font-family: 'Helvetica Neue', sans-serif;
        font-size: 45px; 
        font-weight: 800; 
        color: #1E3A8A; /* Bleu nuit */
        margin-bottom: 10px;
    }
    
    /* Sous-titre */
    .sous-titre {
        font-size: 20px;
        color: #64748B;
        margin-bottom: 30px;
    }

    /* Cartes (Objectifs & Glossaire) */
    .card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 15px;
        border-left: 5px solid #3B82F6; /* Bordure bleue */
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-5px); /* Petit effet de levier au survol */
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Boutons personnalisés */
    .stButton>button { 
        border-radius: 30px; 
        font-weight: bold; 
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        if score < 50:
            st.error(f"🔴 {score}/100 - Niveau Insuffisant")
        elif score < 80:
            st.warning(f"🟠 {score}/100 - En cours d'acquisition")
        else:
            st.success(f"🟢 {score}/100 - Compétence Maîtrisée")
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

@st.dialog("❓ Guide Rapide")
def afficher_notice():
    st.markdown("""
    ### 🎧 Comment s'entraîner ?
    1. **Choisissez un client** dans le menu.
    2. **Cliquez sur 'Décrocher'**.
    3. **Parlez au client** (Micro ou Clavier).
    4. **Analysez** vos résultats à la fin.
    """)

# --- NAVIGATION ---
if "page" not in st.session_state: st.session_state.page = "home"
if "messages" not in st.session_state: st.session_state.messages = [] 
if "appel_en_cours" not in st.session_state: st.session_state.appel_en_cours = False
if "start_time" not in st.session_state: st.session_state.start_time = None
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

# --- SIDEBAR PERMANENTE (LOGO) ---
with st.sidebar:
    # Image du logo (URL fiable)
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
    st.markdown("### Campus CRCD")
    st.markdown("---")
    if st.button("🏠 Retour Accueil"): st.session_state.page = "home"; st.rerun()
    if st.button("❓ Aide / Notice"): afficher_notice()

# =========================================================
# PAGE ACCUEIL (DESIGN PRO)
# =========================================================
if st.session_state.page == "home":
    
    # En-tête avec Colonnes
    col_text, col_img = st.columns([1.5, 1])
    
    with col_text:
        st.markdown('<div class="titre-accueil">Devenez un Expert<br>de la Relation Client</div>', unsafe_allow_html=True)
        st.markdown('<div class="sous-titre">Simulateur conversationnel assisté par Intelligence Artificielle.</div>', unsafe_allow_html=True)
        
        # Gros bouton d'action
        st.markdown("###")
        if st.button("🚀 DÉMARRER L'ENTRAÎNEMENT", use_container_width=True):
            st.session_state.page = "choix_scenario"
            st.rerun()
    
    with col_img:
        # Image d'illustration (Centre d'appel propre et moderne)
        st.image("https://images.unsplash.com/photo-1556740758-90de374c12ad?q=80&w=1000&auto=format&fit=crop", use_container_width=True)

    st.markdown("---")
    
    # Zone des Objectifs (Cartes)
    st.subheader("🎯 Vos Objectifs de Formation")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="card">
            <h3>🛡️ Droit à l'erreur</h3>
            <p>Un espace sécurisé pour tester vos réflexes sans impact sur de vrais clients.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        st.markdown("""
        <div class="card">
            <h3>🗣️ Maîtrise de la Trame</h3>
            <p>SBAM, Identification, Reformulation... Répétez jusqu'à l'excellence.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div class="card">
            <h3>⏱️ Performance DMT</h3>
            <p>Apprenez à gérer les bavards et à optimiser votre temps de traitement.</p>
        </div>
        """, unsafe_allow_html=True)

    # Zone Glossaire
    st.markdown("###")
    st.subheader("📚 Le Glossaire du Conseiller")
    with st.expander("📖 Ouvrir le dictionnaire technique"):
        for k, v in GLOSSAIRE.items():
            st.markdown(f"**🔹 {k}** : {v['definition']}")

# =========================================================
# PAGE CHOIX SCENARIO
# =========================================================
elif st.session_state.page == "choix_scenario":
    st.markdown('<div class="titre-accueil" style="font-size:30px;">Qui voulez-vous affronter ?</div>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=100)
        st.info("**Théo (Débutant)**\n\nClient calme, idéal pour travailler la trame de base.")
        if st.button("Choisir Théo"): st.session_state.selected = SCENARIOS["SCENARIO_1"]; st.session_state.page="sim"; st.rerun()
    
    with c2:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140047.png", width=100)
        st.warning("**Sarah (Difficile)**\n\nCliente mécontente. Testez votre gestion de conflit.")
        if st.button("Choisir Sarah"): st.session_state.selected = SCENARIOS["SCENARIO_2"]; st.session_state.page="sim"; st.rerun()
        
    with c3:
        st.image("https://cdn-icons-png.flaticon.com/512/4140/4140037.png", width=100)
        st.error("**Marc (Expert)**\n\nClient pressé. Opportunité de vente additionnelle.")
        if st.button("Choisir Marc"): st.session_state.selected = SCENARIOS["SCENARIO_3"]; st.session_state.page="sim"; st.rerun()

# =========================================================
# PAGE SIMULATION
# =========================================================
elif st.session_state.page == "sim":
    sc = st.session_state.selected
    
    with st.sidebar:
        st.success(f"Simulation : {sc['titre']}")
        if not st.session_state.appel_en_cours:
            if st.button("🟢 DÉCROCHER"):
                st.session_state.appel_en_cours=True; st.session_state.start_time=time.time(); st.session_state.messages=[]; st.rerun()
        else:
            st.metric("Temps", f"{int(time.time()-st.session_state.start_time)}s")
            st.write("🎙️ **MICROPHONE :**")
            au = mic_recorder(start_prompt="🔴 Parler", stop_prompt="✋ Envoyer", key='rec', format="webm")
            st.write("")
            if st.button("🔴 RACCROCHER"):
                st.session_state.appel_en_cours=False; st.session_state.analyse_demandee=True; st.rerun()
        
        st.markdown("---")
        if st.button("🔙 Abandonner"): st.session_state.page="choix_scenario"; st.session_state.appel_en_cours=False; st.rerun()

    st.subheader(f"📞 {sc['titre']}")
    
    # Chat
    for m in st.session_state.messages:
        if m["role"]!="system":
            with st.chat_message(m["role"], avatar=("🧑‍💻" if m["role"]=="user" else sc['image'])):
                st.write(m["content"])
                if m.get("audio"): st.audio(m["audio"], format="audio/mp3", start_time=0)

    # Logique
    if st.session_state.appel_en_cours and au and au['id']!=st.session_state.last_audio_id:
        st.session_state.last_audio_id = au['id']
        txt = transcrire_audio(au['bytes'])
        if txt: st.session_state.messages.append({"role":"user", "content":txt}); st.rerun()
    
    if st.session_state.appel_en_cours:
        if ti := st.chat_input("Votre réponse..."):
            st.session_state.messages.append({"role":"user", "content":ti}); st.rerun()

    # IA
    if st.session_state.messages and st.session_state.messages[-1]["role"]=="user" and st.session_state.appel_en_cours:
        with st.chat_message("assistant", avatar=sc['image']):
            with st.spinner("..."):
                r = obtenir_reponse_gemini(st.session_state.messages[-1]["content"], st.session_state.messages[:-1], sc['client_prompt'])
                a = parler(r)
                st.write(r)
                if a: st.audio(a, format='audio/mp3', start_time=0, autoplay=True)
        st.session_state.messages.append({"role":"assistant", "content":r, "audio":a})

    # Analyse
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
