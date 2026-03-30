# """
# Cliente unificado para Places API (New) - Google Maps Platform
# Implementa Malla Universal e Banco de Dados SQLite (Cache Espacial) para economia de API.
# """

# import requests
# import math
# import sqlite3
# import json
# import pandas as pd
# from typing import Dict, List, Optional, Tuple
# from config.settings import GOOGLE_MAPS_API_KEY

# class GooglePlacesAPI:
#     BASE_URL = "https://places.googleapis.com/v1/places"
    
#     # Tamanho da célula da Malla Universal em graus (0.015 graus ≈ 1.6 km no equador)
#     # Este valor é fixo e imutável para garantir que a grade global nunca mude.
#     GRID_DEG = 0.015 
    
#     def __init__(self):
#         self.api_key = GOOGLE_MAPS_API_KEY
#         self.headers_eletropostos = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours'
#         }
#         self.headers_pois = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.primaryType,places.userRatingCount'
#         }
#         self._inicializar_banco_dados()

#     def _inicializar_banco_dados(self):
#         """Cria o banco de dados local SQLite e as tabelas se não existirem."""
#         self.conn = sqlite3.connect('evcs_database.db', check_same_thread=False)
#         cursor = self.conn.cursor()
        
#         # Tabela para PONTOS DE INTERESSE (POIs)
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS pois (
#                 place_id TEXT PRIMARY KEY,
#                 nome TEXT,
#                 tipo TEXT,
#                 categoria TEXT,
#                 lat REAL,
#                 lng REAL,
#                 avaliacoes INTEGER,
#                 peso_base REAL,
#                 peso_dinamico REAL
#             )
#         ''')
        
#         # Tabela para ELETROPOSTOS
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS eletropostos (
#                 place_id TEXT PRIMARY KEY,
#                 lat REAL,
#                 lng REAL,
#                 dados_completos_json TEXT
#             )
#         ''')
        
#         # Tabela de CONTROLE DA MALHA UNIVERSAL (Para saber quais áreas já pesquisamos)
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS malha_cache (
#                 cell_id TEXT,
#                 tipo_busca TEXT, -- 'POI_Varejo', 'Eletropostos', etc.
#                 PRIMARY KEY (cell_id, tipo_busca)
#             )
#         ''')
#         self.conn.commit()

#     @staticmethod
#     def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """Calcula a distância em metros entre duas coordenadas"""
#         R = 6371000 
#         phi1, phi2 = math.radians(lat1), math.radians(lat2)
#         delta_phi = math.radians(lat2 - lat1)
#         delta_lambda = math.radians(lon2 - lon1)
        
#         a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
#         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#         return R * c

#     def _obter_celulas_universais(self, lat_centro: float, lng_centro: float, raio_m: int) -> List[Tuple[str, float, float, int]]:
#         """
#         Mapeia o círculo do usuário para a Malla Universal fixa.
#         Retorna as células necessárias para cobrir a área selecionada.
#         """
#         # Bounding box do círculo
#         lat_offset = (raio_m / 111320.0)
#         lng_offset = (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
        
#         lat_min, lat_max = lat_centro - lat_offset, lat_centro + lat_offset
#         lng_min, lng_max = lng_centro - lng_offset, lng_centro + lng_offset
        
#         # Índices da grade universal
#         min_y = math.floor(lat_min / self.GRID_DEG)
#         max_y = math.floor(lat_max / self.GRID_DEG)
#         min_x = math.floor(lng_min / self.GRID_DEG)
#         max_x = math.floor(lng_max / self.GRID_DEG)
        
#         celulas = []
#         # Raio necessário para a API cobrir a célula quadrada (diagonal / 2)
#         raio_busca_celula = int((math.sqrt(2) * (self.GRID_DEG * 111320)) / 2) + 50 
        
#         for y in range(min_y, max_y + 1):
#             for x in range(min_x, max_x + 1):
#                 cell_id = f"cell_{y}_{x}"
#                 c_lat = (y + 0.5) * self.GRID_DEG
#                 c_lng = (x + 0.5) * self.GRID_DEG
#                 celulas.append((cell_id, c_lat, c_lng, raio_busca_celula))
                
#         return celulas

#     def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
#         """Busca POIs usando o Banco de Dados. Só consome API em áreas virgens."""
#         cursor = self.conn.cursor()
#         celulas_necessarias = self._obter_celulas_universais(lat, lng, raio)
#         url = f"{self.BASE_URL}:searchNearby"
        
#         novas_consultas = 0

#         for cell_id, c_lat, c_lng, c_raio in celulas_necessarias:
#             for cat_nome, cat_data in categorias_config.items():
#                 chave_busca = f"POI_{cat_nome}"
                
#                 # 1. Verifica se esta célula já foi mapeada para esta categoria
#                 cursor.execute("SELECT 1 FROM malha_cache WHERE cell_id = ? AND tipo_busca = ?", (cell_id, chave_busca))
#                 ja_pesquisado = cursor.fetchone()
                
#                 if not ja_pesquisado:
#                     novas_consultas += 1
#                     # 2. Área virgem: Consultar API do Google
#                     payload = {
#                         "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
#                         "includedTypes": cat_data["types"],
#                         "maxResultCount": 20
#                     }
#                     try:
#                         response = requests.post(url, json=payload, headers=self.headers_pois)
#                         if response.status_code == 200:
#                             places = response.json().get('places', [])
#                             for p in places:
#                                 if 'location' in p and 'id' in p:
#                                     avaliacoes = p.get('userRatingCount', 1)
#                                     peso_dinamico = cat_data["peso"] * math.log10(avaliacoes + 10)
                                    
#                                     # Salvar no Banco (INSERT OR IGNORE evita duplicatas nas bordas)
#                                     cursor.execute('''
#                                         INSERT OR IGNORE INTO pois (place_id, nome, tipo, categoria, lat, lng, avaliacoes, peso_base, peso_dinamico)
#                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
#                                     ''', (
#                                         p['id'], p.get('displayName', {}).get('text', 'Desconhecido'),
#                                         p.get('primaryType', 'Desconhecido'), cat_nome,
#                                         p['location']['latitude'], p['location']['longitude'],
#                                         avaliacoes, cat_data["peso"], peso_dinamico
#                                     ))
#                     except Exception as e:
#                         print(f"Erro API: {e}")
                    
#                     # 3. Marcar célula como pesquisada (mesmo que venha vazia, para não gastar API de novo)
#                     cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
#                     self.conn.commit()

#         if novas_consultas > 0:
#             print(f"✓ Banco Atualizado: Foram feitas {novas_consultas} novas consultas à API.")
#         else:
#             print(f"⚡ Cache Hit: Área 100% carregada do Banco de Dados. Custo API: $0.")

#         # 4. Extrair TUDO do banco e filtrar pelo círculo real do usuário
#         df_completo = pd.read_sql_query("SELECT * FROM pois", self.conn)
        
#         # Filtro de distância estrito (Haversine)
#         if not df_completo.empty:
#             df_completo['distancia'] = df_completo.apply(lambda row: self._calcular_distancia_haversine(lat, lng, row['lat'], row['lng']), axis=1)
#             df_filtrado = df_completo[df_completo['distancia'] <= raio].copy()
#             # Renomear colunas para manter compatibilidade com o resto do seu código
#             df_filtrado.rename(columns={'nome': 'Nome', 'tipo': 'Tipo', 'categoria': 'Categoria', 'lat': 'Lat', 'lng': 'Lng', 'avaliacoes': 'Avaliacoes_Reais', 'peso_base': 'Peso_Base', 'peso_dinamico': 'Peso'}, inplace=True)
#             return df_filtrado
        
#         return pd.DataFrame()

#     def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
#         """Busca Eletropostos usando a mesma lógica de Banco de Dados."""
#         lat, lng = location
#         cursor = self.conn.cursor()
#         celulas_necessarias = self._obter_celulas_universais(lat, lng, radius_meters)
#         url = f"{self.BASE_URL}:searchNearby"
        
#         chave_busca = "ELETROPOSTOS"
        
#         for cell_id, c_lat, c_lng, c_raio in celulas_necessarias:
#             cursor.execute("SELECT 1 FROM malha_cache WHERE cell_id = ? AND tipo_busca = ?", (cell_id, chave_busca))
#             ja_pesquisado = cursor.fetchone()
            
#             if not ja_pesquisado:
#                 payload = {
#                     "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
#                     "includedTypes": ['electric_vehicle_charging_station']
#                 }
#                 try:
#                     response = requests.post(url, json=payload, headers=self.headers_eletropostos)
#                     if response.status_code == 200:
#                         places = response.json().get('places', [])
#                         for p in places:
#                             if 'location' in p and 'id' in p:
#                                 cursor.execute('''
#                                     INSERT OR IGNORE INTO eletropostos (place_id, lat, lng, dados_completos_json)
#                                     VALUES (?, ?, ?, ?)
#                                 ''', (p['id'], p['location']['latitude'], p['location']['longitude'], json.dumps(p)))
#                 except Exception as e:
#                     print(f"Erro API EV: {e}")
                
#                 cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
#                 self.conn.commit()

#         # Extrair todos os eletropostos do banco e filtrar por distância
#         cursor.execute("SELECT dados_completos_json, lat, lng FROM eletropostos")
#         todos_evs = cursor.fetchall()
        
#         resultados_filtrados = []
#         for dados_json, ev_lat, ev_lng in todos_evs:
#             distancia_real = self._calcular_distancia_haversine(lat, lng, ev_lat, ev_lng)
#             if distancia_real <= radius_meters:
#                 posto = json.loads(dados_json)
#                 posto['distancia_centro_m'] = round(distancia_real)
#                 resultados_filtrados.append(posto)
                
#         return resultados_filtrados

# # Padrão Singleton para manter a conexão do banco aberta
# _google_places_client = None

# def get_google_places_client() -> GooglePlacesAPI:
#     global _google_places_client
#     if _google_places_client is None:
#         _google_places_client = GooglePlacesAPI()
#     return _google_places_client












"""
Cliente unificado para Places API (New) - Google Maps Platform
Implementa Malla Universal e Banco de Dados SQLite (Cache Espacial) para economia de API.
"""

import requests
import math
import sqlite3
import json
import pandas as pd
from typing import Dict, List, Optional, Tuple
from config.settings import GOOGLE_MAPS_API_KEY

class GooglePlacesAPI:
    BASE_URL = "https://places.googleapis.com/v1/places"
    
    # Tamanho da célula da Malla Universal em graus (0.015 graus ≈ 1.6 km no equador)
    # Este valor é fixo e imutável para garantir que a grade global nunca mude.
    GRID_DEG = 0.015 
    
    def __init__(self):
        self.api_key = GOOGLE_MAPS_API_KEY
        self.headers_eletropostos = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours'
        }
        self.headers_pois = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.primaryType,places.userRatingCount'
        }
        self._inicializar_banco_dados()

    def _inicializar_banco_dados(self):
        """Cria o banco de dados local SQLite e as tabelas se não existirem."""
        self.conn = sqlite3.connect('evcs_database.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Tabela para PONTOS DE INTERESSE (POIs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pois (
                place_id TEXT PRIMARY KEY,
                nome TEXT,
                tipo TEXT,
                categoria TEXT,
                lat REAL,
                lng REAL,
                avaliacoes INTEGER,
                peso_base REAL,
                peso_dinamico REAL
            )
        ''')
        
        # Tabela para ELETROPOSTOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eletropostos (
                place_id TEXT PRIMARY KEY,
                lat REAL,
                lng REAL,
                dados_completos_json TEXT
            )
        ''')
        
        # Tabela de CONTROLE DA MALHA UNIVERSAL (Para saber quais áreas já pesquisamos)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS malha_cache (
                cell_id TEXT,
                tipo_busca TEXT, -- 'POI_Varejo', 'Eletropostos', etc.
                PRIMARY KEY (cell_id, tipo_busca)
            )
        ''')
        self.conn.commit()

    @staticmethod
    def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula a distância em metros entre duas coordenadas"""
        R = 6371000 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    def _obter_celulas_universais(self, lat_centro: float, lng_centro: float, raio_m: int) -> List[Tuple[str, float, float, int]]:
        """
        Mapeia o círculo do usuário para a Malla Universal fixa.
        Retorna as células necessárias para cobrir a área selecionada.
        """
        # Bounding box do círculo
        lat_offset = (raio_m / 111320.0)
        lng_offset = (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
        
        lat_min, lat_max = lat_centro - lat_offset, lat_centro + lat_offset
        lng_min, lng_max = lng_centro - lng_offset, lng_centro + lng_offset
        
        # Índices da grade universal
        min_y = math.floor(lat_min / self.GRID_DEG)
        max_y = math.floor(lat_max / self.GRID_DEG)
        min_x = math.floor(lng_min / self.GRID_DEG)
        max_x = math.floor(lng_max / self.GRID_DEG)
        
        celulas = []
        # Raio necessário para a API cobrir a célula quadrada (diagonal / 2)
        raio_busca_celula = int((math.sqrt(2) * (self.GRID_DEG * 111320)) / 2) + 50 
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                cell_id = f"cell_{y}_{x}"
                c_lat = (y + 0.5) * self.GRID_DEG
                c_lng = (x + 0.5) * self.GRID_DEG
                celulas.append((cell_id, c_lat, c_lng, raio_busca_celula))
                
        return celulas

    def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
        """Busca POIs usando o Banco de Dados. Só consome API em áreas virgens."""
        cursor = self.conn.cursor()
        celulas_necessarias = self._obter_celulas_universais(lat, lng, raio)
        url = f"{self.BASE_URL}:searchNearby"
        
        novas_consultas = 0

        for cell_id, c_lat, c_lng, c_raio in celulas_necessarias:
            for cat_nome, cat_data in categorias_config.items():
                chave_busca = f"POI_{cat_nome}"
                
                # 1. Verifica se esta célula já foi mapeada para esta categoria
                cursor.execute("SELECT 1 FROM malha_cache WHERE cell_id = ? AND tipo_busca = ?", (cell_id, chave_busca))
                ja_pesquisado = cursor.fetchone()
                
                if not ja_pesquisado:
                    novas_consultas += 1
                    # 2. Área virgem: Consultar API do Google
                    payload = {
                        "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
                        "includedTypes": cat_data["types"],
                        "maxResultCount": 20
                    }
                    try:
                        response = requests.post(url, json=payload, headers=self.headers_pois)
                        if response.status_code == 200:
                            places = response.json().get('places', [])
                            for p in places:
                                if 'location' in p and 'id' in p:
                                    avaliacoes = p.get('userRatingCount', 1)
                                    peso_dinamico = cat_data["peso"] * math.log10(avaliacoes + 10)
                                    
                                    # Salvar no Banco (INSERT OR IGNORE evita duplicatas nas bordas)
                                    cursor.execute('''
                                        INSERT OR IGNORE INTO pois (place_id, nome, tipo, categoria, lat, lng, avaliacoes, peso_base, peso_dinamico)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        p['id'], p.get('displayName', {}).get('text', 'Desconhecido'),
                                        p.get('primaryType', 'Desconhecido'), cat_nome,
                                        p['location']['latitude'], p['location']['longitude'],
                                        avaliacoes, cat_data["peso"], peso_dinamico
                                    ))
                    except Exception as e:
                        print(f"Erro API: {e}")
                    
                    # 3. Marcar célula como pesquisada (mesmo que venha vazia, para não gastar API de novo)
                    cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
                    self.conn.commit()

        if novas_consultas > 0:
            print(f"✓ Banco Atualizado: Foram feitas {novas_consultas} novas consultas à API.")
        else:
            print(f"Cache Hit: Área 100% carregada do Banco de Dados. Custo API: $0.")

        # 4. Extrair TUDO do banco e filtrar pelo círculo real do usuário
        df_completo = pd.read_sql_query("SELECT * FROM pois", self.conn)
        
        # Filtro de distância estrito (Haversine)
        if not df_completo.empty:
            df_completo['distancia'] = df_completo.apply(lambda row: self._calcular_distancia_haversine(lat, lng, row['lat'], row['lng']), axis=1)
            df_filtrado = df_completo[df_completo['distancia'] <= raio].copy()
            # Renomear colunas para manter compatibilidade com o resto do seu código
            df_filtrado.rename(columns={'nome': 'Nome', 'tipo': 'Tipo', 'categoria': 'Categoria', 'lat': 'Lat', 'lng': 'Lng', 'avaliacoes': 'Avaliacoes_Reais', 'peso_base': 'Peso_Base', 'peso_dinamico': 'Peso'}, inplace=True)
            return df_filtrado
        
        return pd.DataFrame()

    def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
        """Busca Eletropostos usando a mesma lógica de Banco de Dados."""
        lat, lng = location
        cursor = self.conn.cursor()
        celulas_necessarias = self._obter_celulas_universais(lat, lng, radius_meters)
        url = f"{self.BASE_URL}:searchNearby"
        
        chave_busca = "ELETROPOSTOS"
        
        for cell_id, c_lat, c_lng, c_raio in celulas_necessarias:
            cursor.execute("SELECT 1 FROM malha_cache WHERE cell_id = ? AND tipo_busca = ?", (cell_id, chave_busca))
            ja_pesquisado = cursor.fetchone()
            
            if not ja_pesquisado:
                payload = {
                    "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
                    "includedTypes": ['electric_vehicle_charging_station']
                }
                try:
                    response = requests.post(url, json=payload, headers=self.headers_eletropostos)
                    if response.status_code == 200:
                        places = response.json().get('places', [])
                        for p in places:
                            if 'location' in p and 'id' in p:
                                cursor.execute('''
                                    INSERT OR IGNORE INTO eletropostos (place_id, lat, lng, dados_completos_json)
                                    VALUES (?, ?, ?, ?)
                                ''', (p['id'], p['location']['latitude'], p['location']['longitude'], json.dumps(p)))
                except Exception as e:
                    print(f"Erro API EV: {e}")
                
                cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
                self.conn.commit()

        # Extrair todos os eletropostos do banco e filtrar por distância
        cursor.execute("SELECT dados_completos_json, lat, lng FROM eletropostos")
        todos_evs = cursor.fetchall()
        
        resultados_filtrados = []
        for dados_json, ev_lat, ev_lng in todos_evs:
            distancia_real = self._calcular_distancia_haversine(lat, lng, ev_lat, ev_lng)
            if distancia_real <= radius_meters:
                posto = json.loads(dados_json)
                posto['distancia_centro_m'] = round(distancia_real)
                resultados_filtrados.append(posto)
                
        return resultados_filtrados

    def ajustar_coordenada_para_via(self, lat: float, lng: float) -> Tuple[float, float]:
        """
        NOVO: Usa a Geocoding API (Reverse Geocoding) para 'puxar' o ponto
        matemático para a rua ou endereço real mais próximo.
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lng}",
            "key": self.api_key,
            "result_type": "street_address|route|premise"
        }
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    # Pega a coordenada exata do endereço real retornado
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
        except Exception as e:
            print(f"Erro no Reverse Geocoding (Snap to Road): {e}")
        
        # Se falhar, retorna a coordenada matemática original como fallback
        return lat, lng

# Padrão Singleton para manter a conexão do banco aberta
_google_places_client = None

def get_google_places_client() -> GooglePlacesAPI:
    global _google_places_client
    if _google_places_client is None:
        _google_places_client = GooglePlacesAPI()
    return _google_places_client