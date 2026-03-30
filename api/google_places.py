# """
# Cliente unificado para Places API (New) - Google Maps Platform
# Responsável por extrair POIs (Demanda) e Eletropostos (Concorrência).
# """

# import requests
# import math
# import pandas as pd
# from typing import Dict, List, Optional, Tuple
# from config.settings import GOOGLE_MAPS_API_KEY

# class GooglePlacesAPI:
#     BASE_URL = "https://places.googleapis.com/v1/places"
    
#     def __init__(self):
#         self.api_key = GOOGLE_MAPS_API_KEY
#         # Headers originais e estritos para Eletropostos
#         self.headers_eletropostos = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours'
#         }

#     @staticmethod
#     def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """Calcula a distância em metros entre duas coordenadas usando a fórmula de Haversine"""
#         R = 6371000  # Raio médio da Terra em metros
#         phi1, phi2 = math.radians(lat1), math.radians(lat2)
#         delta_phi = math.radians(lat2 - lat1)
#         delta_lambda = math.radians(lon2 - lon1)
        
#         a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
#         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#         return R * c

#     def nearby_search_eletropostos(self, location: Tuple[float, float], radius_meters: int = 5000, included_types: Optional[List[str]] = None) -> List[Dict]:
#         """Método ORIGINAL exato para busca de eletropostos, sem contaminação de payload."""
#         url = f"{self.BASE_URL}:searchNearby"
#         payload = {
#             "locationRestriction": {
#                 "circle": {
#                     "center": {"latitude": location[0], "longitude": location[1]},
#                     "radius": radius_meters
#                 }
#             }
#         }
#         if included_types:
#             payload["includedTypes"] = included_types
        
#         try:
#             response = requests.post(url, json=payload, headers=self.headers_eletropostos)
#             response.raise_for_status()
#             return response.json().get('places', [])
#         except requests.exceptions.RequestException as e:
#             print(f"✗ Erro na Places API (New): {e}")
#             return []

#     def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
#         """Busca estações de carregamento usando malha de 9 pontos e filtro estrito."""
#         lat, lng = location
#         R = 6378137 
#         offset = radius_meters * 0.6 
        
#         dLat = (offset / R) * (180 / math.pi)
#         dLng = (offset / (R * math.cos(math.pi * lat / 180))) * (180 / math.pi)
        
#         pontos_busca = [
#             (lat, lng), (lat + dLat, lng), (lat - dLat, lng),
#             (lat, lng + dLng), (lat, lng - dLng),
#             (lat + dLat, lng + dLng), (lat + dLat, lng - dLng),
#             (lat - dLat, lng + dLng), (lat - dLat, lng - dLng)
#         ]
        
#         todos_lugares = {}
#         raio_busca = int(radius_meters * 0.55)
        
#         for ponto in pontos_busca:
#             lugares = self.nearby_search_eletropostos(
#                 location=ponto, 
#                 radius_meters=raio_busca, 
#                 included_types=['electric_vehicle_charging_station']
#             )
#             for lugar in lugares:
#                 if 'id' in lugar:
#                     todos_lugares[lugar['id']] = lugar
                    
#         resultados_filtrados = []
#         for lugar in todos_lugares.values():
#             if 'location' in lugar:
#                 lugar_lat = lugar['location']['latitude']
#                 lugar_lng = lugar['location']['longitude']
#                 distancia_real = self._calcular_distancia_haversine(lat, lng, lugar_lat, lugar_lng)
                
#                 if distancia_real <= radius_meters:
#                     lugar['distancia_centro_m'] = round(distancia_real)
#                     resultados_filtrados.append(lugar)
                    
#         print(f"✓ Places API: {len(resultados_filtrados)} eletropostos validados dentro do raio estrito.")
#         return resultados_filtrados

#     def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
#         """Busca Polos Geradores de Viagem (Demanda) isolado do método de eletropostos."""
#         url = f"{self.BASE_URL}:searchNearby"
#         headers_pois = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': 'places.displayName,places.location,places.primaryType,places.userRatingCount'
#         }
#         resultados_totais = []
        
#         for cat_nome, cat_data in categorias_config.items():
#             payload = {
#                 "locationRestriction": {
#                     "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": raio}
#                 },
#                 "includedTypes": cat_data["types"],
#                 "maxResultCount": 20 
#             }
#             try:
#                 response = requests.post(url, json=payload, headers=headers_pois)
#                 if response.status_code == 200:
#                     places = response.json().get('places', [])
#                     for p in places:
#                         if 'location' in p:
#                             avaliacoes = p.get('userRatingCount', 1)
#                             fator_volume = math.log10(avaliacoes + 10)
#                             peso_dinamico = cat_data["peso"] * fator_volume

#                             resultados_totais.append({
#                                 "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
#                                 "Tipo": p.get('primaryType', 'Desconhecido'),
#                                 "Categoria": cat_nome,
#                                 "Lat": p['location']['latitude'],
#                                 "Lng": p['location']['longitude'],
#                                 "Avaliacoes_Reais": avaliacoes,
#                                 "Peso_Base": cat_data["peso"],
#                                 "Peso": peso_dinamico
#                             })
#             except Exception as e:
#                 print(f"Erro na API Places (POIs): {e}")
                
#         return pd.DataFrame(resultados_totais)

# # Padrão Singleton para evitar múltiplas instâncias
# _google_places_client = None

# def get_google_places_client() -> GooglePlacesAPI:
#     global _google_places_client
#     if _google_places_client is None:
#         _google_places_client = GooglePlacesAPI()
#     return _google_places_client







"""
Cliente unificado para Places API (New) - Google Maps Platform
Responsável por extrair POIs (Demanda) e Eletropostos (Concorrência).
"""

import requests
import math
import pandas as pd
from typing import Dict, List, Optional, Tuple
from config.settings import GOOGLE_MAPS_API_KEY

class GooglePlacesAPI:
    BASE_URL = "https://places.googleapis.com/v1/places"
    
    def __init__(self):
        self.api_key = GOOGLE_MAPS_API_KEY
        # Headers originais e estritos para Eletropostos
        self.headers_eletropostos = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours'
        }

    @staticmethod
    def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula a distância em metros entre duas coordenadas usando a fórmula de Haversine"""
        R = 6371000  # Raio médio da Terra em metros
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    @staticmethod
    def _gerar_malha_busca(lat: float, lng: float, radius_meters: int) -> Tuple[List[Tuple[float, float]], int]:
        """Gera uma malha de 9 pontos (3x3) para cobrir uma área circular grande, evitando o limite de 20 resultados da API."""
        R = 6378137 
        offset = radius_meters * 0.6 
        
        dLat = (offset / R) * (180 / math.pi)
        dLng = (offset / (R * math.cos(math.pi * lat / 180))) * (180 / math.pi)
        
        pontos_busca = [
            (lat, lng), (lat + dLat, lng), (lat - dLat, lng),
            (lat, lng + dLng), (lat, lng - dLng),
            (lat + dLat, lng + dLng), (lat + dLat, lng - dLng),
            (lat - dLat, lng + dLng), (lat - dLat, lng - dLng)
        ]
        
        # O raio de cada sub-busca deve ser suficiente para sobrepor e não deixar buracos
        raio_busca = int(radius_meters * 0.55)
        return pontos_busca, raio_busca

    def nearby_search_eletropostos(self, location: Tuple[float, float], radius_meters: int = 5000, included_types: Optional[List[str]] = None) -> List[Dict]:
        """Método ORIGINAL exato para busca de eletropostos, sem contaminação de payload."""
        url = f"{self.BASE_URL}:searchNearby"
        payload = {
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": location[0], "longitude": location[1]},
                    "radius": radius_meters
                }
            }
        }
        if included_types:
            payload["includedTypes"] = included_types
        
        try:
            response = requests.post(url, json=payload, headers=self.headers_eletropostos)
            response.raise_for_status()
            return response.json().get('places', [])
        except requests.exceptions.RequestException as e:
            print(f"✗ Erro na Places API (New): {e}")
            return []

    def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
        """Busca estações de carregamento usando malha de 9 pontos e filtro estrito."""
        lat, lng = location
        pontos_busca, raio_busca = self._gerar_malha_busca(lat, lng, radius_meters)
        
        todos_lugares = {}
        
        for ponto in pontos_busca:
            lugares = self.nearby_search_eletropostos(
                location=ponto, 
                radius_meters=raio_busca, 
                included_types=['electric_vehicle_charging_station']
            )
            for lugar in lugares:
                if 'id' in lugar:
                    todos_lugares[lugar['id']] = lugar
                    
        resultados_filtrados = []
        for lugar in todos_lugares.values():
            if 'location' in lugar:
                lugar_lat = lugar['location']['latitude']
                lugar_lng = lugar['location']['longitude']
                distancia_real = self._calcular_distancia_haversine(lat, lng, lugar_lat, lugar_lng)
                
                if distancia_real <= radius_meters:
                    lugar['distancia_centro_m'] = round(distancia_real)
                    resultados_filtrados.append(lugar)
                    
        print(f"✓ Places API: {len(resultados_filtrados)} eletropostos validados dentro do raio estrito.")
        return resultados_filtrados

    def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
        """Busca Polos Geradores de Viagem (Demanda) usando malha de 9 pontos para maximizar a captura."""
        url = f"{self.BASE_URL}:searchNearby"
        headers_pois = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            # Adicionado places.id para garantir que não teremos duplicatas nas sobreposições dos círculos
            'X-Goog-FieldMask': 'places.id,places.displayName,places.location,places.primaryType,places.userRatingCount'
        }
        
        pontos_busca, raio_busca = self._gerar_malha_busca(lat, lng, raio)
        todos_pois = {} # Usaremos um dicionário para evitar duplicatas baseadas no ID do local
        
        for ponto in pontos_busca:
            for cat_nome, cat_data in categorias_config.items():
                payload = {
                    "locationRestriction": {
                        "circle": {"center": {"latitude": ponto[0], "longitude": ponto[1]}, "radius": raio_busca}
                    },
                    "includedTypes": cat_data["types"],
                    "maxResultCount": 20 
                }
                try:
                    response = requests.post(url, json=payload, headers=headers_pois)
                    if response.status_code == 200:
                        places = response.json().get('places', [])
                        for p in places:
                            if 'location' in p and 'id' in p:
                                place_id = p['id']
                                p_lat = p['location']['latitude']
                                p_lng = p['location']['longitude']
                                
                                # Verifica a distância real em relação ao centro original (não ao sub-centro)
                                distancia_real = self._calcular_distancia_haversine(lat, lng, p_lat, p_lng)
                                
                                # Adiciona apenas se estiver dentro do raio principal e ainda não tiver sido capturado
                                if distancia_real <= raio and place_id not in todos_pois:
                                    avaliacoes = p.get('userRatingCount', 1)
                                    fator_volume = math.log10(avaliacoes + 10)
                                    peso_dinamico = cat_data["peso"] * fator_volume

                                    todos_pois[place_id] = {
                                        "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
                                        "Tipo": p.get('primaryType', 'Desconhecido'),
                                        "Categoria": cat_nome,
                                        "Lat": p_lat,
                                        "Lng": p_lng,
                                        "Avaliacoes_Reais": avaliacoes,
                                        "Peso_Base": cat_data["peso"],
                                        "Peso": peso_dinamico
                                    }
                except Exception as e:
                    print(f"Erro na API Places (POIs): {e}")
                    
        print(f"✓ Places API: {len(todos_pois)} POIs validados dentro do raio estrito.")
        return pd.DataFrame(list(todos_pois.values()))

# Padrão Singleton para evitar múltiplas instâncias
_google_places_client = None

def get_google_places_client() -> GooglePlacesAPI:
    global _google_places_client
    if _google_places_client is None:
        _google_places_client = GooglePlacesAPI()
    return _google_places_client