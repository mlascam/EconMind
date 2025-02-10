import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import os

# 🌟 Configura el layout de la página
st.set_page_config(page_title="EconMind", layout="wide")

# Google Analytics Tracking (si es necesario)
GA_TRACKING_ID = "G-NTX0H753BH"  # Reemplaza con tu ID de Medición
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

# -----------------------------------------------------------------------------
# Diccionario de textos en español
textos = {
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
    "ratio_chart_caption": "El ratio se calcula como el promedio mensual del Tipo de Cambio dividido por el IPC General.",
    "brecha_card_title": "📊 Brecha Cambiaria"
}

# -----------------------------------------------------------------------------
# Título principal y subtítulo
st.title(textos["title"])
st.subheader(textos["subtitle"])
st.divider()

# -----------------------------------------------------------------------------
# SECCIÓN: Brecha Cambiaria (mostrar en una card al tope)
@st.cache_data(show_spinner=True)
def obtener_dolar(url, nombre):
    """Obtiene los valores de compra y venta de Dólar desde la API."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        compra = data.get('compra')
        venta = data.get('venta')
        return compra, venta
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al obtener {nombre}: {e}")
        return None, None

URL_OFICIAL = "https://dolarapi.com/v1/dolares/oficial"
URL_MEP = "https://dolarapi.com/v1/dolares/bolsa"

compra_oficial, venta_oficial = obtener_dolar(URL_OFICIAL, "Dólar Oficial")
compra_mep, venta_mep = obtener_dolar(URL_MEP, "Dólar MEP")

if venta_oficial and compra_mep:
    brecha = ((compra_mep - venta_oficial) / venta_oficial) * 100
    # Usamos columnas para centrar la card
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric(
            label=textos["brecha_card_title"],
            value=f"{brecha:.2f}%",
            delta=f"💵 Dólar Oficial Venta: ${venta_oficial} - 💵 Dólar MEP Compra: ${compra_mep}"
        )
else:
    st.error("❌ No se pudo calcular la brecha cambiaria.")

st.divider()

# -----------------------------------------------------------------------------
# Endpoints de las APIs y tokens
IPC_GENERAL_ID = "145.3_INGNACUAL_DICI_M_38"  # IPC General
IPC_NUCLEO_ID = "173.1_INUCLEOLEO_DIC-_0_10"    # IPC Núcleo
IPC_API_URL = f"https://apis.datos.gob.ar/series/api/series/?ids={IPC_GENERAL_ID},{IPC_NUCLEO_ID}&format=json"
BCRA_API_URL = "https://api.estadisticasbcra.com/usd_of"
BCRA_API_TOKEN = st.secrets["BCRA_API_TOKEN"]

# -----------------------------------------------------------------------------
# Función para obtener datos del IPC (con caching y manejo de errores)
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

    expected_columns = {"fecha", "IPC General", "IPC Núcleo"}
    if not expected_columns.issubset(df.columns):
        st.error("❌ La estructura de los datos de IPC no es la esperada.")
        return None

    fecha_corte = pd.to_datetime("2019-12-01")
    df = df[df["fecha"] >= fecha_corte]
    return df

# -----------------------------------------------------------------------------
# Función para obtener datos del Tipo de Cambio USD de la API del BCRA (con caching y manejo de errores)
@st.cache_data(show_spinner=True)
def obtener_usd():
    headers = {"Authorization": f"BEARER {BCRA_API_TOKEN}"}
    try:
        response = requests.get(BCRA_API_URL, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"❌ Error al obtener datos USD: {e}")
        return None

    data = response.json()
    df = pd.DataFrame(data)
    if "d" not in df.columns or "v" not in df.columns:
        st.error("❌ La estructura de los datos USD no es la esperada.")
        return None

    df["fecha"] = pd.to_datetime(df["d"], errors="coerce")
    df.rename(columns={"v": "tipo_cambio"}, inplace=True)
    fecha_corte_usd = pd.to_datetime("2019-12-01")
    df = df[df["fecha"] >= fecha_corte_usd]
    df = df.sort_values("fecha")
    return df

# -----------------------------------------------------------------------------
# SECCIÓN: Inflación y Tipo de Cambio (IPC)
with st.expander(textos["section1"]):
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
# SECCIÓN: Tipo de Cambio USD (BCRA)
with st.expander(textos["usd_section"]):
    df_usd = obtener_usd()
    if df_usd is not None:
        fig_usd = px.line(
            df_usd,
            x="fecha",
            y="tipo_cambio",
            title=textos["usd_chart_title"],
            labels={"fecha": "Fecha", "tipo_cambio": "Tipo de Cambio"},
            markers=True
        )
        st.plotly_chart(fig_usd, use_container_width=True)
        st.caption(textos["usd_chart_caption"])

# -----------------------------------------------------------------------------
# SECCIÓN: Ratio Tipo de Cambio vs IPC
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
        df_ipc["mes"] = df_ipc["fecha"].dt.to_period("M")
        df_ipc_monthly = df_ipc.groupby("mes", as_index=False)["IPC General"].mean()
        df_usd["mes"] = df_usd["fecha"].dt.to_period("M")
        df_usd_monthly = df_usd.groupby("mes", as_index=False)["tipo_cambio"].mean()
        df_ratio = pd.merge(df_ipc_monthly, df_usd_monthly, on="mes", how="inner")
        df_ratio["ratio"] = df_ratio["tipo_cambio"] / df_ratio["IPC General"]
        df_ratio["fecha"] = df_ratio["mes"].dt.to_timestamp()
        fig_ratio = px.line(
            df_ratio,
            x="fecha",
            y="ratio",
            title=textos["ratio_chart_title"],
            labels={"fecha": "Fecha", "ratio": "Ratio Tipo de Cambio / IPC"},
            markers=True
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
        st.caption(textos["ratio_chart_caption"])
    else:
        st.error("No hay datos suficientes para calcular el ratio.")

# -----------------------------------------------------------------------------
# SECCIÓN: Fuentes de Datos y Metodología
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
# SECCIÓN: Artículos
st.subheader(textos["articles"])
st.write(textos["articles_desc"])
