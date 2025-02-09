import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os
from deep_translator import GoogleTranslator

# 🌟 Configure the page layout
st.set_page_config(page_title="EconMind", layout="wide")

# Google Analytics Tracking (if needed)
GA_TRACKING_ID = "G-NTX0H753BH"  # Replace with your Measurement ID
GA_SCRIPT = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_TRACKING_ID}');
</script>
"""
st.markdown(GA_SCRIPT, unsafe_allow_html=True)

# 📌 Header with language selector
col1, col2 = st.columns([0.8, 0.2])
with col2:
    idioma = st.selectbox("🌐", ["ES", "EN"], index=0, label_visibility="collapsed")

# -----------------------------------------------------------------------------
# Define the Spanish texts dictionary.
textos_es = {
    "title": "Hola! Somos EconMind 🚀",
    "subtitle": "💡 Datos y análisis para que tomes mejores decisiones y mejores tu calidad de vida.",
    "section1": "📈 Inflación y Tipo de Cambio",
    "section1_items": [
        "🔹 Ratio Tipo de Cambio vs. Inflación",
        "🔹 Inflación General vs. Inflación Núcleo",
        "🔹 Dólar Oficial vs. Dólar Blue"
    ],
    "articles": "📑 Artículos y Análisis Económicos",
    "articles_desc": "🔍 Aquí se mostrarán artículos sobre temas específicos de economía.",
    "covid": "😷 COVID-19",
    "asume_fernandez": "✌️ Asume Fernández",
    "asume_milei": "🦁 Asume Milei",
    "chart_title": "Evolución de la Inflación General y Núcleo - INDEC",
    "chart_caption": "📌 *IPC General y Núcleo. Tasa de variación mensual. Nivel General. Nacional. Base dic 2016.*",
    "chart_source": "Fuente: INDEC.",
    "usd_section": "💵 Tipo de Cambio USD",
    "usd_chart_title": "Evolución del Tipo de Cambio USD",
    "usd_chart_caption": "Datos proporcionados por el BCRA.",
    "ratio_section": "📊 Ratio Tipo de Cambio vs IPC",
    "ratio_chart_title": "Ratio Tipo de Cambio vs IPC General",
    "ratio_chart_caption": "El ratio se calcula como el promedio mensual del Tipo de Cambio dividido por el IPC General."
}

# -----------------------------------------------------------------------------
# Helper functions to translate strings or lists using deep_translator.
def translate_value(value, target_lang="en"):
    if isinstance(value, str):
        return GoogleTranslator(source='es', target=target_lang).translate(value)
    elif isinstance(value, list):
        return [GoogleTranslator(source='es', target=target_lang).translate(item) if isinstance(item, str) else item for item in value]
    else:
        return value

def translate_dict(text_dict, target_lang="en"):
    return {k: translate_value(v, target_lang) for k, v in text_dict.items()}

# If English is selected, translate the Spanish texts automatically.
if idioma == "EN":
    textos = translate_dict(textos_es, target_lang="en")
else:
    textos = textos_es

# -----------------------------------------------------------------------------
# Main Title and Subtitle
st.title(textos["title"])
st.subheader(textos["subtitle"])
st.divider()

# -----------------------------------------------------------------------------
# Define API endpoints and IDs
IPC_GENERAL_ID = "145.3_INGNACUAL_DICI_M_38"  # IPC General
IPC_NUCLEO_ID = "173.1_INUCLEOLEO_DIC-_0_10"    # IPC Núcleo
IPC_API_URL = f"https://apis.datos.gob.ar/series/api/series/?ids={IPC_GENERAL_ID},{IPC_NUCLEO_ID}&format=json"
BCRA_API_URL = "https://api.estadisticasbcra.com/usd_of"
BCRA_API_TOKEN = st.secrets["BCRA_API_TOKEN"]

# -----------------------------------------------------------------------------
# Function to obtain IPC data (with caching and error handling)
@st.cache_data(show_spinner=True)
def obtener_ipc():
    try:
        response = requests.get(IPC_API_URL)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"❌ Error al conectarse a la API de IPC: {e}")
        return None

    data = response.json().get("data")
    if data is None:
        st.error("❌ La respuesta de la API no contiene la clave 'data'.")
        return None

    df = pd.DataFrame(data, columns=["fecha", "IPC General", "IPC Núcleo"])
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d", errors="coerce")

    # Verify expected columns
    expected_columns = {"fecha", "IPC General", "IPC Núcleo"}
    if not expected_columns.issubset(df.columns):
        st.error("❌ La estructura de los datos de IPC no es la esperada.")
        return None

    # Filter data from December 2019 onward
    fecha_corte = pd.to_datetime("2019-12-01")
    df = df[df["fecha"] >= fecha_corte]
    return df

# -----------------------------------------------------------------------------
# Function to obtain USD exchange rate data from the BCRA API (with caching and error handling)
@st.cache_data(show_spinner=True)
def obtener_usd():
    headers = {"Authorization": f"BEARER {BCRA_API_TOKEN}"}
    try:
        response = requests.get(BCRA_API_URL, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"❌ Error fetching USD data: {e}")
        return None

    data = response.json()
    df = pd.DataFrame(data)
    if "d" not in df.columns or "v" not in df.columns:
        st.error("❌ The USD data does not have the expected structure.")
        return None

    df["fecha"] = pd.to_datetime(df["d"], errors="coerce")
    df.rename(columns={"v": "tipo_cambio"}, inplace=True)
    fecha_corte_usd = pd.to_datetime("2019-12-01")
    df = df[df["fecha"] >= fecha_corte_usd]
    df = df.sort_values("fecha")
    return df

# -----------------------------------------------------------------------------
# SECTION: Inflation and Exchange Rate (IPC)
with st.expander(textos["section1"]):
    # List descriptive items
    for item in textos["section1_items"]:
        st.write(item)

    df_ipc = obtener_ipc()
    if df_ipc is not None:
        fig = px.line(
            df_ipc,
            x="fecha",
            y=["IPC General", "IPC Núcleo"],
            title=textos["chart_title"],
            labels={"fecha": "Fecha", "value": "Índice de Precios", "variable": "Indicador"},
            markers=True
        )

        # Add a shaded region for the COVID-19 period (March 2020 - December 2021)
        fig.add_vrect(
            x0=pd.to_datetime("2020-03-01"),
            x1=pd.to_datetime("2021-12-31"),
            annotation_text=textos["covid"],
            annotation_position="top left",
            fillcolor="lightgray",
            opacity=0.1,
            layer="below",
            line_width=0
        )

        # Add a line and annotation for "Asume Fernández"
        fig.add_shape(
            type="line",
            x0=pd.to_datetime("2019-12-01"),
            x1=pd.to_datetime("2019-12-01"),
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="blue", width=1, dash="dash")
        )
        fig.add_annotation(
            x=pd.to_datetime("2019-12-01"),
            y=0.5,
            xref="x",
            yref="paper",
            text=textos["asume_fernandez"],
            showarrow=False,
            font=dict(size=10, color="blue"),
            xshift=50
        )

        # Add a line and annotation for "Asume Milei"
        fig.add_shape(
            type="line",
            x0=pd.to_datetime("2023-12-01"),
            x1=pd.to_datetime("2023-12-01"),
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="blue", width=1, dash="dash")
        )
        fig.add_annotation(
            x=pd.to_datetime("2023-12-01"),
            y=0.5,
            xref="x",
            yref="paper",
            text=textos["asume_milei"],
            showarrow=False,
            font=dict(size=10, color="blue"),
            xshift=35
        )

        st.plotly_chart(fig, use_container_width=True)
        st.caption(textos["chart_caption"])
        st.caption(textos["chart_source"])

# -----------------------------------------------------------------------------
# SECTION: USD Exchange Rate from BCRA
with st.expander(textos["usd_section"]):
    df_usd = obtener_usd()
    if df_usd is not None:
        fig_usd = px.line(
            df_usd,
            x="fecha",
            y="tipo_cambio",
            title=textos["usd_chart_title"],
            labels={
                "fecha": "Fecha" if idioma == "ES" else "Date",
                "tipo_cambio": "Tipo de Cambio" if idioma == "ES" else "Exchange Rate"
            },
            markers=True
        )
        st.plotly_chart(fig_usd, use_container_width=True)
        st.caption(textos["usd_chart_caption"])

# -----------------------------------------------------------------------------
# SECTION: Ratio Tipo de Cambio vs IPC
with st.expander(textos["ratio_section"]):
    st.markdown("### 📊 ¿Qué nos dice el Ratio Tipo de Cambio vs. Inflación?")
    st.markdown("""
    📌 **Interpretación:**  
    Este ratio mide cuánto se ha **depreciado** el peso argentino en términos reales comparado con la inflación.  
    - **Si el ratio aumenta 📈**, significa que el dólar oficial crece más rápido que la inflación → **mayor depreciación real del peso**.  
    - **Si el ratio cae 📉**, significa que la inflación supera la variación del dólar → **apreciación real del peso**.  

    💡 **Ejemplo práctico:**  
    Si en enero el dólar sube un **5%**, pero la inflación mensual es del **6%**, el ratio bajará. En términos reales, el peso estaría perdiendo menos valor frente al dólar que contra los precios en la economía.
    """)
    st.markdown("""
    🔍 **Impacto en bienes transables vs. no transables:**  
    - Si la inflación es mayor que el aumento del dólar, los **bienes importados** tienden a **encarecerse menos en pesos** que los **bienes y servicios locales**.  

    💡 **Ejemplo práctico:**  
    - Un **iPhone (bien transable)** podría costar **menos pesos** que el mes anterior porque su precio **está atado al dólar**.  
    - Ir a la **peluquería (bien no transable)** podría ser **más caro en pesos**, ya que estos servicios ajustan más rápido a la inflación local.  

    📌 **Conclusión:** El **precio relativo** de los bienes transables sobre los no transables **se abarató**.
    """)
    st.markdown("""
    💰 **¿Cómo podemos usar este ratio para tomar mejores decisiones?**  
    Este indicador nos ayuda a evaluar decisiones financieras clave, por ejemplo, en términos de ahorro, consumo e inversión.
    """)

    if df_ipc is not None and df_usd is not None:
        # Convert IPC data to monthly averages (group by month)
        df_ipc["mes"] = df_ipc["fecha"].dt.to_period("M")
        df_ipc_monthly = df_ipc.groupby("mes", as_index=False)["IPC General"].mean()

        # Convert USD data to monthly averages
        df_usd["mes"] = df_usd["fecha"].dt.to_period("M")
        df_usd_monthly = df_usd.groupby("mes", as_index=False)["tipo_cambio"].mean()

        # Merge the two dataframes on "mes"
        df_ratio = pd.merge(df_ipc_monthly, df_usd_monthly, on="mes", how="inner")
        df_ratio["ratio"] = df_ratio["tipo_cambio"] / df_ratio["IPC General"]

        # Convert "mes" to a timestamp for plotting (using the start of the month)
        df_ratio["fecha"] = df_ratio["mes"].dt.to_timestamp()

        fig_ratio = px.line(
            df_ratio,
            x="fecha",
            y="ratio",
            title=textos["ratio_chart_title"],
            labels={
                "fecha": "Fecha" if idioma == "ES" else "Date",
                "ratio": "Ratio Tipo de Cambio / IPC" if idioma == "ES" else "Exchange Rate / CPI Ratio"
            },
            markers=True
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
        st.caption(textos["ratio_chart_caption"])
    else:
        st.error("No hay datos suficientes para calcular el ratio.")

# -----------------------------------------------------------------------------
# SECTION: Fuentes de Datos y Metodología
st.divider()
st.subheader("📊 🔍 Fuentes de Datos y Metodología")
st.markdown("""
📌 **¿De dónde obtenemos los datos?**  
- **Inflación (IPC General y Núcleo):** API de **INDEC** ([Datos Abiertos del Gobierno](https://datos.gob.ar/)).  
- **Tipo de Cambio Oficial:** API del **Banco Central de la República Argentina (BCRA)** ([Estadísticas BCRA](https://www.bcra.gob.ar/)).  

📌 **Metodología:**  
- **Promedio mensual:** Los datos diarios del BCRA se agrupan para calcular un promedio mensual.  
- **Limpieza y filtrado:** Se normalizan las fechas y se filtra la data desde diciembre de 2019.  
- **Cálculo del Ratio:** Se divide el tipo de cambio promedio mensual por el IPC General.
""")

st.divider()

# -----------------------------------------------------------------------------
# SECTION: Articles
st.subheader(textos["articles"])
st.write(textos["articles_desc"])
