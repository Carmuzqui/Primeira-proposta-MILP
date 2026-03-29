"""
Configurações globais do projeto
Exploracao-APIs-Google
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretórios do projeto
BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / 'cache'
DADOS_DIR = BASE_DIR / 'dados'

# Criar diretórios se não existirem
CACHE_DIR.mkdir(exist_ok=True)
DADOS_DIR.mkdir(exist_ok=True)

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Validar API Key
if not GOOGLE_MAPS_API_KEY:
    raise ValueError("GOOGLE_MAPS_API_KEY não encontrada no arquivo .env")

# Configurações de cache
CACHE_ENABLED = True
CACHE_TTL_DAYS = 7  # Tempo de vida do cache em dias

# Configurações de área padrão (Campinas, SP)
DEFAULT_CENTER = {
    'lat': -22.9056,
    'lng': -47.0608
}
DEFAULT_ZOOM = 12
DEFAULT_RADIUS_KM = 5.0

# Limites de requisições (evitar exceder quotas)
API_LIMITS = {
    'directions': 2500,      # Por dia
    'distance_matrix': 2500,
    'places': 5000,
    'roads': 2500
}

# Tipos de POIs relevantes para eletropostos
POI_TYPES = [
    'shopping_mall',
    'supermarket',
    'parking',
    'gas_station',
    'restaurant',
    'cafe',
    'store'
]

# Configurações de tráfego
TRAFFIC_PERIODS = [7, 9, 12, 14, 18, 20, 22]  # Horas do dia para análise

# Parâmetros para estimativa de VEs
EV_ADOPTION_RATE = 0.02  # 2% do parque vehicular (ajustável)

# Configurações do Streamlit
STREAMLIT_CONFIG = {
    'page_title': 'Exploração APIs Google',
    'page_icon': '🗺️',
    'layout': 'wide',
    'initial_sidebar_state': 'collapsed'  # Sidebar oculto por padrão
}