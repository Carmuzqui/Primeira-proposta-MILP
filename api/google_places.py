# """
# Cliente unificado para Places API (New) - Google Maps Platform
# Responsável por extrair POIs (Demanda) e Eletropostos (Concorrência).
# """

# import requests
# import math
# import pandas as pd
# from typing import Dict, List, Tuple
# from config.settings import GOOGLE_MAPS_API_KEY

# class GooglePlacesAPI:
#     BASE_URL = "https://places.googleapis.com/v1/places"
    
#     def __init__(self):
#         self.api_key = GOOGLE_MAPS_API_KEY

#     @staticmethod
#     def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """Calcula a distância em metros entre duas coordenadas."""
#         R = 6371000 
#         phi1, phi2 = math.radians(lat1), math.radians(lat2)
#         delta_phi = math.radians(lat2 - lat1)
#         delta_lambda = math.radians(lon2 - lon1)
        
#         a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
#         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#         return R * c

#     def nearby_search(self, location: Tuple[float, float], radius_meters: int, included_types: List[str], field_mask: str) -> List[Dict]:
#         """Método base para fazer requisições à API de Places."""
#         url = f"{self.BASE_URL}:searchNearby"
#         headers = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': field_mask
#         }
#         payload = {
#             "locationRestriction": {
#                 "circle": {
#                     "center": {"latitude": location[0], "longitude": location[1]},
#                     "radius": radius_meters
#                 }
#             },
#             "includedTypes": included_types,
#             "maxResultCount": 20 
#         }
        
#         try:
#             response = requests.post(url, json=payload, headers=headers)
#             if response.status_code == 200:
#                 return response.json().get('places', [])
#         except Exception as e:
#             print(f"Erro na API Places: {e}")
            
#         return []

#     def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
#         """Busca Polos Geradores de Viagem (Demanda) e calcula o peso dinâmico."""
#         field_mask = 'places.displayName,places.location,places.primaryType,places.userRatingCount'
#         resultados_totais = []
        
#         for cat_nome, cat_data in categorias_config.items():
#             places = self.nearby_search((lat, lng), raio, cat_data["types"], field_mask)
#             for p in places:
#                 if 'location' in p:
#                     avaliacoes = p.get('userRatingCount', 1)
#                     fator_volume = math.log10(avaliacoes + 10)
#                     peso_dinamico = cat_data["peso"] * fator_volume

#                     resultados_totais.append({
#                         "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
#                         "Tipo": p.get('primaryType', 'Desconhecido'),
#                         "Categoria": cat_nome,
#                         "Lat": p['location']['latitude'],
#                         "Lng": p['location']['longitude'],
#                         "Avaliacoes_Reais": avaliacoes,
#                         "Peso_Base": cat_data["peso"],
#                         "Peso": peso_dinamico
#                     })
                    
#         return pd.DataFrame(resultados_totais)

#     def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
#         """Busca postos de recarga (Concorrência) usando malha de 9 pontos."""
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
#         field_mask = 'places.id,places.displayName,places.formattedAddress,places.location,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber'
        
#         for ponto in pontos_busca:
#             lugares = self.nearby_search(ponto, raio_busca, ['electric_vehicle_charging_station'], field_mask)
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
                    
#         return resultados_filtrados

# # Padrão Singleton para evitar múltiplas instâncias
# _google_places_client = None

# def get_google_places_client() -> GooglePlacesAPI:
#     global _google_places_client
#     if _google_places_client is None:
#         _google_places_client = GooglePlacesAPI()
#     return _google_places_client






# """
# Cliente unificado para Places API (New) - Google Maps Platform
# Responsável por extrair POIs (Demanda) e Eletropostos (Concorrência).
# """

# import requests
# import math
# import pandas as pd
# from typing import Dict, List, Tuple
# from config.settings import GOOGLE_MAPS_API_KEY

# class GooglePlacesAPI:
#     BASE_URL = "https://places.googleapis.com/v1/places"
    
#     def __init__(self):
#         self.api_key = GOOGLE_MAPS_API_KEY
#         # Restaurada a máscara global que garantia os 34 resultados no seu teste original
#         self.default_field_mask = 'places.id,places.displayName,places.formattedAddress,places.location,places.types,places.evChargeOptions,places.rating,places.userRatingCount,places.websiteUri,places.nationalPhoneNumber,places.regularOpeningHours'

#     @staticmethod
#     def _calcular_distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#         """Calcula a distância em metros entre duas coordenadas."""
#         R = 6371000 
#         phi1, phi2 = math.radians(lat1), math.radians(lat2)
#         delta_phi = math.radians(lat2 - lat1)
#         delta_lambda = math.radians(lon2 - lon1)
        
#         a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
#         c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
#         return R * c

#     def nearby_search(self, location: Tuple[float, float], radius_meters: int, included_types: List[str], field_mask: str = None) -> List[Dict]:
#         """Método base para fazer requisições à API de Places."""
#         url = f"{self.BASE_URL}:searchNearby"
        
#         # Se nenhuma máscara for passada, usa a global que você desenhou originalmente
#         current_mask = field_mask if field_mask else self.default_field_mask
        
#         headers = {
#             'Content-Type': 'application/json',
#             'X-Goog-Api-Key': self.api_key,
#             'X-Goog-FieldMask': current_mask
#         }
#         payload = {
#             "locationRestriction": {
#                 "circle": {
#                     "center": {"latitude": location[0], "longitude": location[1]},
#                     "radius": radius_meters
#                 }
#             },
#             "includedTypes": included_types,
#             "maxResultCount": 20 
#         }
        
#         try:
#             response = requests.post(url, json=payload, headers=headers)
#             if response.status_code == 200:
#                 return response.json().get('places', [])
#         except Exception as e:
#             print(f"Erro na API Places: {e}")
            
#         return []

#     def buscar_pois(self, lat: float, lng: float, raio: int, categorias_config: dict) -> pd.DataFrame:
#         """Busca Polos Geradores de Viagem (Demanda) e calcula o peso dinâmico."""
#         field_mask = 'places.displayName,places.location,places.primaryType,places.userRatingCount'
#         resultados_totais = []
        
#         for cat_nome, cat_data in categorias_config.items():
#             places = self.nearby_search((lat, lng), raio, cat_data["types"], field_mask)
#             for p in places:
#                 if 'location' in p:
#                     avaliacoes = p.get('userRatingCount', 1)
#                     fator_volume = math.log10(avaliacoes + 10)
#                     peso_dinamico = cat_data["peso"] * fator_volume

#                     resultados_totais.append({
#                         "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
#                         "Tipo": p.get('primaryType', 'Desconhecido'),
#                         "Categoria": cat_nome,
#                         "Lat": p['location']['latitude'],
#                         "Lng": p['location']['longitude'],
#                         "Avaliacoes_Reais": avaliacoes,
#                         "Peso_Base": cat_data["peso"],
#                         "Peso": peso_dinamico
#                     })
                    
#         return pd.DataFrame(resultados_totais)

#     def buscar_eletropostos(self, location: Tuple[float, float], radius_meters: int) -> List[Dict]:
#         """Busca postos de recarga (Concorrência) usando malha de 9 pontos."""
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
        
#         # REMOVIDO: a field_mask daqui. A API agora usará a self.default_field_mask original da sua classe.
#         for ponto in pontos_busca:
#             lugares = self.nearby_search(ponto, raio_busca, ['electric_vehicle_charging_station'])
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
                    
#         return resultados_filtrados

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
        
        todos_lugares = {}
        raio_busca = int(radius_meters * 0.55)
        
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
        """Busca Polos Geradores de Viagem (Demanda) isolado do método de eletropostos."""
        url = f"{self.BASE_URL}:searchNearby"
        headers_pois = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.displayName,places.location,places.primaryType,places.userRatingCount'
        }
        resultados_totais = []
        
        for cat_nome, cat_data in categorias_config.items():
            payload = {
                "locationRestriction": {
                    "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": raio}
                },
                "includedTypes": cat_data["types"],
                "maxResultCount": 20 
            }
            try:
                response = requests.post(url, json=payload, headers=headers_pois)
                if response.status_code == 200:
                    places = response.json().get('places', [])
                    for p in places:
                        if 'location' in p:
                            avaliacoes = p.get('userRatingCount', 1)
                            fator_volume = math.log10(avaliacoes + 10)
                            peso_dinamico = cat_data["peso"] * fator_volume

                            resultados_totais.append({
                                "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
                                "Tipo": p.get('primaryType', 'Desconhecido'),
                                "Categoria": cat_nome,
                                "Lat": p['location']['latitude'],
                                "Lng": p['location']['longitude'],
                                "Avaliacoes_Reais": avaliacoes,
                                "Peso_Base": cat_data["peso"],
                                "Peso": peso_dinamico
                            })
            except Exception as e:
                print(f"Erro na API Places (POIs): {e}")
                
        return pd.DataFrame(resultados_totais)

# Padrão Singleton para evitar múltiplas instâncias
_google_places_client = None

def get_google_places_client() -> GooglePlacesAPI:
    global _google_places_client
    if _google_places_client is None:
        _google_places_client = GooglePlacesAPI()
    return _google_places_client