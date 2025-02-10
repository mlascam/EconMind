import requests

# Endpoints de la API para Dólar Oficial y Dólar MEP
URL_OFICIAL = "https://dolarapi.com/v1/dolares/oficial"
URL_MEP = "https://dolarapi.com/v1/dolares/bolsa"

def obtener_dolar(url, nombre):
    """Función para obtener valores de compra y venta de Dólar desde la API."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        compra = data.get('compra')
        venta = data.get('venta')
        print(f"{nombre} - Compra: ${compra}, Venta: ${venta}")
        return compra, venta
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener {nombre}: {e}")
        return None, None

# Obtener valores de Dólar Oficial y Dólar MEP
compra_oficial, venta_oficial = obtener_dolar(URL_OFICIAL, "Dólar Oficial")
compra_mep, venta_mep = obtener_dolar(URL_MEP, "Dólar MEP")

# Calcular la Brecha Cambiaria con Dólar MEP
if venta_oficial and compra_mep:
    brecha = ((compra_mep - venta_oficial) / venta_oficial) * 100
    print(f"\n📊 Brecha Cambiaria (Dólar MEP): {brecha:.2f}%")
    print(f"💵 Dólar Oficial Venta: ${venta_oficial}")
    print(f"💵 Dólar MEP Compra: ${compra_mep}\n")
else:
    print("❌ No se pudo calcular la brecha cambiaria.")
