# Mon Coach CRCD

Application Streamlit francophone pour s'entraîner aux interactions de relation client. Les réponses vocales de l'IA utilisent désormais des voix neuronales gratuites via Edge TTS, avec repli gTTS.

## 1. Récupérer les dernières modifications
Si vous avez déjà cloné votre dépôt GitHub localement :

```bash
git checkout main
git pull origin main
```

Si ce dépôt n'est pas encore présent :

```bash
git clone https://github.com/<votre-compte>/mon-coach-crcd.git
cd mon-coach-crcd
```

## 2. Installer les dépendances
Il est conseillé d'utiliser un environnement virtuel Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate  # Sous Windows : .venv\\Scripts\\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Les voix neuronales gratuites reposent sur le paquet `edge-tts` déjà listé dans `requirements.txt`.

## 3. Configurer les secrets
Créez le fichier `.streamlit/secrets.toml` et ajoutez votre clé Gemini :

```toml
GOOGLE_API_KEY = "votre_clef_apis"
```

## 4. Lancer l'application en local

```bash
streamlit run app.py
```

## 5. Publier sur GitHub après vos changements

```bash
git status
# Vérifiez les fichiers modifiés

git add .
git commit -m "Votre message de commit"
git push origin main
```

Votre dépôt GitHub contiendra alors la version utilisant les voix neuronales Edge TTS.
