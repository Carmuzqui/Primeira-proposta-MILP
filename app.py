# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# Estimação de demanda gravitacional baseada em malha e Eletropostos.
# """

# import streamlit as st

# # Importando os módulos e componentes construídos
# from api.google_places import get_google_places_client
# from components.sidebar import render_sidebar
# from components.mapa import renderizar_mapa_completo
# from utils.geo_math import processar_grid_e_centroides

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # CSS para maximizar o uso da tela no mapa
# st.markdown("""
#     <style>
#     .main .block-container {
#         padding: 0.5rem 0.5rem 0rem 0.5rem;
#         max-width: 100%;
#     }
#     iframe {
#         width: 100%;
#         height: 90vh;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # --- CATEGORIAS DE BUSCA ---
# CATEGORIAS_POIS = {
#     "Varejo e lazer": {
#         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
#         "color": "blue",
#         "icon": "shopping-cart",
#         "peso": 3.0 
#     },
#     "Transporte": {
#         "types": ["bus_station", "subway_station", "transit_station"],
#         "color": "red",
#         "icon": "bus",
#         "peso": 2.0
#     },
#     "Serviços e saúde": {
#         "types": ["hospital", "bank", "university"],
#         "color": "purple",
#         "icon": "heart", 
#         "peso": 1.5
#     }
# }

# # --- INICIALIZAR ESTADO DA SESSÃO ---
# if 'dados_pois' not in st.session_state:
#     st.session_state.dados_pois = None
# if 'dados_eletropostos' not in st.session_state:
#     st.session_state.dados_eletropostos = None
# if 'dados_candidatos' not in st.session_state:
#     st.session_state.dados_candidatos = None
# if 'info_grid' not in st.session_state:
#     st.session_state.info_grid = None
# if 'analise_ativa' not in st.session_state:
#     st.session_state.analise_ativa = False

# # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# config = render_sidebar()

# # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# if config['btn_gerar']:
#     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
#         cliente_api = get_google_places_client()
        
#         # 1. Busca POIs (Demanda)
#         df_pois = cliente_api.buscar_pois(
#             lat=config['lat'], 
#             lng=config['lng'], 
#             raio=config['raio'], 
#             categorias_config=CATEGORIAS_POIS
#         )
#         st.session_state.dados_pois = df_pois
        
#         # 2. Busca Eletropostos (Concorrência)
#         eletropostos = cliente_api.buscar_eletropostos(
#             location=(config['lat'], config['lng']), 
#             radius_meters=config['raio']
#         )
#         st.session_state.dados_eletropostos = eletropostos
        
#         # 3. Processa Malha Matemática
#         candidatos, info_grid = processar_grid_e_centroides(
#             df_pois=df_pois, 
#             lat_centro=config['lat'], 
#             lng_centro=config['lng'], 
#             raio_m=config['raio'], 
#             tamanho_grid_m=config['tamanho_grid']
#         )
#         st.session_state.dados_candidatos = candidatos
#         st.session_state.info_grid = info_grid
        
#         st.session_state.analise_ativa = True

# # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# if st.session_state.analise_ativa:
#     if st.session_state.dados_pois.empty:
#         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
#     else:
#         # Chama o componente do mapa passando todos os dados processados e opções visuais
#         renderizar_mapa_completo(
#             lat=config['lat'],
#             lng=config['lng'],
#             raio=config['raio'],
#             df_pois=st.session_state.dados_pois,
#             df_cand=st.session_state.dados_candidatos,
#             grid=st.session_state.info_grid,
#             mostrar_nodos=config['mostrar_nodos'], # AQUI: Passando o novo parâmetro
#             mostrar_heatmap=config['mostrar_heatmap'],
#             mostrar_eletropostos=config['mostrar_eletropostos'],
#             dados_eletropostos=st.session_state.dados_eletropostos,
#             categorias_pois=CATEGORIAS_POIS
#         )
# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")











# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# Estimação de demanda gravitacional baseada em malha e Eletropostos.
# """

# import streamlit as st

# # Importando os módulos e componentes construídos
# from api.google_places import get_google_places_client
# from components.sidebar import render_sidebar
# from components.mapa import renderizar_mapa_completo
# from utils.geo_math import processar_grid_e_centroides

# # Importando o novo simulador financeiro/matemático
# from modelo.simulador import pré_computar_cenarios, mock_resolver_cplex

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # CSS para maximizar o uso da tela no mapa
# st.markdown("""
#     <style>
#     .main .block-container {
#         padding: 0.5rem 0.5rem 0rem 0.5rem;
#         max-width: 100%;
#     }
#     iframe {
#         width: 100%;
#         height: 90vh;
#     }
#     </style>
# """, unsafe_allow_html=True)

# # --- CATEGORIAS DE BUSCA ---
# CATEGORIAS_POIS = {
#     "Varejo e lazer": {
#         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
#         "color": "blue",
#         "icon": "shopping-cart",
#         "peso": 3.0 
#     },
#     "Transporte": {
#         "types": ["bus_station", "subway_station", "transit_station"],
#         "color": "red",
#         "icon": "bus",
#         "peso": 2.0
#     },
#     "Serviços e saúde": {
#         "types": ["hospital", "bank", "university"],
#         "color": "purple",
#         "icon": "heart", 
#         "peso": 1.5
#     }
# }

# # --- INICIALIZAR ESTADO DA SESSÃO ---
# if 'dados_pois' not in st.session_state:
#     st.session_state.dados_pois = None
# if 'dados_eletropostos' not in st.session_state:
#     st.session_state.dados_eletropostos = None
# if 'dados_candidatos' not in st.session_state:
#     st.session_state.dados_candidatos = None
# if 'info_grid' not in st.session_state:
#     st.session_state.info_grid = None
# if 'analise_ativa' not in st.session_state:
#     st.session_state.analise_ativa = False

# # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# config = render_sidebar()

# # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# if config['btn_gerar']:
#     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
#         cliente_api = get_google_places_client()
        
#         # 1. Busca POIs (Demanda)
#         df_pois = cliente_api.buscar_pois(
#             lat=config['lat'], 
#             lng=config['lng'], 
#             raio=config['raio'], 
#             categorias_config=CATEGORIAS_POIS
#         )
#         st.session_state.dados_pois = df_pois
        
#         # 2. Busca Eletropostos (Concorrência)
#         eletropostos = cliente_api.buscar_eletropostos(
#             location=(config['lat'], config['lng']), 
#             radius_meters=config['raio']
#         )
#         st.session_state.dados_eletropostos = eletropostos
        
#         # 3. Processa Malha Matemática
#         candidatos, info_grid = processar_grid_e_centroides(
#             df_pois=df_pois, 
#             lat_centro=config['lat'], 
#             lng_centro=config['lng'], 
#             raio_m=config['raio'], 
#             tamanho_grid_m=config['tamanho_grid']
#         )
#         st.session_state.dados_candidatos = candidatos
#         st.session_state.info_grid = info_grid
        
#         st.session_state.analise_ativa = True

# # --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO CPLEX) ---
# if config.get('btn_otimizar'):
#     if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
#         with st.spinner("Simulando atractividade e cenários combinatórios..."):
            
#             # Recupera os dados guardados na sessão
#             df_cand = st.session_state.dados_candidatos
#             dados_evs = st.session_state.dados_eletropostos or []
            
#             # Gera a matriz pré-computada R_c(S_c)
#             matriz_cplex = pré_computar_cenarios(
#                 df_cand=df_cand, 
#                 dados_evs=dados_evs,
#                 raio_influencia_m=1500, # Distância máxima para considerar como vizinho
#                 max_vizinhos=4          # Trava para evitar explosão combinatória
#             )
            
#             # Exibe os resultados no terminal do VS Code
#             mock_resolver_cplex(matriz_cplex)
            
#             st.success("Matriz de cenários gerada com sucesso! Verifique o terminal do VS Code.")
#     else:
#         st.warning("Por favor, gere a malha de candidatos primeiro antes de otimizar.")

# # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# if st.session_state.analise_ativa:
#     if st.session_state.dados_pois.empty:
#         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
#     else:
#         # Chama o componente do mapa passando todos os dados processados e opções visuais
#         renderizar_mapa_completo(
#             lat=config['lat'],
#             lng=config['lng'],
#             raio=config['raio'],
#             df_pois=st.session_state.dados_pois,
#             df_cand=st.session_state.dados_candidatos,
#             grid=st.session_state.info_grid,
#             mostrar_nodos=config['mostrar_nodos'], 
#             mostrar_heatmap=config['mostrar_heatmap'],
#             mostrar_eletropostos=config['mostrar_eletropostos'],
#             dados_eletropostos=st.session_state.dados_eletropostos,
#             categorias_pois=CATEGORIAS_POIS
#         )
# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")










"""
Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
Estimação de demanda gravitacional baseada em malha e Eletropostos.
"""

import streamlit as st

# Importando os módulos e componentes construídos
from api.google_places import get_google_places_client
from components.sidebar import render_sidebar
from components.mapa import renderizar_mapa_completo
from utils.geo_math import processar_grid_e_centroides

# Importando o simulador de cenários e o otimizador MILP (CPLEX)
from modelo.simulador import pré_computar_cenarios
from modelo.otimizador import resolver_modelo_cplex

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Designação eletropostos", layout="wide")

# CSS para maximizar o uso da tela no mapa
st.markdown("""
    <style>
    .main .block-container {
        padding: 0.5rem 0.5rem 0rem 0.5rem;
        max-width: 100%;
    }
    iframe {
        width: 100%;
        height: 90vh;
    }
    </style>
""", unsafe_allow_html=True)

# --- CATEGORIAS DE BUSCA ---
CATEGORIAS_POIS = {
    "Varejo e lazer": {
        "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
        "color": "blue",
        "icon": "shopping-cart",
        "peso": 3.0 
    },
    "Transporte": {
        "types": ["bus_station", "subway_station", "transit_station"],
        "color": "red",
        "icon": "bus",
        "peso": 2.0
    },
    "Serviços e saúde": {
        "types": ["hospital", "bank", "university"],
        "color": "purple",
        "icon": "heart", 
        "peso": 1.5
    }
}

# --- INICIALIZAR ESTADO DA SESSÃO ---
if 'dados_pois' not in st.session_state:
    st.session_state.dados_pois = None
if 'dados_eletropostos' not in st.session_state:
    st.session_state.dados_eletropostos = None
if 'dados_candidatos' not in st.session_state:
    st.session_state.dados_candidatos = None
if 'info_grid' not in st.session_state:
    st.session_state.info_grid = None
if 'analise_ativa' not in st.session_state:
    st.session_state.analise_ativa = False

# --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
config = render_sidebar()

# --- LÓGICA DE COLETA E PROCESSAMENTO ---
if config['btn_gerar']:
    with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
        cliente_api = get_google_places_client()
        
        # 1. Busca POIs (Demanda)
        df_pois = cliente_api.buscar_pois(
            lat=config['lat'], 
            lng=config['lng'], 
            raio=config['raio'], 
            categorias_config=CATEGORIAS_POIS
        )
        st.session_state.dados_pois = df_pois
        
        # 2. Busca Eletropostos (Concorrência)
        eletropostos = cliente_api.buscar_eletropostos(
            location=(config['lat'], config['lng']), 
            radius_meters=config['raio']
        )
        st.session_state.dados_eletropostos = eletropostos
        
        # 3. Processa Malha Matemática
        candidatos, info_grid = processar_grid_e_centroides(
            df_pois=df_pois, 
            lat_centro=config['lat'], 
            lng_centro=config['lng'], 
            raio_m=config['raio'], 
            tamanho_grid_m=config['tamanho_grid']
        )
        st.session_state.dados_candidatos = candidatos
        st.session_state.info_grid = info_grid
        
        st.session_state.analise_ativa = True

# --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO + CPLEX) ---
if config.get('btn_otimizar'):
    if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
        with st.spinner("Simulando cenários e resolvendo modelo MILP com CPLEX..."):
            
            # Recupera os dados guardados na sessão
            df_cand = st.session_state.dados_candidatos
            dados_evs = st.session_state.dados_eletropostos or []
            
            # 1. Gera a matriz pré-computada R_c(S_c)
            matriz_cplex = pré_computar_cenarios(
                df_cand=df_cand, 
                dados_evs=dados_evs,
                raio_influencia_m=1500, # Distância máxima para considerar como vizinho
                max_vizinhos=4          # Trava para evitar explosão combinatória
            )
            
            # 2. Resolve matematicamente com IBM CPLEX
            resultado = resolver_modelo_cplex(matriz_cplex)
            
            # 3. Exibe o resultado na interface
            if resultado and resultado['status'] == 'Optimal':
                st.success(f"✅ Otimização Concluída! Lucro Global Máximo Projetado: {resultado['lucro_total']:.2f}")
                
                nodos_str = ", ".join(resultado['nodos_selecionados']) if resultado['nodos_selecionados'] else "Nenhum (Todos deram prejuízo)"
                st.info(f"📍 Nodos selecionados para instalação: {nodos_str}")
                
                st.caption("Verifique o terminal do VS Code para os detalhes matemáticos da execução.")
            else:
                st.error("❌ Não foi possível encontrar uma solução viável para esta rede.")
                
    else:
        st.warning("Por favor, gere a malha de candidatos primeiro antes de otimizar.")

# --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
if st.session_state.analise_ativa:
    if st.session_state.dados_pois.empty:
        st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
    else:
        # Chama o componente do mapa passando todos os dados processados e opções visuais
        renderizar_mapa_completo(
            lat=config['lat'],
            lng=config['lng'],
            raio=config['raio'],
            df_pois=st.session_state.dados_pois,
            df_cand=st.session_state.dados_candidatos,
            grid=st.session_state.info_grid,
            mostrar_nodos=config['mostrar_nodos'], 
            mostrar_heatmap=config['mostrar_heatmap'],
            mostrar_eletropostos=config['mostrar_eletropostos'],
            dados_eletropostos=st.session_state.dados_eletropostos,
            categorias_pois=CATEGORIAS_POIS
        )
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")