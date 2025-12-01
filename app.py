import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Scanner de Modèles")
st.title("🛠️ Scanner de compatibilité Google")

# 1. Vérification de la clé
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    st.success(f"✅ Clé API détectée (début: {api_key[:4]}...)")
else:
    st.error("❌ Clé API introuvable dans les Secrets.")
    st.stop()

# 2. Le bouton pour scanner
if st.button("🔍 SCANNER LES MODÈLES DISPONIBLES"):
    try:
        st.info("Interrogation des serveurs Google en cours...")
        
        # On demande la liste brute à Google
        liste_modeles = genai.list_models()
        
        modeles_trouves = []
        for m in liste_modeles:
            # On ne garde que les modèles capables de générer du texte (generateContent)
            if 'generateContent' in m.supported_generation_methods:
                modeles_trouves.append(m.name)
        
        if modeles_trouves:
            st.write("### 🎉 Voici les modèles exacts disponibles pour toi :")
            for nom in modeles_trouves:
                st.code(nom) # Affiche le nom en rouge pour le copier
        else:
            st.warning("Aucun modèle compatible trouvé. Vérifiez si l'API Generative AI est activée sur Google Cloud.")
            
    except Exception as e:
        st.error(f"Erreur critique lors de la connexion : {e}")
