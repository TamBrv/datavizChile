import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import time

# --- Barra lateral con descripción ---
st.sidebar.title("Acerca del Proyecto")
st.sidebar.info(
    """
    Esta aplicación muestra las farmacias de turno en Chile utilizando datos en vivo del Ministerio de Salud (MINSAL).
    Puedes filtrar por región y seleccionar una o varias comunas para ver las farmacias disponibles.
    """
)

# --- Título de la App con color ---
st.markdown("<h1 style='color:#2E86C1;'>🩺 Farmacias de Turno en Chile</h1>", unsafe_allow_html=True)
st.write("Datos en vivo desde el Ministerio de Salud (MINSAL)")

# --- Obtener datos desde la API REST ---
url = "https://midas.minsal.cl/farmacia_v2/WS/getLocalesTurnos.php"
response = requests.get(url)
time.sleep(1)

# Validar la respuesta
if response.status_code == 200:
    data = response.json()
    df = pd.DataFrame(data)
    region_names = {
        "1": "Arica y Parinacota",
        "2": "Tarapacá",
        "3": "Antofagasta",
        "4": "Atacama",
        "5": "Coquimbo",
        "6": "Valparaíso",
        "7": "Metropolitana",
        "8": "Libertador B. O'Higgins",
        "9": "Maule",
        "10": "Biobío",
        "11": "La Araucanía",
        "12": "Los Ríos",
        "13": "Los Lagos",
        "14": "Aysén",
        "15": "Magallanes",
        "16": "Ñuble"
    }

    if df.empty:
        st.error("No se recibieron datos desde la API.")
        st.stop()

    # --- Mostrar tabla completa ---
    st.subheader("📋 Datos completos de farmacias")
    st.dataframe(df)

    # --- Filtros agrupados en un contenedor ---
    with st.container():
        regiones = df["fk_region"].astype(str).unique()
        regiones_sorted = sorted(regiones)
        region_options = [f"{r} - {region_names.get(r, 'Desconocida')}" for r in regiones_sorted]
        region_selection = st.selectbox("Selecciona región (ID):", region_options)
        region = str(region_selection.split(" - ")[0])

        region_df = df[df["fk_region"].astype(str) == region]
        comunas_sorted = sorted(region_df["comuna_nombre"].dropna().unique())
        comuna_opciones = [c for c in comunas_sorted]
        comuna = st.selectbox("Selecciona una comuna:", comuna_opciones) if comuna_opciones else None

        if comuna:
            filtrado = region_df[region_df["comuna_nombre"] == comuna]
        else:
            filtrado = pd.DataFrame()

        # Verifica que la columna local_nombre existe antes de usarla
        if "local_nombre" in filtrado.columns:
            farmacia_opciones = sorted(filtrado["local_nombre"].dropna().unique())
            seleccion_farmacia = st.selectbox("Filtrar por nombre de farmacia:", ["Todas"] + farmacia_opciones)
            if seleccion_farmacia != "Todas":
                filtrado = filtrado[filtrado["local_nombre"] == seleccion_farmacia]
        else:
            farmacia_opciones = []
            seleccion_farmacia = "Todas"

    # --- Filtrado dinámico ---
    filtrado = filtrado.sort_values(by="local_nombre") if "local_nombre" in filtrado.columns else filtrado
    filtrado = filtrado.dropna(axis=1, how="all")

    st.subheader(f"Farmacias de turno en {comuna if comuna else 'la selección actual'}")
    columnas_deseadas = [
        "local_nombre",
        "local_direccion",
        "funcionamiento_hora_apertura",
        "funcionamiento_hora_cierre",
        "local_telefono"
    ]
    columnas_existentes = [col for col in columnas_deseadas if col in filtrado.columns]
    if columnas_existentes and not filtrado.empty:
        st.dataframe(filtrado[columnas_existentes])
    else:
        st.warning("No hay columnas relevantes disponibles para mostrar.")

    # --- Análisis: cantidad de farmacias por comuna (para gráfico) ---
    conteo = df[df["fk_region"] == region]["comuna_nombre"].value_counts()

    st.subheader(f"📊 Número de farmacias de turno por comuna en la región {region_names.get(region, 'Desconocida')}")
    if conteo.empty:
        st.warning("No hay farmacias disponibles para graficar en esta región.")
    else:
        fig, ax = plt.subplots(figsize=(10,6))
        conteo.plot(kind='bar', ax=ax, color='#2E86C1')
        ax.set_xlabel("Comuna")
        ax.set_ylabel("Cantidad de farmacias")
        ax.set_title(f"Farmacias de turno por comuna en {region_names.get(region, 'Desconocida')}")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

else:
    st.error("No se pudo obtener la información desde la API.")
