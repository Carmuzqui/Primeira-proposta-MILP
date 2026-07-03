# import os
# import pandas as pd
# import requests
# import sqlite3
# from tqdm import tqdm
# from config.settings import GOOGLE_MAPS_API_KEY

# def get_lat_lng(address, conn):
#     """
#     Obtiene latitud y longitud desde el caché SQLite o consumiendo la API de Google Geocoding.
#     """
#     cursor = conn.cursor()
    
#     # 1. Buscar en Caché
#     cursor.execute("SELECT lat, lng FROM geocache WHERE address = ?", (address,))
#     row = cursor.fetchone()
#     if row:
#         return row[0], row[1]
    
#     # 2. Chamar API si no está en caché
#     url = "https://maps.googleapis.com/maps/api/geocode/json"
    
#     # IMPORTANTE: Usar 'params' asegura que los espacios y acentos (ej. São Paulo) se codifiquen bien.
#     params = {
#         "address": address,
#         "key": GOOGLE_MAPS_API_KEY
#     }
    
#     try:
#         response = requests.get(url, params=params)
#         response.raise_for_status() # Verifica si hay errores HTTP (ej. 404, 500)
#         data = response.json()
        
#         if data.get('status') == 'OK' and data.get('results'):
#             location = data['results'][0]['geometry']['location']
#             lat = location['lat']
#             lng = location['lng']
            
#             # Guardar en caché
#             cursor.execute("INSERT INTO geocache (address, lat, lng) VALUES (?, ?, ?)", (address, lat, lng))
#             conn.commit()
            
#             return lat, lng
#         else:
#             # Manejo de ZERO_RESULTS u otros status de la API
#             print(f"\n[Aviso] No se encontró el lugar '{address}'. Status: {data.get('status')}")
#             return None, None
            
#     except Exception as e:
#         print(f"\n[Error] Fallo en la conexión para '{address}': {e}")
#         return None, None

# def main():
#     # Inicializar Base de Datos
#     conn = sqlite3.connect('geocache.db')
#     conn.execute('''CREATE TABLE IF NOT EXISTS geocache (
#         address TEXT PRIMARY KEY,
#         lat REAL,
#         lng REAL
#     )''')

#     # Leer archivo (Asegúrate de que la ruta sea correcta)
#     input_file = 'dados/Matrizes PNT 2016-2017.xlsx'
#     try:
#         df = pd.read_excel(input_file, sheet_name='Centroides')
#     except FileNotFoundError:
#         print(f"Error: No se encontró el archivo en la ruta '{input_file}'")
#         conn.close()
#         return

#     # Si quieres procesar todo, quita el .head(25)
#     df = df.head(25)
#     results = []

#     print("Iniciando geocodificación...")
#     for index, row in tqdm(df.iterrows(), total=len(df)):
#         node_id = row.get('Node_ID')
#         centroide = row.get('Centroide')
#         uf = row.get('UF')
        
#         # Construir el string de búsqueda. Ej: "Campinas, SP, Brasil"
#         address = f"{centroide}, {uf}, Brasil"
        
#         lat, lng = get_lat_lng(address, conn)
        
#         results.append({
#             'Node_ID': node_id,
#             'Centroide': centroide,
#             'UF': uf,
#             'Latitude': lat,
#             'Longitude': lng
#         })

#     # Cerrar conexión
#     conn.close()

#     # Guardar resultados
#     output_df = pd.DataFrame(results)
#     output_file = 'dados/Matrizes_PNT_geocodificado.xlsx'
    
#     # Crear el directorio 'dados' si no existe
#     os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
#     output_df.to_excel(output_file, index=False)
#     print(f"\n¡Geocodificación concluida! Archivo guardado en: {output_file}")

# if __name__ == "__main__":
#     main()








import sys
import os

# Adiciona dinamicamente a pasta raiz do projeto ao PATH do Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import requests
import sqlite3
from tqdm import tqdm
from config.settings import GOOGLE_MAPS_API_KEY

def get_lat_lng(address, conn):
    """
    Obtiene latitud y longitud desde el caché SQLite o consumiendo la API de Google Geocoding.
    """
    cursor = conn.cursor()
    
    # 1. Buscar en Caché
    cursor.execute("SELECT lat, lng FROM geocache WHERE address = ?", (address,))
    row = cursor.fetchone()
    if row:
        return row[0], row[1]
    
    # 2. Chamar API si no está en caché
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    # IMPORTANTE: Usar 'params' asegura que los espacios y acentos se codifiquen bien.
    params = {
        "address": address,
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status() # Verifica si hay errores HTTP
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('results'):
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            
            # Guardar en caché
            cursor.execute("INSERT INTO geocache (address, lat, lng) VALUES (?, ?, ?)", (address, lat, lng))
            conn.commit()
            
            return lat, lng
        else:
            # Manejo de ZERO_RESULTS u otros status
            print(f"\n[Aviso] No se encontró el lugar '{address}'. Status: {data.get('status')}")
            return None, None
            
    except Exception as e:
        print(f"\n[Error] Fallo en la conexión para '{address}': {e}")
        return None, None

def main():
    # Inicializar Base de Datos
    conn = sqlite3.connect('geocache.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS geocache (
        address TEXT PRIMARY KEY,
        lat REAL,
        lng REAL
    )''')

    # Leer archivo 
    input_file = 'dados/Matrizes PNT 2016-2017.xlsx'
    try:
        df = pd.read_excel(input_file, sheet_name='Centroides')
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en la ruta '{input_file}'")
        conn.close()
        return

    # REMOVIDO: df = df.head(25) -> Agora o script processará todas as linhas do Excel

    results = []

    print(f"Iniciando geocodificação de {len(df)} centroides...")
    for index, row in tqdm(df.iterrows(), total=len(df)):
        node_id = row.get('Node_ID')
        centroide = row.get('Centroide')
        uf = row.get('UF')
        
        # Construir el string de búsqueda.
        address = f"{centroide}, {uf}, Brasil"
        
        lat, lng = get_lat_lng(address, conn)
        
        results.append({
            'Node_ID': node_id,
            'Centroide': centroide,
            'UF': uf,
            'Latitude': lat,
            'Longitude': lng
        })

    # Cerrar conexión
    conn.close()

    # Guardar resultados
    output_df = pd.DataFrame(results)
    output_file = 'dados/Matrizes_PNT_geocodificado.xlsx'
    
    # Crear el directorio 'dados' si no existe
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    output_df.to_excel(output_file, index=False)
    print(f"\n¡Geocodificación concluida! Archivo guardado en: {output_file}")

if __name__ == "__main__":
    main()