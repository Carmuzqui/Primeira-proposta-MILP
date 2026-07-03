"""
utils/api_rotas.py
Módulo para consultar a Google Directions API respeitando limites rígidos e usando cache.
"""

import requests
import sqlite3
import pandas as pd
from config.settings import GOOGLE_MAPS_API_KEY

def obter_rotas_com_cache(df_candidatos, db_path, limite_api):
    """
    Verifica o cache e consulta a API do Google apenas para rotas inéditas,
    respeitando o 'limite_api'.
    Retorna um DataFrame com a polilinha de cada rota viável.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Garantir que a tabela de cache de rotas existe
    cursor.execute('''CREATE TABLE IF NOT EXISTS rotas_cache (
        origem_id TEXT,
        destino_id TEXT,
        polyline TEXT,
        distancia_metros REAL,
        PRIMARY KEY (origem_id, destino_id)
    )''')
    conn.commit()

    rotas_finais = []
    consultas_api_realizadas = 0
    rotas_do_cache = 0

    url_base = "https://maps.googleapis.com/maps/api/directions/json"

    for _, row in df_candidatos.iterrows():
        origem = row['Origem_ID']
        destino = row['Destino_ID']
        fluxo = row['Fluxo']
        
        # 1. Verificar Cache
        cursor.execute("SELECT polyline, distancia_metros FROM rotas_cache WHERE origem_id = ? AND destino_id = ?", (origem, destino))
        cache_hit = cursor.fetchone()
        
        if cache_hit:
            rotas_finais.append({
                'Origem_ID': origem,
                'Destino_ID': destino,
                'Fluxo': fluxo,
                'Polyline': cache_hit[0],
                'Distancia_Metros': cache_hit[1],
                'Fonte': 'Cache'
            })
            rotas_do_cache += 1
            continue # Vai para a próxima rota sem gastar API
            
        # 2. Se não está no cache, verificar se ainda temos orçamento
        if consultas_api_realizadas >= limite_api:
            # Já gastamos o limite. Ignoramos as rotas restantes.
            continue
            
        # 3. Chamar a API do Google
        lat_o, lng_o = row['Lat_O'], row['Lng_O']
        lat_d, lng_d = row['Lat_D'], row['Lng_D']
        
        params = {
            "origin": f"{lat_o},{lng_o}",
            "destination": f"{lat_d},{lng_d}",
            "key": GOOGLE_MAPS_API_KEY
        }
        
        try:
            response = requests.get(url_base, params=params)
            data = response.json()
            
            if data.get('status') == 'OK':
                rota = data['routes'][0]
                polyline = rota['overview_polyline']['points']
                dist_m = rota['legs'][0]['distance']['value']
                
                # Salvar no Cache
                cursor.execute(
                    "INSERT INTO rotas_cache (origem_id, destino_id, polyline, distancia_metros) VALUES (?, ?, ?, ?)",
                    (origem, destino, polyline, dist_m)
                )
                conn.commit()
                
                rotas_finais.append({
                    'Origem_ID': origem,
                    'Destino_ID': destino,
                    'Fluxo': fluxo,
                    'Polyline': polyline,
                    'Distancia_Metros': dist_m,
                    'Fonte': 'API'
                })
                consultas_api_realizadas += 1
                
        except Exception as e:
            print(f"Erro na API para a rota {origem}->{destino}: {e}")

    conn.close()
    
    # Transformar resultado em DataFrame
    df_resultado = pd.DataFrame(rotas_finais)
    
    return df_resultado, consultas_api_realizadas, rotas_do_cache