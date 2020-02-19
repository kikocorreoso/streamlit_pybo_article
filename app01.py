import streamlit as st

st.title('Título')
st.header("Cabecero")
st.subheader("SubCabecero")
st.text("Esto es texto")
st.latex("y = x^2")
st.code("if a == 1:\n    print(a)", language="python")
st.code("var a = 1;", language="javascript")
st.markdown("Esto es **texto** usando *Markdown*")
