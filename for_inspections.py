import requests
import pandas as pd
from config import BCRA_API_TOKEN  # 🔑 Importar token desde config.py

# 📌 URL de la API del BCRA
BCRA_API_URL = "https://api.estadisticasbcra.com/usd"
IPC_GENERAL_ID = "145.3_INGNACUAL_DICI_M_38"  # Inflación General

# 📌 Hacer la solicitud a la API con el TOKEN en el header
headers = {"Authorization": f"BEARER {BCRA_API_TOKEN}"}
response = requests.get(BCRA_API_URL, headers=headers)

# 📊 Verificar si la respuesta es exitosa
if response.status_code == 200:
    data = response.json()  # Convertir la respuesta en JSON
    df = pd.DataFrame(data)  # Convertir en DataFrame
    df["d"] = pd.to_datetime(df["d"])  # Convertir la fecha a formato datetime

    # 📌 Renombrar columnas para mayor claridad
    df.rename(columns={"d": "fecha", "v": "tipo_cambio"}, inplace=True)

    # 📊 Mostrar primeras filas
    num_registros = df.shape[0]
    print(f"📌 La tabla tiene {num_registros} registros.")

else:
    print(f"❌ Error {response.status_code}: No se pudo obtener la data.")


df["mes"] = df["fecha"].dt.to_period("M")

df_mensual = df.groupby("mes")["tipo_cambio"].mean().reset_index()

print(df_mensual)

IPC_API_URL = f"https://apis.datos.gob.ar/series/api/series/?ids={IPC_GENERAL_ID}&format=json"


response2 = requests.get(IPC_API_URL)

if response2.status_code == 200:
    data2 = response2.json()
    print(data2)
    df2 = pd.DataFrame(data2["data"], columns=["fecha", "IPC General"])
    df2["fecha"] = pd.to_datetime(df2["fecha"])


else:
    print(f"❌ Error {response2.status_code}: No se pudo obtener la data.")

df2["mes"] = df2["fecha"].dt.to_period("M")

df2_mensual = df2.groupby("mes")["IPC General"].mean().reset_index()


df_final = pd.merge(df_mensual, df2_mensual, on="mes", how="inner")
print(df_final)


