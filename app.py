import streamlit as st
import google.generativeai as genai
import time
import re
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import io

# --- IMPORTATION DES DONNÉES ---
# Note : Assurez-vous d'avoir les fichiers prompts.py et glossaire_data.py
try:
    from prompts import SCENARIOS
    from glossaire_data import GLOSSAIRE
except ImportError:
    st.error("🚨 Erreur critique : Les fichiers 'prompts.py' ou 'glossaire_data.py' sont manquants dans le dépôt GitHub.")
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
        if score < 50: st.error(f"🔴 {score
