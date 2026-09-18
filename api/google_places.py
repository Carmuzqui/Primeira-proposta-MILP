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
#             print(f"Cache Hit: Área 100% carregada do Banco de Dados. Custo API: $0.")

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

#     def ajustar_coordenada_para_via(self, lat: float, lng: float) -> Tuple[float, float]:
#         """
#         NOVO: Usa a Geocoding API (Reverse Geocoding) para 'puxar' o ponto
#         matemático para a rua ou endereço real mais próximo.
#         """
#         url = "https://maps.googleapis.com/maps/api/geocode/json"
#         params = {
#             "latlng": f"{lat},{lng}",
#             "key": self.api_key,
#             "result_type": "street_address|route|premise"
#         }
#         try:
#             response = requests.get(url, params=params)
#             if response.status_code == 200:
#                 data = response.json()
#                 if data.get("results"):
#                     # Pega a coordenada exata do endereço real retornado
#                     location = data["results"][0]["geometry"]["location"]
#                     return location["lat"], location["lng"]
#         except Exception as e:
#             print(f"Erro no Reverse Geocoding (Snap to Road): {e}")
        
#         # Se falhar, retorna a coordenada matemática original como fallback
#         return lat, lng

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

Correções desta versão:
  1. Uma célula só é marcada como pesquisada quando a consulta retorna 200 (sem exceção);
     falhas não envenenam mais o cache e são reprocessadas na próxima corrida.
  2. Falhas ficam visíveis: status_code e um trecho do corpo são impressos quando não é 200.
  3. Throttle e backoff: pausa entre requisições e retentativa com espera crescente em 429/5xx
     e em quedas de conexão (SSL), para não atropelar a API.
  4. Teto de novas consultas por sessão (iniciar_sessao_consultas), para testes controlados.
"""

import time
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
        # Controle de sessão (teto de novas consultas e throttle)
        self.limite_novas_consultas: Optional[int] = None   # None = sem limite
        self.novas_consultas_sessao: int = 0
        self._aviso_limite: bool = False
        self.pausa_entre: float = 0.12                       # segundos entre requisições novas
        self._inicializar_banco_dados()

    # ------------------------------------------------------------------
    # Controle de sessão de consultas (chamar no início de cada "Gerar")
    # ------------------------------------------------------------------
    def iniciar_sessao_consultas(self, limite: Optional[int] = None):
        """Reinicia o contador e define o teto de NOVAS consultas para esta corrida.
        limite=None significa sem limite."""
        self.limite_novas_consultas = limite
        self.novas_consultas_sessao = 0
        self._aviso_limite = False

    def _pode_consultar(self) -> bool:
        """True se ainda há orçamento de novas consultas nesta sessão."""
        if self.limite_novas_consultas is None:
            return True
        if self.novas_consultas_sessao < self.limite_novas_consultas:
            return True
        if not self._aviso_limite:
            print(f"⚠️ Limite de {self.limite_novas_consultas} novas consultas atingido nesta corrida. "
                  f"As demais células ficam para a próxima (não foram marcadas).")
            self._aviso_limite = True
        return False

    # ------------------------------------------------------------------
    # POST com throttle e backoff
    # ------------------------------------------------------------------
    def _post_com_retentativa(self, url, payload, headers, tentativas=4, pausa_base=0.6):
        """Envia o POST com pausa e retentativa. Retorna a Response (mesmo se != 200)
        ou None se todas as tentativas caíram por erro de conexão."""
        resp = None
        for i in range(tentativas):
            time.sleep(self.pausa_entre)  # throttle: não atropelar a API
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=20)
            except requests.exceptions.RequestException as e:
                espera = pausa_base * (2 ** i)
                print(f"  conexão falhou ({e.__class__.__name__}); nova tentativa em {espera:.1f}s")
                time.sleep(espera)
                resp = None
                continue
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 500, 502, 503, 504):
                espera = pausa_base * (2 ** i)
                print(f"  status {resp.status_code} (limite/servidor); aguardando {espera:.1f}s "
                      f"(retentativa {i + 1}/{tentativas})")
                time.sleep(espera)
                continue
            # Erro duro (400, 403 de billing/quota, etc.): repetir não adianta.
            return resp
        return resp

    def _inicializar_banco_dados(self):
        """Cria o banco de dados local SQLite e as tabelas se não existirem."""
        self.conn = sqlite3.connect('evcs_database.db', check_same_thread=False)
        cursor = self.conn.cursor()

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eletropostos (
                place_id TEXT PRIMARY KEY,
                lat REAL,
                lng REAL,
                dados_completos_json TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS malha_cache (
                cell_id TEXT,
                tipo_busca TEXT,
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
        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _obter_celulas_universais(self, lat_centro: float, lng_centro: float, raio_m: int) -> List[Tuple[str, float, float, int]]:
        """Mapeia o círculo do usuário para a Malla Universal fixa."""
        lat_offset = (raio_m / 111320.0)
        lng_offset = (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
        lat_min, lat_max = lat_centro - lat_offset, lat_centro + lat_offset
        lng_min, lng_max = lng_centro - lng_offset, lng_centro + lng_offset

        min_y = math.floor(lat_min / self.GRID_DEG)
        max_y = math.floor(lat_max / self.GRID_DEG)
        min_x = math.floor(lng_min / self.GRID_DEG)
        max_x = math.floor(lng_max / self.GRID_DEG)

        celulas = []
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

                cursor.execute("SELECT 1 FROM malha_cache WHERE cell_id = ? AND tipo_busca = ?", (cell_id, chave_busca))
                if cursor.fetchone():
                    continue  # já pesquisado

                if not self._pode_consultar():
                    continue  # sem orçamento nesta sessão; NÃO marca, fica para depois

                self.novas_consultas_sessao += 1
                novas_consultas += 1

                payload = {
                    "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
                    "includedTypes": cat_data["types"],
                    "maxResultCount": 20
                }
                resp = self._post_com_retentativa(url, payload, self.headers_pois)
                sucesso = resp is not None and resp.status_code == 200

                if sucesso:
                    places = resp.json().get('places', [])
                    for p in places:
                        if 'location' in p and 'id' in p:
                            avaliacoes = p.get('userRatingCount', 1)
                            peso_dinamico = cat_data["peso"] * math.log10(avaliacoes + 10)
                            cursor.execute('''
                                INSERT OR IGNORE INTO pois (place_id, nome, tipo, categoria, lat, lng, avaliacoes, peso_base, peso_dinamico)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                p['id'], p.get('displayName', {}).get('text', 'Desconhecido'),
                                p.get('primaryType', 'Desconhecido'), cat_nome,
                                p['location']['latitude'], p['location']['longitude'],
                                avaliacoes, cat_data["peso"], peso_dinamico
                            ))
                    # Só marca a célula quando a consulta foi bem-sucedida.
                    cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
                    self.conn.commit()
                else:
                    if resp is not None:
                        print(f"POI '{cat_nome}' status {resp.status_code}: {resp.text[:180]}")
                    else:
                        print(f"POI '{cat_nome}': falha de conexão após retentativas (célula não marcada).")

        if novas_consultas > 0:
            print(f"✓ Banco Atualizado: Foram feitas {novas_consultas} novas consultas à API.")
        else:
            print(f"Cache Hit: Área 100% carregada do Banco de Dados. Custo API: $0.")

        df_completo = pd.read_sql_query("SELECT * FROM pois", self.conn)
        if not df_completo.empty:
            df_completo['distancia'] = df_completo.apply(
                lambda row: self._calcular_distancia_haversine(lat, lng, row['lat'], row['lng']), axis=1)
            df_filtrado = df_completo[df_completo['distancia'] <= raio].copy()
            df_filtrado.rename(columns={'nome': 'Nome', 'tipo': 'Tipo', 'categoria': 'Categoria', 'lat': 'Lat',
                                        'lng': 'Lng', 'avaliacoes': 'Avaliacoes_Reais', 'peso_base': 'Peso_Base',
                                        'peso_dinamico': 'Peso'}, inplace=True)
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
            if cursor.fetchone():
                continue

            if not self._pode_consultar():
                continue

            self.novas_consultas_sessao += 1

            payload = {
                "locationRestriction": {"circle": {"center": {"latitude": c_lat, "longitude": c_lng}, "radius": c_raio}},
                "includedTypes": ['electric_vehicle_charging_station']
            }
            resp = self._post_com_retentativa(url, payload, self.headers_eletropostos)
            sucesso = resp is not None and resp.status_code == 200

            if sucesso:
                places = resp.json().get('places', [])
                for p in places:
                    if 'location' in p and 'id' in p:
                        cursor.execute('''
                            INSERT OR IGNORE INTO eletropostos (place_id, lat, lng, dados_completos_json)
                            VALUES (?, ?, ?, ?)
                        ''', (p['id'], p['location']['latitude'], p['location']['longitude'], json.dumps(p)))
                cursor.execute("INSERT INTO malha_cache (cell_id, tipo_busca) VALUES (?, ?)", (cell_id, chave_busca))
                self.conn.commit()
            else:
                if resp is not None:
                    print(f"EV status {resp.status_code}: {resp.text[:180]}")
                else:
                    print("EV: falha de conexão após retentativas (célula não marcada).")

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
        """Usa a Geocoding API (Reverse Geocoding) para 'puxar' o ponto matemático
        para a rua ou endereço real mais próximo."""
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "latlng": f"{lat},{lng}",
            "key": self.api_key,
            "result_type": "street_address|route|premise"
        }
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    location = data["results"][0]["geometry"]["location"]
                    return location["lat"], location["lng"]
        except Exception as e:
            print(f"Erro no Reverse Geocoding (Snap to Road): {e}")
        return lat, lng


# Padrão Singleton para manter a conexão do banco aberta
_google_places_client = None

def get_google_places_client() -> GooglePlacesAPI:
    global _google_places_client
    if _google_places_client is None:
        _google_places_client = GooglePlacesAPI()
    return _google_places_client