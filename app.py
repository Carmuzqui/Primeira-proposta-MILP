# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# # Estimação de demanda gravitacional baseada em malha e Eletropostos.
# # """

# # import streamlit as st

# # # Importando os módulos e componentes construídos
# # from api.google_places import get_google_places_client
# # from components.sidebar import render_sidebar
# # from components.mapa import renderizar_mapa_completo
# # from utils.geo_math import processar_grid_e_centroides

# # # Importando o simulador de cenários e o otimizador MILP (CPLEX)
# # from modelo.simulador import pré_computar_cenarios
# # from modelo.otimizador import resolver_modelo_cplex

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # # CSS para maximizar o uso da tela no mapa
# # st.markdown("""
# #     <style>
# #     .main .block-container {
# #         padding: 0.5rem 0.5rem 0rem 0.5rem;
# #         max-width: 100%;
# #     }
# #     iframe {
# #         width: 100%;
# #         height: 90vh;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)

# # # --- CATEGORIAS DE BUSCA ---
# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
# #         "color": "blue",
# #         "icon": "shopping-cart",
# #         "peso": 3.0 
# #     },
# #     "Transporte": {
# #         "types": ["bus_station", "subway_station", "transit_station"],
# #         "color": "red",
# #         "icon": "bus",
# #         "peso": 2.0
# #     },
# #     "Serviços e saúde": {
# #         "types": ["hospital", "bank", "university"],
# #         "color": "purple",
# #         "icon": "heart", 
# #         "peso": 1.5
# #     }
# # }

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # if 'dados_pois' not in st.session_state:
# #     st.session_state.dados_pois = None
# # if 'dados_eletropostos' not in st.session_state:
# #     st.session_state.dados_eletropostos = None
# # if 'dados_candidatos' not in st.session_state:
# #     st.session_state.dados_candidatos = None
# # if 'info_grid' not in st.session_state:
# #     st.session_state.info_grid = None
# # if 'analise_ativa' not in st.session_state:
# #     st.session_state.analise_ativa = False

# # # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# # config = render_sidebar()

# # # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# # if config['btn_gerar']:
# #     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
# #         cliente_api = get_google_places_client()
        
# #         # 1. Busca POIs (Demanda)
# #         df_pois = cliente_api.buscar_pois(
# #             lat=config['lat'], 
# #             lng=config['lng'], 
# #             raio=config['raio'], 
# #             categorias_config=CATEGORIAS_POIS
# #         )
# #         st.session_state.dados_pois = df_pois
        
# #         # 2. Busca Eletropostos (Concorrência)
# #         eletropostos = cliente_api.buscar_eletropostos(
# #             location=(config['lat'], config['lng']), 
# #             radius_meters=config['raio']
# #         )
# #         st.session_state.dados_eletropostos = eletropostos
        
# #         # 3. Processa Malha Matemática
# #         candidatos, info_grid = processar_grid_e_centroides(
# #             df_pois=df_pois, 
# #             lat_centro=config['lat'], 
# #             lng_centro=config['lng'], 
# #             raio_m=config['raio'], 
# #             tamanho_grid_m=config['tamanho_grid']
# #         )
# #         st.session_state.dados_candidatos = candidatos
# #         st.session_state.info_grid = info_grid
        
# #         st.session_state.analise_ativa = True

# # # --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO + CPLEX) ---
# # if config.get('btn_otimizar'):
# #     if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
# #         with st.spinner("Simulando cenários e resolvendo modelo MILP com CPLEX..."):
            
# #             # Recupera os dados guardados na sessão
# #             df_cand = st.session_state.dados_candidatos
# #             dados_evs = st.session_state.dados_eletropostos or []
            
# #             # 1. Gera a matriz pré-computada R_c(S_c)
# #             matriz_cplex = pré_computar_cenarios(
# #                 df_cand=df_cand, 
# #                 dados_evs=dados_evs,
# #                 raio_influencia_m=1500, # Distância máxima para considerar como vizinho
# #                 max_vizinhos=4          # Trava para evitar explosão combinatória
# #             )
            
# #             # 2. Resolve matematicamente com IBM CPLEX
# #             resultado = resolver_modelo_cplex(matriz_cplex)
            
# #             # 3. Exibe o resultado na interface
# #             if resultado and resultado['status'] == 'Optimal':
# #                 st.success(f"✅ Otimização Concluída! Lucro Global Máximo Projetado: {resultado['lucro_total']:.2f}")
                
# #                 nodos_str = ", ".join(resultado['nodos_selecionados']) if resultado['nodos_selecionados'] else "Nenhum (Todos deram prejuízo)"
# #                 st.info(f"📍 Nodos selecionados para instalação: {nodos_str}")
                
# #                 st.caption("Verifique o terminal do VS Code para os detalhes matemáticos da execução.")
# #             else:
# #                 st.error("❌ Não foi possível encontrar uma solução viável para esta rede.")
                
# #     else:
# #         st.warning("Por favor, gere a malha de candidatos primeiro antes de otimizar.")

# # # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# # if st.session_state.analise_ativa:
# #     if st.session_state.dados_pois.empty:
# #         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
# #     else:
# #         # Chama o componente do mapa passando todos os dados processados e opções visuais
# #         renderizar_mapa_completo(
# #             lat=config['lat'],
# #             lng=config['lng'],
# #             raio=config['raio'],
# #             df_pois=st.session_state.dados_pois,
# #             df_cand=st.session_state.dados_candidatos,
# #             grid=st.session_state.info_grid,
# #             mostrar_nodos=config['mostrar_nodos'], 
# #             mostrar_heatmap=config['mostrar_heatmap'],
# #             mostrar_eletropostos=config['mostrar_eletropostos'],
# #             dados_eletropostos=st.session_state.dados_eletropostos,
# #             categorias_pois=CATEGORIAS_POIS
# #         )
# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")











# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# # Estimação de demanda gravitacional baseada em malha e Eletropostos.
# # """

# # import streamlit as st

# # # Importando os módulos e componentes construídos
# # from api.google_places import get_google_places_client
# # from components.sidebar import render_sidebar
# # from components.mapa import renderizar_mapa_completo
# # from utils.geo_math import processar_grid_e_centroides

# # # Importando o simulador de cenários e o otimizador MILP (CPLEX)
# # from modelo.simulador import pré_computar_cenarios
# # from modelo.otimizador import resolver_modelo_cplex

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # # CSS para maximizar o uso da tela no mapa
# # st.markdown("""
# #     <style>
# #     .main .block-container {
# #         padding: 0.5rem 0.5rem 0rem 0.5rem;
# #         max-width: 100%;
# #     }
# #     iframe {
# #         width: 100%;
# #         height: 90vh;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)

# # # --- CATEGORIAS DE BUSCA ---
# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
# #         "color": "blue",
# #         "icon": "shopping-cart",
# #         "peso": 3.0 
# #     },
# #     "Transporte": {
# #         "types": ["bus_station", "subway_station", "transit_station"],
# #         "color": "red",
# #         "icon": "bus",
# #         "peso": 2.0
# #     },
# #     "Serviços e saúde": {
# #         "types": ["hospital", "bank", "university"],
# #         "color": "purple",
# #         "icon": "heart", 
# #         "peso": 1.5
# #     }
# # }

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # if 'dados_pois' not in st.session_state:
# #     st.session_state.dados_pois = None
# # if 'dados_eletropostos' not in st.session_state:
# #     st.session_state.dados_eletropostos = None
# # if 'dados_candidatos' not in st.session_state:
# #     st.session_state.dados_candidatos = None
# # if 'info_grid' not in st.session_state:
# #     st.session_state.info_grid = None
# # if 'analise_ativa' not in st.session_state:
# #     st.session_state.analise_ativa = False

# # # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# # config = render_sidebar()

# # # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# # if config['btn_gerar']:
# #     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
# #         cliente_api = get_google_places_client()
        
# #         # 1. Busca POIs (Demanda)
# #         df_pois = cliente_api.buscar_pois(
# #             lat=config['lat'], 
# #             lng=config['lng'], 
# #             raio=config['raio'], 
# #             categorias_config=CATEGORIAS_POIS
# #         )
# #         st.session_state.dados_pois = df_pois
        
# #         # 2. Busca Eletropostos (Concorrência)
# #         eletropostos = cliente_api.buscar_eletropostos(
# #             location=(config['lat'], config['lng']), 
# #             radius_meters=config['raio']
# #         )
# #         st.session_state.dados_eletropostos = eletropostos
        
# #         # 3. Processa Malha Matemática
# #         candidatos, info_grid = processar_grid_e_centroides(
# #             df_pois=df_pois, 
# #             lat_centro=config['lat'], 
# #             lng_centro=config['lng'], 
# #             raio_m=config['raio'], 
# #             tamanho_grid_m=config['tamanho_grid']
# #         )
# #         st.session_state.dados_candidatos = candidatos
# #         st.session_state.info_grid = info_grid
        
# #         st.session_state.analise_ativa = True

# # # --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO + CPLEX) ---
# # if config.get('btn_otimizar'):
# #     if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
# #         with st.spinner("Garantindo cobertura de 85% e resolvendo modelo MILP com CPLEX..."):
            
# #             # Recupera os dados guardados na sessão
# #             df_cand = st.session_state.dados_candidatos
# #             dados_evs = st.session_state.dados_eletropostos or []
# #             df_pois = st.session_state.dados_pois # Necessário para checar a cobertura
            
# #             # 1. Gera a matriz pré-computada R_c(S_c) e o mapa de cobertura
# #             matriz_cplex, dados_cobertura = pré_computar_cenarios(
# #                 df_cand=df_cand, 
# #                 dados_evs=dados_evs,
# #                 df_pois=df_pois,
# #                 raio_influencia_m=1500, # Distância máxima para considerar como vizinho (concorrência)
# #                 max_vizinhos=4,         # Trava para evitar explosão combinatória
# #                 raio_cobertura_m=800    # ~10 minutos caminhando para ser considerado "atendido"
# #             )
            
# #             # 2. Resolve matematicamente com IBM CPLEX exigindo a meta de 85%
# #             resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, meta_cobertura_pct=0.85)
            
# #             # 3. Exibe o resultado na interface
# #             if resultado and resultado['status'] == 'Optimal':
# #                 st.success(f"✅ Otimização Concluída! Lucro Global Máximo Projetado: {resultado['lucro_total']:.2f}")
                
# #                 # Bloco de Qualidade da Rede (Novidade)
# #                 st.info(f"🎯 **Qualidade da Rede:** {resultado['cobertura_final']} de {resultado['total_pois']} POIs atendidos ({resultado['pct_cobertura']:.1f}% de Cobertura).")
                
# #                 nodos_str = ", ".join(resultado['nodos_selecionados']) if resultado['nodos_selecionados'] else "Nenhum"
# #                 st.write(f"📍 **Nodos selecionados para instalação:** {nodos_str}")
                
# #                 st.caption("Verifique o terminal do VS Code para os detalhes matemáticos da execução.")
# #             else:
# #                 st.error("❌ Modelo inviável: Nem instalando todos os candidatos foi possível atingir a meta de cobertura solicitada.")
                
# #     else:
# #         st.warning("Por favor, gere a malha de candidatos primeiro antes de otimizar.")

# # # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# # if st.session_state.analise_ativa:
# #     if st.session_state.dados_pois.empty:
# #         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
# #     else:
# #         # Chama o componente do mapa passando todos os dados processados e opções visuais
# #         renderizar_mapa_completo(
# #             lat=config['lat'],
# #             lng=config['lng'],
# #             raio=config['raio'],
# #             df_pois=st.session_state.dados_pois,
# #             df_cand=st.session_state.dados_candidatos,
# #             grid=st.session_state.info_grid,
# #             mostrar_nodos=config['mostrar_nodos'], 
# #             mostrar_heatmap=config['mostrar_heatmap'],
# #             mostrar_eletropostos=config['mostrar_eletropostos'],
# #             dados_eletropostos=st.session_state.dados_eletropostos,
# #             categorias_pois=CATEGORIAS_POIS
# #         )
# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")












# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# # Estimação de demanda gravitacional baseada em malha e Eletropostos.
# # """

# # import streamlit as st

# # from api.google_places import get_google_places_client
# # from components.sidebar import render_sidebar
# # from components.mapa import renderizar_mapa_completo
# # from utils.geo_math import processar_grid_e_centroides
# # from modelo.simulador import pré_computar_cenarios
# # from modelo.otimizador import resolver_modelo_cplex

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # st.markdown("""
# #     <style>
# #     .main .block-container {
# #         padding: 0.5rem 0.5rem 0rem 0.5rem;
# #         max-width: 100%;
# #     }
# #     iframe {
# #         width: 100%;
# #         height: 90vh;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)

# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
# #         "color": "blue",
# #         "icon": "shopping-cart",
# #         "peso": 3.0 
# #     },
# #     "Transporte": {
# #         "types": ["bus_station", "subway_station", "transit_station"],
# #         "color": "red",
# #         "icon": "bus",
# #         "peso": 2.0
# #     },
# #     "Serviços e saúde": {
# #         "types": ["hospital", "bank", "university"],
# #         "color": "purple",
# #         "icon": "heart", 
# #         "peso": 1.5
# #     }
# # }

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # if 'dados_pois' not in st.session_state:
# #     st.session_state.dados_pois = None
# # if 'dados_eletropostos' not in st.session_state:
# #     st.session_state.dados_eletropostos = None
# # if 'dados_candidatos' not in st.session_state:
# #     st.session_state.dados_candidatos = None
# # if 'info_grid' not in st.session_state:
# #     st.session_state.info_grid = None
# # if 'analise_ativa' not in st.session_state:
# #     st.session_state.analise_ativa = False
# # if 'nodos_otimizados' not in st.session_state:
# #     st.session_state.nodos_otimizados = []

# # # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# # config = render_sidebar()

# # # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# # if config['btn_gerar']:
# #     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
# #         # Limpar otimização anterior ao gerar nova malha
# #         st.session_state.nodos_otimizados = []
        
# #         cliente_api = get_google_places_client()
# #         df_pois = cliente_api.buscar_pois(config['lat'], config['lng'], config['raio'], CATEGORIAS_POIS)
# #         st.session_state.dados_pois = df_pois
        
# #         eletropostos = cliente_api.buscar_eletropostos((config['lat'], config['lng']), config['raio'])
# #         st.session_state.dados_eletropostos = eletropostos
        
# #         candidatos, info_grid = processar_grid_e_centroides(df_pois, config['lat'], config['lng'], config['raio'], config['tamanho_grid'])
# #         st.session_state.dados_candidatos = candidatos
# #         st.session_state.info_grid = info_grid
# #         st.session_state.analise_ativa = True

# # # --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO + CPLEX) ---
# # if config.get('btn_otimizar'):
# #     if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
# #         with st.spinner("Otimizando rede..."):
# #             matriz_cplex, dados_cobertura = pré_computar_cenarios(
# #                 st.session_state.dados_candidatos, 
# #                 st.session_state.dados_eletropostos or [],
# #                 st.session_state.dados_pois,
# #                 1500, 4, 800
# #             )
# #             resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, 0.85)
            
# #             if resultado and resultado['status'] == 'Optimal':
# #                 st.session_state.nodos_otimizados = resultado['nodos_selecionados']
# #             else:
# #                 st.error("Modelo inviável. Verifique o terminal.")
# #                 st.session_state.nodos_otimizados = []
# #     else:
# #         st.warning("Gere a malha de candidatos primeiro.")

# # # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# # if st.session_state.analise_ativa:
# #     if st.session_state.dados_pois.empty:
# #         st.warning("Nenhum POI encontrado nesse raio.")
# #     else:
# #         renderizar_mapa_completo(
# #             lat=config['lat'], lng=config['lng'], raio=config['raio'],
# #             df_pois=st.session_state.dados_pois, df_cand=st.session_state.dados_candidatos,
# #             grid=st.session_state.info_grid, mostrar_nodos=config['mostrar_nodos'], 
# #             mostrar_heatmap=config['mostrar_heatmap'], mostrar_eletropostos=config['mostrar_eletropostos'],
# #             dados_eletropostos=st.session_state.dados_eletropostos, categorias_pois=CATEGORIAS_POIS,
# #             nodos_otimizados=st.session_state.nodos_otimizados # NOVO PARÂMETRO
# #         )
# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")








# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# # Estimação de demanda gravitacional baseada em malha e Eletropostos.
# # """

# # import streamlit as st

# # from api.google_places import get_google_places_client
# # from components.sidebar import render_sidebar
# # from components.mapa import renderizar_mapa_completo
# # from utils.geo_math import processar_grid_e_centroides
# # from modelo.simulador import pré_computar_cenarios
# # from modelo.otimizador import resolver_modelo_cplex

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # st.markdown("""
# #     <style>
# #     .main .block-container {
# #         padding: 0.5rem 0.5rem 0rem 0.5rem;
# #         max-width: 100%;
# #     }
# #     iframe {
# #         width: 100%;
# #         height: 90vh;
# #     }
# #     </style>
# # """, unsafe_allow_html=True)

# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
# #         "color": "blue",
# #         "icon": "shopping-cart",
# #         "peso": 3.0 
# #     },
# #     "Transporte": {
# #         "types": ["bus_station", "subway_station", "transit_station"],
# #         "color": "red",
# #         "icon": "bus",
# #         "peso": 2.0
# #     },
# #     "Serviços e saúde": {
# #         "types": ["hospital", "bank", "university"],
# #         "color": "purple",
# #         "icon": "heart", 
# #         "peso": 1.5
# #     }
# # }

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # if 'dados_pois' not in st.session_state:
# #     st.session_state.dados_pois = None
# # if 'dados_eletropostos' not in st.session_state:
# #     st.session_state.dados_eletropostos = None
# # if 'dados_candidatos' not in st.session_state:
# #     st.session_state.dados_candidatos = None
# # if 'info_grid' not in st.session_state:
# #     st.session_state.info_grid = None
# # if 'analise_ativa' not in st.session_state:
# #     st.session_state.analise_ativa = False
# # if 'nodos_otimizados' not in st.session_state:
# #     st.session_state.nodos_otimizados = []

# # # --- RENDERIZAR SIDEBAR E OBTER PARÂMETROS ---
# # config = render_sidebar()

# # # --- LÓGICA DE COLETA E PROCESSAMENTO ---
# # if config['btn_gerar']:
# #     with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
# #         # Limpar otimização anterior ao gerar nova malha
# #         st.session_state.nodos_otimizados = []
        
# #         cliente_api = get_google_places_client()
# #         df_pois = cliente_api.buscar_pois(config['lat'], config['lng'], config['raio'], CATEGORIAS_POIS)
# #         st.session_state.dados_pois = df_pois
        
# #         eletropostos = cliente_api.buscar_eletropostos((config['lat'], config['lng']), config['raio'])
# #         st.session_state.dados_eletropostos = eletropostos
        
# #         candidatos, info_grid = processar_grid_e_centroides(df_pois, config['lat'], config['lng'], config['raio'], config['tamanho_grid'])
# #         st.session_state.dados_candidatos = candidatos
# #         st.session_state.info_grid = info_grid
# #         st.session_state.analise_ativa = True

# # # --- LÓGICA DE OTIMIZAÇÃO (PRÉ-PROCESSAMENTO + CPLEX) ---
# # if config.get('btn_otimizar'):
# #     if st.session_state.analise_ativa and st.session_state.dados_candidatos is not None and not st.session_state.dados_candidatos.empty:
# #         with st.spinner("Otimizando rede..."):
# #             matriz_cplex, dados_cobertura = pré_computar_cenarios(
# #                 st.session_state.dados_candidatos, 
# #                 st.session_state.dados_eletropostos or [],
# #                 st.session_state.dados_pois,
# #                 1500, 4, 800
# #             )
# #             resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, 0.85)
            
# #             if resultado and resultado['status'] == 'Optimal':
# #                 st.session_state.nodos_otimizados = resultado['nodos_selecionados']
# #             else:
# #                 st.error("Modelo inviável. Verifique o terminal.")
# #                 st.session_state.nodos_otimizados = []
# #     else:
# #         st.warning("Gere a malha de candidatos primeiro.")

# # # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# # if st.session_state.analise_ativa:
# #     if st.session_state.dados_pois.empty:
# #         st.warning("Nenhum POI encontrado nesse raio.")
# #     else:
# #         renderizar_mapa_completo(
# #             lat=config['lat'], 
# #             lng=config['lng'], 
# #             raio=config['raio'],
# #             df_pois=st.session_state.dados_pois, 
# #             df_cand=st.session_state.dados_candidatos,
# #             grid=st.session_state.info_grid, 
# #             dados_eletropostos=st.session_state.dados_eletropostos, 
# #             categorias_pois=CATEGORIAS_POIS,
# #             nodos_otimizados=st.session_state.nodos_otimizados
# #         )
# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")








# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
# Dois modos de varredura com a mesma lógica de busca:
#   - Urbano (raio): círculo em torno de um ponto.
#   - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
# """

# import os
# import math
# import numpy as np
# import pandas as pd
# import streamlit as st

# from api.google_places import get_google_places_client
# from components.sidebar import render_sidebar
# from components.mapa import renderizar_mapa_completo
# from utils.geo_math import processar_grid_e_centroides
# from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
# from modelo.simulador import pré_computar_cenarios
# from modelo.otimizador import resolver_modelo_cplex

# # Caminhos dos dados geográficos
# SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
# RODOVIAS_DIR = os.path.join("dados", "rodovias")

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Designação eletropostos", layout="wide")

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
# for chave, valor in {
#     'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
#     'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
#     'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
# }.items():
#     if chave not in st.session_state:
#         st.session_state[chave] = valor


# # ==========================================================
# # Helpers
# # ==========================================================
# def _haversine_m(lat0, lon0, lats, lons):
#     """Distância em metros de um ponto (lat0,lon0) a arrays de pontos."""
#     R = 6371000.0
#     p = np.pi / 180.0
#     lats = np.asarray(lats, dtype=float)
#     lons = np.asarray(lons, dtype=float)
#     a = (np.sin((lats - lat0) * p / 2) ** 2
#          + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
#     return 2 * R * np.arcsin(np.sqrt(a))


# def _construir_candidatos_rodovia(df_pois, centros, tamanho_grid_m=800, raio_ponto_m=800):
#     """
#     No modo rodovia, cada centro da corrente de círculos vira um candidato sobre a via
#     (sem 'Snap to Road', pois já está na estrada). Mantém o mesmo esquema de colunas
#     que o mapa e o simulador esperam: cell_i, cell_j, Lat_Centroide, Lng_Centroide,
#     Qtd_POIs, Score_Estimado.
#     """
#     if not centros:
#         return pd.DataFrame(), None

#     lats = [c["lat"] for c in centros]
#     lngs = [c["lng"] for c in centros]
#     lat_ref = sum(lats) / len(lats)
#     lat_step = tamanho_grid_m / 111320.0
#     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

#     tem_pois = df_pois is not None and not df_pois.empty
#     all_lat = lats + (list(df_pois["Lat"]) if tem_pois else [])
#     all_lng = lngs + (list(df_pois["Lng"]) if tem_pois else [])
#     lat_min, lng_min = min(all_lat), min(all_lng)

#     if tem_pois:
#         plat = df_pois["Lat"].to_numpy()
#         plng = df_pois["Lng"].to_numpy()
#         pw = df_pois["Peso"].to_numpy()
#     else:
#         plat = plng = pw = None

#     linhas = []
#     for c in centros:
#         la, lo = c["lat"], c["lng"]
#         if plat is not None and len(plat) > 0:
#             d = _haversine_m(la, lo, plat, plng)
#             m = d <= raio_ponto_m
#             qtd = int(m.sum())
#             score = float(pw[m].sum())
#         else:
#             qtd, score = 0, 0.0
#         linhas.append({
#             "cell_i": int((la - lat_min) / lat_step),
#             "cell_j": int((lo - lng_min) / lng_step),
#             "Lat_Centroide": la,
#             "Lng_Centroide": lo,
#             "Qtd_POIs": qtd,
#             "Score_Estimado": score,
#         })

#     cand = pd.DataFrame(linhas)
#     info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
#     return cand, info_grid


# def _coletar_urbano(cliente, cfg):
#     df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
#     eletropostos = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
#     cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
#     return df_pois, eletropostos, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"]


# def _coletar_rodovia(cliente, cfg, status):
#     if not cfg.get("rodovias_sel"):
#         st.warning("Selecione ao menos uma rodovia.")
#         return None
#     if not os.path.exists(SP_POLY_PATH):
#         st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
#         return None

#     poly = carregar_poligono_estado(SP_POLY_PATH)
#     dfs, evs, centros_all = [], {}, []

#     for rod in cfg["rodovias_sel"]:
#         arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
#         if not os.path.exists(arq):
#             st.warning(f"Arquivo não encontrado: {arq}")
#             continue
#         comps, km = carregar_tracado(arq, rod["ref"], poly)
#         centros, passo = gerar_cadeia_circulos(comps, cfg["raio"], cfg.get("fator", 1.0))
#         status.write(f"{rod['ref']}: {km:.0f} km em SP, {len(centros)} círculos (passo {passo:.1f} km)")
#         centros_all += centros

#         for c in centros:
#             df = cliente.buscar_pois(c["lat"], c["lng"], cfg["raio"], CATEGORIAS_POIS)
#             if df is not None and not df.empty:
#                 dfs.append(df)
#             for posto in cliente.buscar_eletropostos((c["lat"], c["lng"]), cfg["raio"]):
#                 loc = posto.get("location", {}) or {}
#                 chave = posto.get("id") or (loc.get("latitude"), loc.get("longitude"))
#                 evs[chave] = posto

#     df_pois = (pd.concat(dfs, ignore_index=True).drop_duplicates(subset="place_id")
#                if dfs else pd.DataFrame())
#     eletropostos = list(evs.values())
#     cand, grid = _construir_candidatos_rodovia(df_pois, centros_all, cfg["tamanho_grid"], cfg["tamanho_grid"])

#     if centros_all:
#         mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
#         mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
#     else:
#         mlat, mlng = -22.81, -47.06
#     # raio=0 evita desenhar um círculo de busca gigante no modo rodovia
#     return df_pois, eletropostos, cand, grid, mlat, mlng, 0


# # ==========================================================
# # Sidebar
# # ==========================================================
# config = render_sidebar()

# # ==========================================================
# # Coleta e processamento
# # ==========================================================
# if config["btn_gerar"]:
#     st.session_state.nodos_otimizados = []
#     cliente = get_google_places_client()

#     if config["modo"] == "Urbano (raio)":
#         with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
#             resultado = _coletar_urbano(cliente, config)
#     else:
#         with st.spinner("Varrendo rodovia(s) com a corrente de círculos..."):
#             status = st.empty()
#             resultado = _coletar_rodovia(cliente, config, status)

#     if resultado:
#         df_pois, eletr, cand, grid, mlat, mlng, mraio = resultado
#         st.session_state.dados_pois = df_pois
#         st.session_state.dados_eletropostos = eletr
#         st.session_state.dados_candidatos = cand
#         st.session_state.info_grid = grid
#         st.session_state.map_lat = mlat
#         st.session_state.map_lng = mlng
#         st.session_state.map_raio = mraio
#         st.session_state.analise_ativa = True

# # ==========================================================
# # Otimização (pré-processamento + CPLEX)
# # ==========================================================
# if config.get("btn_otimizar"):
#     cand = st.session_state.dados_candidatos
#     if st.session_state.analise_ativa and cand is not None and not cand.empty:
#         with st.spinner("Otimizando rede..."):
#             matriz_cplex, dados_cobertura = pré_computar_cenarios(
#                 st.session_state.dados_candidatos,
#                 st.session_state.dados_eletropostos or [],
#                 st.session_state.dados_pois,
#                 1500, 4, 800
#             )
#             resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, 0.85)
#             if resultado and resultado["status"] == "Optimal":
#                 st.session_state.nodos_otimizados = resultado["nodos_selecionados"]
#             else:
#                 st.error("Modelo inviável. Verifique o terminal.")
#                 st.session_state.nodos_otimizados = []
#     else:
#         st.warning("Gere a malha de candidatos primeiro.")

# # ==========================================================
# # Área principal (mapa em tela cheia)
# # ==========================================================
# if st.session_state.analise_ativa:
#     if st.session_state.dados_pois is None or st.session_state.dados_pois.empty:
#         st.warning("Nenhum POI encontrado.")
#     else:
#         renderizar_mapa_completo(
#             lat=st.session_state.map_lat,
#             lng=st.session_state.map_lng,
#             raio=st.session_state.map_raio,
#             df_pois=st.session_state.dados_pois,
#             df_cand=st.session_state.dados_candidatos,
#             grid=st.session_state.info_grid,
#             dados_eletropostos=st.session_state.dados_eletropostos,
#             categorias_pois=CATEGORIAS_POIS,
#             nodos_otimizados=st.session_state.nodos_otimizados
#         )
# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")






"""
Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
Dois modos de varredura com a mesma lógica de busca:
  - Urbano (raio): círculo em torno de um ponto.
  - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
"""

import os
import math
import numpy as np
import pandas as pd
import streamlit as st

from api.google_places import get_google_places_client
from components.sidebar import render_sidebar
from components.mapa import renderizar_mapa_completo
from utils.geo_math import processar_grid_e_centroides
from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
from modelo.simulador import pré_computar_cenarios
from modelo.otimizador import resolver_modelo_cplex

# Caminhos dos dados geográficos
SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
RODOVIAS_DIR = os.path.join("dados", "rodovias")

# Teto de NOVAS consultas à API por corrida (proteção de custo em testes).
# Use um número baixo (ex.: 10) para validar; troque para None quando estiver validado (sem limite).
LIMITE_NOVAS_CONSULTAS = 100

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Designação eletropostos", layout="wide")

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
for chave, valor in {
    'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
    'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
    'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


# ==========================================================
# Helpers
# ==========================================================
def _haversine_m(lat0, lon0, lats, lons):
    """Distância em metros de um ponto (lat0,lon0) a arrays de pontos."""
    R = 6371000.0
    p = np.pi / 180.0
    lats = np.asarray(lats, dtype=float)
    lons = np.asarray(lons, dtype=float)
    a = (np.sin((lats - lat0) * p / 2) ** 2
         + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def _construir_candidatos_rodovia(df_pois, centros, tamanho_grid_m=800, raio_ponto_m=800):
    """
    No modo rodovia, cada centro da corrente de círculos vira um candidato sobre a via
    (sem 'Snap to Road', pois já está na estrada). Mantém o mesmo esquema de colunas
    que o mapa e o simulador esperam: cell_i, cell_j, Lat_Centroide, Lng_Centroide,
    Qtd_POIs, Score_Estimado.
    """
    if not centros:
        return pd.DataFrame(), None

    lats = [c["lat"] for c in centros]
    lngs = [c["lng"] for c in centros]
    lat_ref = sum(lats) / len(lats)
    lat_step = tamanho_grid_m / 111320.0
    lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

    tem_pois = df_pois is not None and not df_pois.empty
    all_lat = lats + (list(df_pois["Lat"]) if tem_pois else [])
    all_lng = lngs + (list(df_pois["Lng"]) if tem_pois else [])
    lat_min, lng_min = min(all_lat), min(all_lng)

    if tem_pois:
        plat = df_pois["Lat"].to_numpy()
        plng = df_pois["Lng"].to_numpy()
        pw = df_pois["Peso"].to_numpy()
    else:
        plat = plng = pw = None

    linhas = []
    for c in centros:
        la, lo = c["lat"], c["lng"]
        if plat is not None and len(plat) > 0:
            d = _haversine_m(la, lo, plat, plng)
            m = d <= raio_ponto_m
            qtd = int(m.sum())
            score = float(pw[m].sum())
        else:
            qtd, score = 0, 0.0
        linhas.append({
            "cell_i": int((la - lat_min) / lat_step),
            "cell_j": int((lo - lng_min) / lng_step),
            "Lat_Centroide": la,
            "Lng_Centroide": lo,
            "Qtd_POIs": qtd,
            "Score_Estimado": score,
        })

    cand = pd.DataFrame(linhas)
    info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
    return cand, info_grid


def _coletar_urbano(cliente, cfg):
    df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
    eletropostos = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
    cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
    return df_pois, eletropostos, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"]


def _coletar_rodovia(cliente, cfg, status):
    if not cfg.get("rodovias_sel"):
        st.warning("Selecione ao menos uma rodovia.")
        return None
    if not os.path.exists(SP_POLY_PATH):
        st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
        return None

    poly = carregar_poligono_estado(SP_POLY_PATH)
    dfs, evs, centros_all = [], {}, []

    for rod in cfg["rodovias_sel"]:
        arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
        if not os.path.exists(arq):
            st.warning(f"Arquivo não encontrado: {arq}")
            continue
        comps, km = carregar_tracado(arq, rod["ref"], poly)
        centros, passo = gerar_cadeia_circulos(comps, cfg["raio"], cfg.get("fator", 1.0))
        status.write(f"{rod['ref']}: {km:.0f} km em SP, {len(centros)} círculos (passo {passo:.1f} km)")
        centros_all += centros

        for c in centros:
            df = cliente.buscar_pois(c["lat"], c["lng"], cfg["raio"], CATEGORIAS_POIS)
            if df is not None and not df.empty:
                dfs.append(df)
            for posto in cliente.buscar_eletropostos((c["lat"], c["lng"]), cfg["raio"]):
                loc = posto.get("location", {}) or {}
                chave = posto.get("id") or (loc.get("latitude"), loc.get("longitude"))
                evs[chave] = posto

    df_pois = (pd.concat(dfs, ignore_index=True).drop_duplicates(subset="place_id")
               if dfs else pd.DataFrame())
    eletropostos = list(evs.values())
    cand, grid = _construir_candidatos_rodovia(df_pois, centros_all, cfg["tamanho_grid"], cfg["tamanho_grid"])

    if centros_all:
        mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
        mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
    else:
        mlat, mlng = -22.81, -47.06
    # raio=0 evita desenhar um círculo de busca gigante no modo rodovia
    return df_pois, eletropostos, cand, grid, mlat, mlng, 0


# ==========================================================
# Sidebar
# ==========================================================
config = render_sidebar()

# ==========================================================
# Coleta e processamento
# ==========================================================
if config["btn_gerar"]:
    st.session_state.nodos_otimizados = []
    cliente = get_google_places_client()
    # Reinicia o contador e aplica o teto de novas consultas para esta corrida.
    cliente.iniciar_sessao_consultas(LIMITE_NOVAS_CONSULTAS)

    if config["modo"] == "Urbano (raio)":
        with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
            resultado = _coletar_urbano(cliente, config)
    else:
        with st.spinner("Varrendo rodovia(s) com a corrente de círculos..."):
            status = st.empty()
            resultado = _coletar_rodovia(cliente, config, status)

    if resultado:
        df_pois, eletr, cand, grid, mlat, mlng, mraio = resultado
        st.session_state.dados_pois = df_pois
        st.session_state.dados_eletropostos = eletr
        st.session_state.dados_candidatos = cand
        st.session_state.info_grid = grid
        st.session_state.map_lat = mlat
        st.session_state.map_lng = mlng
        st.session_state.map_raio = mraio
        st.session_state.analise_ativa = True

# ==========================================================
# Otimização (pré-processamento + CPLEX)
# ==========================================================
if config.get("btn_otimizar"):
    cand = st.session_state.dados_candidatos
    if st.session_state.analise_ativa and cand is not None and not cand.empty:
        with st.spinner("Otimizando rede..."):
            matriz_cplex, dados_cobertura = pré_computar_cenarios(
                st.session_state.dados_candidatos,
                st.session_state.dados_eletropostos or [],
                st.session_state.dados_pois,
                1500, 4, 800
            )
            resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, 0.85)
            if resultado and resultado["status"] == "Optimal":
                st.session_state.nodos_otimizados = resultado["nodos_selecionados"]
            else:
                st.error("Modelo inviável. Verifique o terminal.")
                st.session_state.nodos_otimizados = []
    else:
        st.warning("Gere a malha de candidatos primeiro.")

# ==========================================================
# Área principal (mapa em tela cheia)
# ==========================================================
if st.session_state.analise_ativa:
    if st.session_state.dados_pois is None or st.session_state.dados_pois.empty:
        st.warning("Nenhum POI encontrado.")
    else:
        renderizar_mapa_completo(
            lat=st.session_state.map_lat,
            lng=st.session_state.map_lng,
            raio=st.session_state.map_raio,
            df_pois=st.session_state.dados_pois,
            df_cand=st.session_state.dados_candidatos,
            grid=st.session_state.info_grid,
            dados_eletropostos=st.session_state.dados_eletropostos,
            categorias_pois=CATEGORIAS_POIS,
            nodos_otimizados=st.session_state.nodos_otimizados
        )
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")