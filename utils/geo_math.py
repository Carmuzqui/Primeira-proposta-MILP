"""
Módulo de utilitários matemáticos e espaciais.
Isola a lógica de cálculo de malha e centroides para o modelo de otimização.
"""

import math
import pandas as pd

def processar_grid_e_centroides(df_pois, lat_centro, lng_centro, raio_m, tamanho_grid_m=800):
    """
    Cria a grade virtual e calcula os centroides dos POIs para cada célula ativa.
    """
    if df_pois.empty:
        return pd.DataFrame(), None
        
    # 1 Grau de latitude = ~111.32 km (111320 m)
    lat_step = tamanho_grid_m / 111320.0
    lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_centro)))
    
    # Definir Bounding Box baseada no raio estrito
    lat_min = lat_centro - (raio_m / 111320.0)
    lng_min = lng_centro - (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
    
    # Atribuir cada POI à sua célula da matriz (i, j)
    df_pois['cell_i'] = ((df_pois['Lat'] - lat_min) / lat_step).astype(int)
    df_pois['cell_j'] = ((df_pois['Lng'] - lng_min) / lng_step).astype(int)
    
    # Agrupamento e cálculo do centroide por célula
    candidatos = df_pois.groupby(['cell_i', 'cell_j']).agg(
        Lat_Centroide=('Lat', 'mean'),
        Lng_Centroide=('Lng', 'mean'),
        Qtd_POIs=('Nome', 'count'),
        Score_Estimado=('Peso', 'sum')
    ).reset_index()
    
    info_grid = {
        'lat_min': lat_min, 'lng_min': lng_min,
        'lat_step': lat_step, 'lng_step': lng_step
    }
    
    return candidatos, info_grid