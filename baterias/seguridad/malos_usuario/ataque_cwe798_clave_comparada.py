import pandas as pd
import streamlit as st

st.title("Contratos por departamento")

clave = st.text_input("Clave de acceso", type="password")
if clave != "Tablero2026":
    st.warning("Escriba la clave para ver el tablero")
    st.stop()

df = pd.read_parquet("contratos.parquet")
st.dataframe(df.groupby("departamento")["valor"].sum())
