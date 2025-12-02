# --- ANALYSE & BAROMÈTRE ---
    if hasattr(st.session_state, 'analyse_demandee') and st.session_state.analyse_demandee:
        st.divider()
        st.subheader("📝 Bilan du Coach")
        
        with st.spinner("Analyse du verbatim et calcul du score..."):
            # 1. Récupération du texte de la conversation
            conv = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages if m['role']!='system'])
            
            # 2. Analyse par l'IA
            res = analyse_coach(conv, sc['coach_prompt'])
            
            # 3. Extraction et Affichage du Score
            score_final = extraire_score(res)
            afficher_barometre(score_final)
            
            # 4. Affichage du texte de l'analyse (sans le tag de score)
            texte_propre = res.replace(f"[SCORE:{score_final}]", "")
            st.info(texte_propre)
            
            # --- PRÉPARATION DES FICHIERS À TÉLÉCHARGER ---
            
            # Fichier 1 : Le Feedback du Coach
            contenu_feedback = f"""
            BILAN PÉDAGOGIQUE - CRCD
            Date : {time.strftime('%d/%m/%Y à %H:%M')}
            Scénario : {sc['titre']}
            NOTE GLOBALE : {score_final}/100
            
            ------------------------------------------------
            ANALYSE DÉTAILLÉE DU COACH :
            ------------------------------------------------
            {texte_propre}
            """
            
            # Fichier 2 : Le Verbatim (Transcription)
            contenu_verbatim = f"""
            VERBATIM DE L'APPEL (TRANSCRIPTION)
            Date : {time.strftime('%d/%m/%Y à %H:%M')}
            Scénario : {sc['titre']}
            Durée : {int(time.time() - st.session_state.start_time) if st.session_state.start_time else 0} secondes
            
            ------------------------------------------------
            TRANSCRIPTION DES ÉCHANGES :
            ------------------------------------------------
            {conv}
            """
            
            # --- AFFICHAGE DES DEUX BOUTONS ---
            st.write("### 💾 Sauvegarder votre travail")
            col_dl1, col_dl2 = st.columns(2)
            
            with col_dl1:
                st.download_button(
                    label="📥 TÉLÉCHARGER LE FEEDBACK (PDF/TXT)",
                    data=contenu_feedback,
                    file_name=f"Feedback_{sc['titre'].split(':')[0].strip()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col_dl2:
                st.download_button(
                    label="📜 TÉLÉCHARGER LE VERBATIM (SCRIPT)",
                    data=contenu_verbatim,
                    file_name=f"Verbatim_{sc['titre'].split(':')[0].strip()}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            st.session_state.analyse_demandee = False
