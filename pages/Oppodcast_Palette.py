import streamlit as st
from jingle_palette import JinglePalette

st.set_page_config(page_title="Jingle Palette", page_icon="🎛️", layout="wide")

st.title("🎛️ Jingle Palette")
st.caption("Lancez vos sons instantanément pendant vos enregistrements")

palette = JinglePalette()
palette.render()
