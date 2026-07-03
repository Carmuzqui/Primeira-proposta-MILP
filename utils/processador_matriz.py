"""
utils/processador_matriz.py
Módulo responsável por ler a matriz O-D do Excel, cruzar com as coordenadas 
do SQLite e aplicar os filtros locais (Haversine e Fluxo) para economizar API.
"""

import pandas as pd
import sqlite3
import math
import os

def _calcular_haversine(lat1, lon1, lat2, lon2):
    """Calcula a distância em linha reta (km) entre dois pontos."""
    R = 6371.0 # Raio da Terra em km
    
    # Converte graus para radianos
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def preparar_candidatos_rotas(caminho_excel, aba_matriz, db_path, fluxo_minimo, dist_minima_km):
    """
    1. Lê a matriz O-D do Excel.
    2. Transforma (Melt) de Matriz para Lista (Origem, Destino, Fluxo).
    3. Puxa as coordenadas do SQLite.
    4. Aplica os filtros para retornar apenas as rotas que valem a pena consultar no Google.
    """
    
    if not os.path.exists(caminho_excel):
        raise FileNotFoundError(f"Arquivo Excel não encontrado: {caminho_excel}")
        
    if not os.path.exists(db_path):
        raise FileNotFoundError("Banco de dados SQLite não encontrado. Rode a geocodificação primeiro.")

    # Passo 3: Carregar a Matriz e transformar em lista
    # Usamos index_col=0 porque a Coluna A tem os Node_IDs de Origem
    df_matriz = pd.read_excel(caminho_excel, sheet_name=aba_matriz, index_col=0)
    
    # Transforma a matriz quadrada em formato tabular: Origem | Destino | Fluxo
    # O .stack() remove os NaNs/Zeros dependendo de como o Excel está formatado
    df_lista = df_matriz.stack().reset_index()
    df_lista.columns = ['Origem_ID', 'Destino_ID', 'Fluxo']
    
    # Filtro 1: Remover rotas circulares (Origem == Destino) e fluxos irrelevantes
    df_lista = df_lista[df_lista['Origem_ID'] != df_lista['Destino_ID']]
    df_lista = df_lista[df_lista['Fluxo'] >= fluxo_minimo]
    
    # Passo 4: Cruzamento Espacial (Buscar coordenadas locais)
    conn = sqlite3.connect(db_path)
    # Lemos apenas as coordenadas geocodificadas
    df_coords = pd.read_sql_query("SELECT address, lat, lng FROM geocache", conn)
    conn.close()
    
    # Como o seu Node_ID está dentro da string de endereço ou temos que mapear?
    # No seu script original, a tabela 'geocache' salvou a coluna 'address' (ex: "Campinas, SP, Brasil").
    # Precisaremos da aba de Centroides para mapear Node_ID -> Address -> Lat/Lng
    df_centroides = pd.read_excel(caminho_excel, sheet_name='Centroides')
    df_centroides['address'] = df_centroides['Centroide'] + ", " + df_centroides['UF'] + ", Brasil"
    
    # Cria um dicionário rápido de Node_ID -> Coordenadas
    df_map = pd.merge(df_centroides, df_coords, on='address', how='inner')
    dict_coords = df_map.set_index('Node_ID')[['lat', 'lng']].to_dict('index')

    rotas_filtradas = []
    
    # Aplica o Filtro Haversine
    for _, row in df_lista.iterrows():
        origem = row['Origem_ID']
        destino = row['Destino_ID']
        fluxo = row['Fluxo']
        
        # Só processa se tivermos as coordenadas dos dois pontos
        if origem in dict_coords and destino in dict_coords:
            lat1, lng1 = dict_coords[origem]['lat'], dict_coords[origem]['lng']
            lat2, lng2 = dict_coords[destino]['lat'], dict_coords[destino]['lng']
            
            dist_km = _calcular_haversine(lat1, lng1, lat2, lng2)
            
            # Filtro 2: Distância mínima
            if dist_km >= dist_minima_km:
                rotas_filtradas.append({
                    'Origem_ID': origem,
                    'Lat_O': lat1,
                    'Lng_O': lng1,
                    'Destino_ID': destino,
                    'Lat_D': lat2,
                    'Lng_D': lng2,
                    'Fluxo': fluxo,
                    'Dist_Reta_km': dist_km
                })
                
    # Retorna as rotas ordenadas pelos maiores fluxos primeiro (para priorizar no limite da API)
    df_final = pd.DataFrame(rotas_filtradas)
    if not df_final.empty:
        df_final = df_final.sort_values(by='Fluxo', ascending=False).reset_index(drop=True)
        
    return df_final