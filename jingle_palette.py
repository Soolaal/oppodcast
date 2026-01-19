import streamlit as st
import os
import base64
import json

class JinglePalette:
    def __init__(self):
        # On force l'utilisation du dossier Documents défini par le système
        USER_DOCS = os.path.expanduser("~/Documents")
        base_dir = os.path.join(USER_DOCS, "Oppodcast Studio", "assets", "jingles")
        
        self.base_dir = base_dir
        self.presets_dir = os.path.join(self.base_dir, "presets")
        
        os.makedirs(self.base_dir, exist_ok=True)
        os.makedirs(self.presets_dir, exist_ok=True)


    def _get_audio_base64(self, file_path):
        try:
            with open(file_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except: return ""

    # --- GESTION DES PRESETS ---
    def get_presets(self):
        presets = [f.replace(".json", "") for f in os.listdir(self.presets_dir) if f.endswith(".json")]
        if not presets:
            # Création d'une palette par défaut si aucune n'existe
            default_slots = {} 
            self.save_preset("Défaut", default_slots)
            return ["Défaut"]
        presets.sort()
        return presets

    def load_preset(self, preset_name):
        path = os.path.join(self.presets_dir, f"{preset_name}.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f: return json.load(f)
            except: pass
        return {}

    def save_preset(self, preset_name, slots_data):
        # Sécurisation du nom de fichier
        safe_name = "".join([c for c in preset_name if c.isalnum() or c in (' ', '-', '_')]).strip()
        if not safe_name: safe_name = "Unnamed"
        path = os.path.join(self.presets_dir, f"{safe_name}.json")
        with open(path, "w") as f:
            json.dump(slots_data, f)

    def delete_preset(self, preset_name):
        path = os.path.join(self.presets_dir, f"{preset_name}.json")
        if os.path.exists(path):
            os.remove(path)

    def render(self):
        # 1. SCAN FICHIERS AUDIO (Pool Commun)
        real_files = [f for f in os.listdir(self.base_dir) if f.lower().endswith(('.mp3', '.wav'))]
        real_files.sort()

        # 2. SÉLECTION DU PROFIL (PALETTE)
        st.markdown("### 🎛️ Jingle Palette")
        
        col_sel, col_new = st.columns([3, 1])
        all_presets = self.get_presets()
        
        # Gestion de l'état de la sélection
        if "current_preset" not in st.session_state:
            st.session_state["current_preset"] = all_presets[0]
        
        # Si le preset en session n'existe plus (supprimé), on reset
        if st.session_state["current_preset"] not in all_presets:
             st.session_state["current_preset"] = all_presets[0]

        with col_sel:
            selected_preset = st.selectbox(
                "Profil Actif", 
                all_presets, 
                index=all_presets.index(st.session_state["current_preset"]),
                label_visibility="collapsed"
            )
            # Mise à jour session si changement
            if selected_preset != st.session_state["current_preset"]:
                st.session_state["current_preset"] = selected_preset
                st.rerun()

        with col_new:
            with st.popover("➕ / ⚙️"):
                st.markdown("**Gérer les Profils**")
                new_name = st.text_input("Nom nouvelle palette")
                if st.button("Créer") and new_name:
                    self.save_preset(new_name, {})
                    st.session_state["current_preset"] = new_name
                    st.success(f"Palette '{new_name}' créée !")
                    st.rerun()
                
                st.divider()
                if st.button("🗑️ Supprimer la palette active"):
                    if len(all_presets) > 1:
                        self.delete_preset(selected_preset)
                        st.session_state["current_preset"] = all_presets[0] # Fallback
                        st.rerun()
                    else:
                        st.error("Impossible de supprimer la dernière palette.")

        # Chargement de la config du profil actif
        current_slots = self.load_preset(selected_preset)

        # 3. INTERFACE DE GESTION (Upload & Matrix)
        with st.expander(f"🛠️ Configurer '{selected_preset}' & Uploads", expanded=False):
            tab_up, tab_grid = st.tabs(["Upload / Nettoyage", "Assignation des Pads"])
            
            with tab_up:
                col_up, col_del = st.columns(2)
                with col_up:
                    uploaded = st.file_uploader("Ajouter des sons (Pool Commun)", type=["mp3", "wav"], accept_multiple_files=True)
                    if uploaded:
                        for up in uploaded:
                            safe_name = "".join([c for c in up.name if c.isalnum() or c in (' ', '.', '-', '_')]).strip()
                            with open(os.path.join(self.base_dir, safe_name), "wb") as f: f.write(up.getbuffer())
                        st.success("Sons ajoutés !")
                        st.rerun()
                with col_del:
                    if real_files:
                        to_del = st.multiselect("Supprimer des fichiers du disque", real_files)
                        if to_del and st.button("🗑️ Supprimer"):
                            for f in to_del:
                                try: os.remove(os.path.join(self.base_dir, f))
                                except: pass
                            st.success("Supprimé.")
                            st.rerun()

            with tab_grid:
                st.info(f"Édition de la grille pour : **{selected_preset}**")
                
                rows_labels = ["A", "B", "C", "D", "E"]
                cols_labels = ["1", "2", "3", "4", "5", "6"]
                
                data_matrix = []
                for r in rows_labels:
                    row_data = {}
                    row_data["Ligne"] = r
                    for c in cols_labels:
                        slot_id = f"{r}{c}"
                        val = current_slots.get(slot_id)
                        if val and val not in real_files: val = None
                        row_data[c] = val
                    data_matrix.append(row_data)

                column_config = {
                    "Ligne": st.column_config.TextColumn(disabled=True, width="small"),
                }
                options = real_files
                for c in cols_labels:
                    column_config[c] = st.column_config.SelectboxColumn(label=c, width="medium", options=options, required=False)

                edited_df = st.data_editor(data_matrix, column_config=column_config, hide_index=True, use_container_width=True, num_rows="fixed")

                if st.button("💾 Sauvegarder la Grille"):
                    new_slots = {}
                    try: data_list = edited_df.to_dict(orient="records")
                    except AttributeError: data_list = edited_df
                        
                    for row in data_list:
                        r_label = row["Ligne"]
                        for c_label in cols_labels:
                            val = row.get(c_label)
                            if val: new_slots[f"{r_label}{c_label}"] = val
                    
                    self.save_preset(selected_preset, new_slots)
                    st.success(f"Palette '{selected_preset}' sauvegardée !")
                    st.rerun()

        # 4. RENDU HTML/JS (PLAYER)
        # Identique à avant, mais utilise 'current_slots' qui dépend du preset
        rows = ["A", "B", "C", "D", "E"]
        cols_count = 6
        cards_html = ""
        
        for r in rows:
            for c in range(1, cols_count + 1):
                slot_id = f"{r}{c}"
                filename = current_slots.get(slot_id)
                
                if filename and filename in real_files:
                    fpath = os.path.join(self.base_dir, filename)
                    b64 = self._get_audio_base64(fpath)
                    ext = os.path.splitext(filename)[1].lower()
                    mime = "audio/wav" if ext == ".wav" else "audio/mpeg"
                    name = os.path.splitext(filename)[0]
                    display = name if len(name) < 16 else name[:14]+".."
                    
                    cards_html += f"""
                    <div class="card" id="card_{slot_id}" onclick="playJingle('{slot_id}', '{name}')">
                        <div class="slot-label">{slot_id}</div>
                        <div class="icon">🎵</div>
                        <div class="name">{display}</div>
                        <audio id="aud_{slot_id}" src="data:{mime};base64,{b64}"></audio>
                    </div>"""
                else:
                    cards_html += f"""<div class="card empty"><div class="slot-label">{slot_id}</div></div>"""

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            :root {{ --accent: #FF4B4B; --bg: #0E1117; --card-bg: #262730; --empty-bg: #1c1d24; }}
            body {{ margin: 0; padding: 0; background: transparent; font-family: sans-serif; color: white; overflow: hidden; }}
            .grid-container {{ height: 500px; overflow-y: auto; padding: 10px; display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; padding-bottom: 70px; }}
            ::-webkit-scrollbar {{ width: 6px; }}
            ::-webkit-scrollbar-thumb {{ background: #444; border-radius: 4px; }}
            .card {{ background: var(--card-bg); border: 1px solid #444; border-radius: 6px; height: 80px; display: flex; flex-direction: column; justify-content: center; align-items: center; cursor: pointer; user-select: none; transition: all 0.1s; position: relative; }}
            .card:hover {{ border-color: var(--accent); background: #333; }}
            .card:active {{ transform: scale(0.96); }}
            .card.playing {{ border-color: #00FF00; box-shadow: 0 0 8px rgba(0,255,0,0.3); background: #1a2e1a; }}
            .card.empty {{ background: var(--empty-bg); border: 1px dashed #333; cursor: default; opacity: 0.5; }}
            .slot-label {{ position: absolute; top: 4px; left: 5px; font-size: 9px; color: #666; font-weight: bold; }}
            .icon {{ font-size: 18px; margin-bottom: 2px; }}
            .name {{ font-size: 10px; font-weight: bold; text-align: center; width: 95%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .player-bar {{ position: fixed; bottom: 0; left: 0; right: 0; height: 60px; background: #1E1E1E; border-top: 1px solid #333; display: flex; align-items: center; padding: 0 15px; z-index: 100; }}
            .info-box {{ flex: 1; display: flex; flex-direction: column; min-width: 0; margin-right: 10px; }}
            .now-playing {{ font-size: 13px; font-weight: bold; color: #FFF; margin-bottom: 2px; }}
            .time-display {{ font-size: 11px; color: #AAA; font-family: monospace; }}
            .controls {{ display: flex; align-items: center; gap: 10px; }}
            .btn-stop {{ background: #CC3333; color: white; border: none; border-radius: 4px; padding: 6px 12px; font-weight: bold; cursor: pointer; }}
            .btn-stop:hover {{ background: #FF4444; }}
        </style>
        </head>
        <body>
        <div class="grid-container">{cards_html}</div>
        <div class="player-bar">
            <div class="info-box"><div class="now-playing" id="trackName">Prêt</div><div class="time-display" id="timeDisp">00:00 / 00:00</div></div>
            <div class="controls">
                <span style="font-size:12px">🔊</span>
                <input type="range" min="0" max="1" step="0.05" value="0.8" oninput="setVolume(this.value)" style="width:80px; accent-color:#FF4B4B;">
                <button class="btn-stop" onclick="stopAll()">STOP</button>
            </div>
        </div>
        <script>
            let currentAudio = null; let currentId = null; let updateTimer = null; let globalVolume = 0.8;
            function formatTime(sec) {{ if(isNaN(sec)) return "00:00"; let m = Math.floor(sec / 60); let s = Math.floor(sec % 60); return (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s); }}
            function setVolume(val) {{ globalVolume = val; if(currentAudio) currentAudio.volume = globalVolume; }}
            function stopAll() {{ if(currentAudio) {{ currentAudio.pause(); currentAudio.currentTime = 0; }} if(currentId) {{ let old = document.getElementById('card_' + currentId); if(old) old.classList.remove('playing'); }} currentAudio = null; currentId = null; clearInterval(updateTimer); document.getElementById('trackName').innerText = "Prêt"; document.getElementById('timeDisp').innerText = "00:00 / 00:00"; }}
            function playJingle(slotId, name) {{ if (currentId === slotId) {{ stopAll(); return; }} stopAll(); let audio = document.getElementById('aud_' + slotId); let card = document.getElementById('card_' + slotId); if(audio) {{ currentAudio = audio; currentId = slotId; audio.volume = globalVolume; audio.play(); card.classList.add('playing'); document.getElementById('trackName').innerText = "▶ " + name; updateTimer = setInterval(() => {{ if(!audio) return; let cur = audio.currentTime; let dur = audio.duration || 0; document.getElementById('timeDisp').innerText = formatTime(cur) + " / " + formatTime(dur); if(audio.ended) stopAll(); }}, 100); }} }}
        </script>
        </body>
        </html>
        """
        st.components.v1.html(full_html, height=580)
