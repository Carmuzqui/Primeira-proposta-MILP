# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# # Estimação de demanda gravitacional baseada em malha (Grid 200x200m) e mapa de Calor.
# # """

# # import streamlit as st
# # import requests
# # import pandas as pd
# # import folium
# # import math
# # from folium.plugins import HeatMap
# # from streamlit_folium import st_folium
# # from config.settings import GOOGLE_MAPS_API_KEY  # Importando a chave diretamente

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Geração de nodos candidatos EVCS", layout="wide")

# # # --- CATEGORIAS DE BUSCA (Google Places API Types) ---
# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe"],
# #         "color": "blue",
# #         "icon": "shopping-cart",
# #         "peso": 3.0  # Maior peso gravitacional (mais visitantes/tempo de permanência)
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

# # # --- FUNÇÕES MATEMÁTICAS E DE COLETA ---
# # # def buscar_pois(lat, lng, raio):
# # #     url = "https://places.googleapis.com/v1/places:searchNearby"
# # #     headers = {
# # #         'Content-Type': 'application/json',
# # #         'X-Goog-Api-Key': GOOGLE_MAPS_API_KEY,
# # #         'X-Goog-FieldMask': 'places.displayName,places.location,places.primaryType'
# # #     }
    
# # #     resultados_totais = []
    
# # #     for cat_nome, cat_data in CATEGORIAS_POIS.items():
# # #         payload = {
# # #             "locationRestriction": {
# # #                 "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": raio}
# # #             },
# # #             "includedTypes": cat_data["types"],
# # #             "maxResultCount": 20 
# # #         }
        
# # #         try:
# # #             response = requests.post(url, json=payload, headers=headers)
# # #             if response.status_code == 200:
# # #                 places = response.json().get('places', [])
# # #                 for p in places:
# # #                     if 'location' in p:
# # #                         resultados_totais.append({
# # #                             "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
# # #                             "Tipo": p.get('primaryType', 'Desconhecido'),
# # #                             "Categoria": cat_nome,
# # #                             "Lat": p['location']['latitude'],
# # #                             "Lng": p['location']['longitude'],
# # #                             "Peso": cat_data["peso"]
# # #                         })
# # #         except Exception as e:
# # #             st.error(f"Erro ao buscar {cat_nome}: {e}")
            
# # #     return pd.DataFrame(resultados_totais)



# # def buscar_pois(lat, lng, raio):
# #     url = "https://places.googleapis.com/v1/places:searchNearby"
# #     headers = {
# #         'Content-Type': 'application/json',
# #         'X-Goog-Api-Key': GOOGLE_MAPS_API_KEY,
# #         # Adicionado 'places.userRatingCount' na máscara de campos
# #         'X-Goog-FieldMask': 'places.displayName,places.location,places.primaryType,places.userRatingCount'
# #     }
    
# #     resultados_totais = []
    
# #     for cat_nome, cat_data in CATEGORIAS_POIS.items():
# #         payload = {
# #             "locationRestriction": {
# #                 "circle": {"center": {"latitude": lat, "longitude": lng}, "radius": raio}
# #             },
# #             "includedTypes": cat_data["types"],
# #             "maxResultCount": 20 
# #         }
        
# #         try:
# #             response = requests.post(url, json=payload, headers=headers)
# #             if response.status_code == 200:
# #                 places = response.json().get('places', [])
# #                 for p in places:
# #                     if 'location' in p:
# #                         # Extrai o número de avaliações (padrão 1 se não houver para evitar erros matemáticos)
# #                         avaliacoes = p.get('userRatingCount', 1)
                        
# #                         # CÁLCULO DO ÍNDICE COMPOSTO DE DEMANDA
# #                         # Usa log10 para suavizar outliers (ex: shoppings com 50.000 avaliações vs farmácias com 10)
# #                         # O peso da categoria simula o "Tempo de Permanência" (Dwell Time)
# #                         fator_volume = math.log10(avaliacoes + 10) # +10 evita log(1) = 0
# #                         peso_dinamico = cat_data["peso"] * fator_volume

# #                         resultados_totais.append({
# #                             "Nome": p.get('displayName', {}).get('text', 'Desconhecido'),
# #                             "Tipo": p.get('primaryType', 'Desconhecido'),
# #                             "Categoria": cat_nome,
# #                             "Lat": p['location']['latitude'],
# #                             "Lng": p['location']['longitude'],
# #                             "Avaliacoes_Reais": avaliacoes,
# #                             "Peso_Base": cat_data["peso"],
# #                             "Peso": peso_dinamico # Este é o valor que o HeatMap vai ler
# #                         })
# #         except Exception as e:
# #             st.error(f"Erro ao buscar {cat_nome}: {e}")
            
# #     return pd.DataFrame(resultados_totais)




# # def processar_grid_e_centroides(df_pois, lat_centro, lng_centro, raio_m, tamanho_grid_m=200):
# #     """
# #     Cria a grade virtual e calcula os centroides dos POIs para cada célula ativa.
# #     """
# #     if df_pois.empty:
# #         return pd.DataFrame(), None
        
# #     lat_step = tamanho_grid_m / 111320.0
# #     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_centro)))
    
# #     lat_min = lat_centro - (raio_m / 111320.0)
# #     lng_min = lng_centro - (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
    
# #     df_pois['cell_i'] = ((df_pois['Lat'] - lat_min) / lat_step).astype(int)
# #     df_pois['cell_j'] = ((df_pois['Lng'] - lng_min) / lng_step).astype(int)
    
# #     candidatos = df_pois.groupby(['cell_i', 'cell_j']).agg(
# #         Lat_Centroide=('Lat', 'mean'),
# #         Lng_Centroide=('Lng', 'mean'),
# #         Qtd_POIs=('Nome', 'count'),
# #         Score_Estimado=('Peso', 'sum')
# #     ).reset_index()
    
# #     info_grid = {
# #         'lat_min': lat_min, 'lng_min': lng_min,
# #         'lat_step': lat_step, 'lng_step': lng_step
# #     }
    
# #     return candidatos, info_grid

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # if 'dados_pois' not in st.session_state:
# #     st.session_state.dados_pois = None
# # if 'dados_candidatos' not in st.session_state:
# #     st.session_state.dados_candidatos = None
# # if 'info_grid' not in st.session_state:
# #     st.session_state.info_grid = None
# # if 'analise_ativa' not in st.session_state:
# #     st.session_state.analise_ativa = False

# # # --- SIDEBAR: CONTROLES ---
# # with st.sidebar:
# #     st.title("Análise de atratividade")
# #     st.markdown("Geração de malha e cálculo de demanda para nodos candidatos.")
# #     st.divider()
    
# #     st.header("Parâmetros espaciais")
# #     lat = st.number_input("Latitude inicial", value=-22.815313, format="%.6f")
# #     lng = st.number_input("Longitude inicial", value=-47.06914, format="%.6f")
    
# #     raio = st.slider("Raio de busca (metros)", min_value=500, max_value=10000, value=2000, step=500)
# #     tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=200, step=100)
        
# #     st.divider()
# #     if st.button("Gerar malha e candidatos", type="primary", use_container_width=True):
# #         with st.spinner("Mapeando POIs e calculando centroides..."):
# #             df_pois = buscar_pois(lat, lng, raio)
# #             st.session_state.dados_pois = df_pois
            
# #             candidatos, info_grid = processar_grid_e_centroides(df_pois, lat, lng, raio, tamanho_grid)
# #             st.session_state.dados_candidatos = candidatos
# #             st.session_state.info_grid = info_grid
            
# #             st.session_state.analise_ativa = True

# #     st.divider()
# #     # st.header("Visualização")
# #     # Novo controle para ativar/desativar o mapa de calor
# #     mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
    

# # # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# # if st.session_state.analise_ativa:
# #     df_pois = st.session_state.dados_pois
# #     df_cand = st.session_state.dados_candidatos
# #     grid = st.session_state.info_grid
    
# #     if df_pois.empty:
# #         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
# #     else:
# #         # Criação do Mapa Base
# #         mapa = folium.Map(location=[lat, lng], zoom_start=14, tiles='CartoDB positron')
        
# #         # --- CAMADA: MAPA DE CALOR (Opcional) ---
# #         if mostrar_heatmap:
# #             # Prepara os dados: [Latitude, Longitude, Peso (Intensidade)]
# #             heat_data = [[row['Lat'], row['Lng'], row['Peso']] for index, row in df_pois.iterrows()]
# #             HeatMap(
# #                 heat_data,
# #                 name="Demanda Gravitacional",
# #                 radius=25,
# #                 blur=15,
# #                 min_opacity=0.4,
# #                 gradient={0.2: 'blue', 0.6: 'lime', 1.0: 'red'} # Personalização de cores do calor
# #             ).add_to(mapa)

# #         # Limite de busca
# #         folium.Circle(
# #             [lat, lng],
# #             radius=raio,
# #             color='gray',
# #             fill=False,
# #             dash_array='5, 5',
# #             weight=2
# #         ).add_to(mapa)
        
# #         folium.CircleMarker(
# #             [lat, lng], radius=5, color='black', fill=True, popup="Centro da Busca"
# #         ).add_to(mapa)
        
# #         # --- CAMADA: GRADE E CENTROIDES ---
# #         for _, row in df_cand.iterrows():
# #             i, j = row['cell_i'], row['cell_j']
# #             c_lat_min = grid['lat_min'] + (i * grid['lat_step'])
# #             c_lat_max = c_lat_min + grid['lat_step']
# #             c_lng_min = grid['lng_min'] + (j * grid['lng_step'])
# #             c_lng_max = c_lng_min + grid['lng_step']
            
# #             # Polígono da célula
# #             folium.Rectangle(
# #                 bounds=[[c_lat_min, c_lng_min], [c_lat_max, c_lng_max]],
# #                 color='blue',
# #                 weight=1,
# #                 fill=True,
# #                 fillColor='blue',
# #                 fillOpacity=0.05
# #             ).add_to(mapa)
            
# #             # Nodo Candidato
# #             folium.Marker(
# #                 [row['Lat_Centroide'], row['Lng_Centroide']],
# #                 popup=f"<b>CANDIDATO EVCS</b><br>POIs na área: {row['Qtd_POIs']}<br>Score base: {row['Score_Estimado']:.1f}",
# #                 tooltip="Nodo candidato otimizado",
# #                 icon=folium.Icon(color='black', icon='wrench', prefix='fa')
# #             ).add_to(mapa)

# #         # --- CAMADA: POIs ORIGINAIS ---
# #         for _, row in df_pois.iterrows():
# #             cat_info = CATEGORIAS_POIS[row['Categoria']]
# #             folium.CircleMarker(
# #                 [row['Lat'], row['Lng']],
# #                 radius=4,
# #                 color=cat_info['color'],
# #                 fill=True,
# #                 fillOpacity=0.8,
# #                 tooltip=f"{row['Nome']} ({row['Tipo']}) - Peso: {row['Peso']}"
# #             ).add_to(mapa)

# #         # --- LEGENDA ---
# #         legend_html = f'''
# #          <div style="position: fixed; 
# #                      bottom: 30px; right: 30px; width: 220px; height: 210px; 
# #                      border:2px solid grey; z-index:9999; font-size:13px;
# #                      background-color:white; opacity: 0.95; padding: 10px;
# #                      border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
# #              <b>Convenções do mapa</b><br>
# #              <i class="fa fa-circle" style="color:blue;"></i> Varejo e lazer<br>
# #              <i class="fa fa-circle" style="color:red;"></i> Transporte<br>
# #              <i class="fa fa-circle" style="color:purple;"></i> Serviços e saúde<br>
# #              <hr style="margin: 5px 0;">
# #              <div style="width:12px; height:12px; background-color:lightblue; display:inline-block; border:1px solid blue;"></div> Área de cobertura<br>
# #              <i class="fa fa-wrench fa-1x" style="color:black;"></i> Nodo candidato (centroide)<br>
# #              {"<hr style='margin: 5px 0;'><span style='background: linear-gradient(to right, blue, lime, red); width: 100%; height: 10px; display: block;'></span> Densidade de demanda" if mostrar_heatmap else ""}
# #          </div>
# #          '''
# #         mapa.get_root().html.add_child(folium.Element(legend_html))
            
# #         st_folium(mapa, use_container_width=True, height=850, returned_objects=[])

# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")










# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos
# Estimação de demanda gravitacional baseada em malha (Grid 200x200m) e Eletropostos.
# """

# import streamlit as st
# import pandas as pd
# import folium
# import math
# from folium.plugins import HeatMap
# from streamlit_folium import st_folium

# # Importando o novo cliente unificado da API
# from api.google_places import get_google_places_client

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Geração de nodos candidatos EVCS", layout="wide")

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

# # --- FUNÇÕES MATEMÁTICAS ---
# def processar_grid_e_centroides(df_pois, lat_centro, lng_centro, raio_m, tamanho_grid_m=200):
#     if df_pois.empty:
#         return pd.DataFrame(), None
        
#     lat_step = tamanho_grid_m / 111320.0
#     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_centro)))
    
#     lat_min = lat_centro - (raio_m / 111320.0)
#     lng_min = lng_centro - (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
    
#     df_pois['cell_i'] = ((df_pois['Lat'] - lat_min) / lat_step).astype(int)
#     df_pois['cell_j'] = ((df_pois['Lng'] - lng_min) / lng_step).astype(int)
    
#     candidatos = df_pois.groupby(['cell_i', 'cell_j']).agg(
#         Lat_Centroide=('Lat', 'mean'),
#         Lng_Centroide=('Lng', 'mean'),
#         Qtd_POIs=('Nome', 'count'),
#         Score_Estimado=('Peso', 'sum')
#     ).reset_index()
    
#     info_grid = {
#         'lat_min': lat_min, 'lng_min': lng_min,
#         'lat_step': lat_step, 'lng_step': lng_step
#     }
    
#     return candidatos, info_grid

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

# # --- SIDEBAR: CONTROLES ---
# with st.sidebar:
#     st.title("Análise de atratividade")
#     st.markdown("Geração de malha e cálculo de demanda para nodos candidatos.")
#     st.divider()
    
#     st.header("Parâmetros espaciais")
#     lat = st.number_input("Latitude inicial", value=-22.815313, format="%.6f")
#     lng = st.number_input("Longitude inicial", value=-47.06914, format="%.6f")
    
#     raio = st.slider("Raio de busca (metros)", min_value=500, max_value=10000, value=2000, step=500)
#     tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=200, step=100)
        
#     st.divider()
#     if st.button("Gerar malha e candidatos", type="primary", use_container_width=True):
#         with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
#             cliente_api = get_google_places_client()
            
#             # 1. Busca POIs
#             df_pois = cliente_api.buscar_pois(lat, lng, raio, CATEGORIAS_POIS)
#             st.session_state.dados_pois = df_pois
            
#             # 2. Busca Eletropostos
#             eletropostos = cliente_api.buscar_eletropostos((lat, lng), raio)
#             st.session_state.dados_eletropostos = eletropostos
            
#             # 3. Processa Malha Matemática
#             candidatos, info_grid = processar_grid_e_centroides(df_pois, lat, lng, raio, tamanho_grid)
#             st.session_state.dados_candidatos = candidatos
#             st.session_state.info_grid = info_grid
            
#             st.session_state.analise_ativa = True

#     st.divider()
#     mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
#     mostrar_eletropostos = st.toggle("Mostrar eletropostos (concorrência)", value=False, help="Exibe a infraestrutura de recarga já existente na área.")

# # --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
# if st.session_state.analise_ativa:
#     df_pois = st.session_state.dados_pois
#     df_cand = st.session_state.dados_candidatos
#     grid = st.session_state.info_grid
    
#     if df_pois.empty:
#         st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
#     else:
#         mapa = folium.Map(location=[lat, lng], zoom_start=14, tiles='CartoDB positron')
        
#         # --- CAMADA: MAPA DE CALOR (Demanda) ---
#         if mostrar_heatmap:
#             heat_data = [[row['Lat'], row['Lng'], row['Peso']] for index, row in df_pois.iterrows()]
#             HeatMap(
#                 heat_data,
#                 name="Demanda Gravitacional",
#                 radius=25, blur=15, min_opacity=0.4,
#                 gradient={0.2: 'blue', 0.6: 'lime', 1.0: 'red'} 
#             ).add_to(mapa)

#         # Limite de busca e Centro
#         folium.Circle([lat, lng], radius=raio, color='gray', fill=False, dash_array='5, 5', weight=2).add_to(mapa)
#         folium.CircleMarker([lat, lng], radius=5, color='black', fill=True, popup="Centro da Busca").add_to(mapa)
        
#         # --- CAMADA: GRADE E CENTROIDES ---
#         for _, row in df_cand.iterrows():
#             i, j = row['cell_i'], row['cell_j']
#             c_lat_min = grid['lat_min'] + (i * grid['lat_step'])
#             c_lat_max = c_lat_min + grid['lat_step']
#             c_lng_min = grid['lng_min'] + (j * grid['lng_step'])
#             c_lng_max = c_lng_min + grid['lng_step']
            
#             folium.Rectangle(
#                 bounds=[[c_lat_min, c_lng_min], [c_lat_max, c_lng_max]],
#                 color='blue', weight=1, fill=True, fillColor='blue', fillOpacity=0.05
#             ).add_to(mapa)
            
#             folium.Marker(
#                 [row['Lat_Centroide'], row['Lng_Centroide']],
#                 popup=f"<b>CANDIDATO EVCS</b><br>POIs na área: {row['Qtd_POIs']}<br>Score base: {row['Score_Estimado']:.1f}",
#                 tooltip="Nodo candidato otimizado",
#                 icon=folium.Icon(color='black', icon='wrench', prefix='fa')
#             ).add_to(mapa)

#         # --- CAMADA: POIs ORIGINAIS ---
#         for _, row in df_pois.iterrows():
#             cat_info = CATEGORIAS_POIS[row['Categoria']]
#             folium.CircleMarker(
#                 [row['Lat'], row['Lng']],
#                 radius=4, # Tamanho original dos POIs
#                 color=cat_info['color'], fill=True, fillOpacity=0.8,
#                 tooltip=f"{row['Nome']} ({row['Tipo']}) - Peso: {row['Peso']:.1f}"
#             ).add_to(mapa)

#         # --- CAMADA: ELETEROPOSTOS (Concorrência) ---
#         if mostrar_eletropostos and st.session_state.dados_eletropostos:
#             for posto in st.session_state.dados_eletropostos:
#                 if 'location' in posto:
#                     p_lat = posto['location']['latitude']
#                     p_lng = posto['location']['longitude']
#                     nome = posto.get('displayName', {}).get('text', 'Eletroposto')
#                     endereco = posto.get('formattedAddress', 'Endereço não disponível')
#                     distancia = posto.get('distancia_centro_m', 0) / 1000 
                    
#                     rating = posto.get('rating', 'N/A')
#                     user_ratings = posto.get('userRatingCount', 0)
#                     telefone = posto.get('nationalPhoneNumber', 'N/A')
#                     website = posto.get('websiteUri', '#')
                    
#                     ev_info = ""
#                     ev_options = posto.get('evChargeOptions', {})
#                     conector_total = ev_options.get('connectorCount', 0)
                    
#                     if conector_total > 0:
#                         ev_info += f"<p style='margin: 5px 0; font-size: 12px;'><b>🔌 Conectores ({conector_total}):</b><br>"
#                         for conn in ev_options.get('connectorAggregation', []):
#                             tipo = conn.get('type', 'Desconhecido').replace('EV_CONNECTOR_TYPE_', '')
#                             count = conn.get('count', 0)
#                             kw = conn.get('maxChargeRateKw', 'N/A')
#                             ev_info += f"- {count}x {tipo} (Max: {kw}kW)<br>"
#                         ev_info += "</p>"
#                     else:
#                         ev_info += "<p style='margin: 5px 0; font-size: 12px; color: #d32f2f;'>Sem detalhes de conectores.</p>"

#                     estrelas = f"⭐ {rating} ({user_ratings} avaliações)" if rating != 'N/A' else "Sem avaliações"

#                     popup_html = f"""
#                     <div style="font-family: Arial, sans-serif; width: 280px;">
#                         <h4 style="margin: 0 0 8px 0; color: #2e7d32; border-bottom: 1px solid #ccc; padding-bottom: 5px;">{nome}</h4>
#                         <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: bold; color: #e65100;">{estrelas}</p>
#                         <p style="margin: 5px 0; font-size: 12px;"><b>📍 Endereço:</b><br>{endereco}</p>                
#                         <p style="margin: 5px 0; font-size: 12px;"><b>📞 Contato:</b> {telefone}</p>
#                         <div style="background-color: #e8f5e9; padding: 8px; border-radius: 5px; margin: 10px 0;">{ev_info}</div>
#                         <p style="margin: 5px 0; font-size: 12px; color: #d84315;"><b>Distância do centro:</b> {distancia:.2f} km</p>
#                         <div style="display: flex; justify-content: space-between; align-items: center;">
#                             <span style="font-size: 10px; color: #666;">{p_lat:.5f}, {p_lng:.5f}</span>
#                             <a href="{website}" target="_blank" style="font-size: 12px; color: #fff; background-color: #2e7d32; padding: 4px 8px; text-decoration: none; border-radius: 4px;">Web</a>
#                         </div>
#                     </div>
#                     """
                    
#                     folium.CircleMarker(
#                         [p_lat, p_lng],
#                         radius=7, # Ligeiramente maior que os POIs (4)
#                         color='green', fill=True, fillColor='green', fillOpacity=0.9,
#                         popup=folium.Popup(popup_html, max_width=300),
#                         tooltip=f"⚡ {nome}"
#                     ).add_to(mapa)

#         # --- LEGENDA ---
#         legend_html = f'''
#          <div style="position: fixed; 
#                      bottom: 30px; right: 30px; width: 230px; height: 230px; 
#                      border:2px solid grey; z-index:9999; font-size:13px;
#                      background-color:white; opacity: 0.95; padding: 10px;
#                      border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
#              <b>Convenções do mapa</b><br>
#              <i class="fa fa-circle" style="color:blue;"></i> Varejo e lazer<br>
#              <i class="fa fa-circle" style="color:red;"></i> Transporte<br>
#              <i class="fa fa-circle" style="color:purple;"></i> Serviços e saúde<br>
#              <i class="fa fa-circle" style="color:green; font-size: 16px;"></i> Eletroposto (Concorrência)<br>
#              <hr style="margin: 5px 0;">
#              <div style="width:12px; height:12px; background-color:lightblue; display:inline-block; border:1px solid blue;"></div> Área de cobertura<br>
#              <i class="fa fa-wrench fa-1x" style="color:black;"></i> Nodo candidato (centroide)<br>
#              {"<hr style='margin: 5px 0;'><span style='background: linear-gradient(to right, blue, lime, red); width: 100%; height: 10px; display: block;'></span> Densidade de demanda" if mostrar_heatmap else ""}
#          </div>
#          '''
#         mapa.get_root().html.add_child(folium.Element(legend_html))
            
#         st_folium(mapa, use_container_width=True, height=850, returned_objects=[])

# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")










"""
Dashboard exploratório: análise de geradores de viagem (POIs) e geração de nodos candidatos
Estimação de demanda gravitacional baseada em malha (Grid 200x200m) e eletropostos.
"""

import streamlit as st
import pandas as pd
import folium
import math
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Importando o novo cliente unificado da API
from api.google_places import get_google_places_client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Designação eletropostos", layout="wide")

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

# --- FUNÇÕES MATEMÁTICAS ---
def processar_grid_e_centroides(df_pois, lat_centro, lng_centro, raio_m, tamanho_grid_m=800):
    if df_pois.empty:
        return pd.DataFrame(), None
        
    lat_step = tamanho_grid_m / 111320.0
    lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_centro)))
    
    lat_min = lat_centro - (raio_m / 111320.0)
    lng_min = lng_centro - (raio_m / (111320.0 * math.cos(math.radians(lat_centro))))
    
    df_pois['cell_i'] = ((df_pois['Lat'] - lat_min) / lat_step).astype(int)
    df_pois['cell_j'] = ((df_pois['Lng'] - lng_min) / lng_step).astype(int)
    
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

# --- SIDEBAR: CONTROLES ---
with st.sidebar:
    # st.title("Análise de atratividade")
    # st.markdown("Geração de malha e cálculo de demanda para nodos candidatos.")
    # st.divider()
    
    st.header("Parâmetros espaciais")
    lat = st.number_input("Latitude inicial", value=-22.815313, format="%.6f")
    lng = st.number_input("Longitude inicial", value=-47.06914, format="%.6f")
    
    raio = st.slider("Raio de busca (metros)", min_value=500, max_value=10000, value=2000, step=500)
    tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)
        
    st.divider()
    if st.button("Gerar malha e candidatos", type="primary", use_container_width=True):
        with st.spinner("Mapeando POIs, concorrência e calculando centroides..."):
            cliente_api = get_google_places_client()
            
            # 1. Busca POIs
            df_pois = cliente_api.buscar_pois(lat, lng, raio, CATEGORIAS_POIS)
            st.session_state.dados_pois = df_pois
            
            # 2. Busca Eletropostos
            eletropostos = cliente_api.buscar_eletropostos((lat, lng), raio)
            st.session_state.dados_eletropostos = eletropostos
            
            # 3. Processa Malha Matemática
            candidatos, info_grid = processar_grid_e_centroides(df_pois, lat, lng, raio, tamanho_grid)
            st.session_state.dados_candidatos = candidatos
            st.session_state.info_grid = info_grid
            
            st.session_state.analise_ativa = True

    st.divider()
    mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
    mostrar_eletropostos = st.toggle("Mostrar eletropostos (concorrência)", value=False, help="Exibe a infraestrutura de recarga já existente na área.")

# --- ÁREA PRINCIPAL (MAPA EM TELA CHEIA) ---
if st.session_state.analise_ativa:
    df_pois = st.session_state.dados_pois
    df_cand = st.session_state.dados_candidatos
    grid = st.session_state.info_grid
    
    if df_pois.empty:
        st.warning("Nenhum POI encontrado nesse raio. Tente aumentar a área de busca.")
    else:
        mapa = folium.Map(location=[lat, lng], zoom_start=14, tiles='CartoDB positron')
        
        # --- CAMADA: MAPA DE CALOR (Demanda) ---
        if mostrar_heatmap:
            heat_data = [[row['Lat'], row['Lng'], row['Peso']] for index, row in df_pois.iterrows()]
            HeatMap(
                heat_data,
                name="Demanda Gravitacional",
                radius=25, blur=15, min_opacity=0.4,
                gradient={0.2: 'blue', 0.6: 'lime', 1.0: 'red'} 
            ).add_to(mapa)

        # Limite de busca e Centro
        folium.Circle([lat, lng], radius=raio, color='gray', fill=False, dash_array='5, 5', weight=2).add_to(mapa)
        folium.CircleMarker([lat, lng], radius=5, color='black', fill=True, popup="Centro da Busca").add_to(mapa)
        
        # --- CAMADA: GRADE E CENTROIDES ---
        for _, row in df_cand.iterrows():
            i, j = row['cell_i'], row['cell_j']
            c_lat_min = grid['lat_min'] + (i * grid['lat_step'])
            c_lat_max = c_lat_min + grid['lat_step']
            c_lng_min = grid['lng_min'] + (j * grid['lng_step'])
            c_lng_max = c_lng_min + grid['lng_step']
            
            folium.Rectangle(
                bounds=[[c_lat_min, c_lng_min], [c_lat_max, c_lng_max]],
                color='blue', weight=1, fill=True, fillColor='blue', fillOpacity=0.05
            ).add_to(mapa)
            
            folium.Marker(
                [row['Lat_Centroide'], row['Lng_Centroide']],
                popup=f"<b>CANDIDATO EVCS</b><br>POIs na área: {row['Qtd_POIs']}<br>Score base: {row['Score_Estimado']:.1f}",
                tooltip="Nodo candidato otimizado",
                icon=folium.Icon(color='black', icon='wrench', prefix='fa')
            ).add_to(mapa)

        # --- CAMADA: POIs ORIGINAIS ---
        for _, row in df_pois.iterrows():
            cat_info = CATEGORIAS_POIS[row['Categoria']]
            folium.CircleMarker(
                [row['Lat'], row['Lng']],
                radius=4, # Tamanho original dos POIs
                color=cat_info['color'], fill=True, fillOpacity=0.8,
                tooltip=f"{row['Nome']} ({row['Tipo']}) - Peso: {row['Peso']:.1f}"
            ).add_to(mapa)

        # --- CAMADA: ELETEROPOSTOS (Concorrência) ---
        if mostrar_eletropostos and st.session_state.dados_eletropostos:
            for posto in st.session_state.dados_eletropostos:
                if 'location' in posto:
                    p_lat = posto['location']['latitude']
                    p_lng = posto['location']['longitude']
                    nome = posto.get('displayName', {}).get('text', 'Eletroposto')
                    endereco = posto.get('formattedAddress', 'Endereço não disponível')
                    distancia = posto.get('distancia_centro_m', 0) / 1000 
                    
                    rating = posto.get('rating', 'N/A')
                    user_ratings = posto.get('userRatingCount', 0)
                    telefone = posto.get('nationalPhoneNumber', 'N/A')
                    website = posto.get('websiteUri', '#')
                    
                    ev_info = ""
                    ev_options = posto.get('evChargeOptions', {})
                    conector_total = ev_options.get('connectorCount', 0)
                    
                    if conector_total > 0:
                        ev_info += f"<p style='margin: 5px 0; font-size: 12px;'><b>🔌 Conectores ({conector_total}):</b><br>"
                        for conn in ev_options.get('connectorAggregation', []):
                            tipo = conn.get('type', 'Desconhecido').replace('EV_CONNECTOR_TYPE_', '')
                            count = conn.get('count', 0)
                            kw = conn.get('maxChargeRateKw', 'N/A')
                            ev_info += f"- {count}x {tipo} (Max: {kw}kW)<br>"
                        ev_info += "</p>"
                    else:
                        ev_info += "<p style='margin: 5px 0; font-size: 12px; color: #d32f2f;'>Sem detalhes de conectores.</p>"

                    estrelas = f"⭐ {rating} ({user_ratings} avaliações)" if rating != 'N/A' else "Sem avaliações"

                    popup_html = f"""
                    <div style="font-family: Arial, sans-serif; width: 280px;">
                        <h4 style="margin: 0 0 8px 0; color: #2e7d32; border-bottom: 1px solid #ccc; padding-bottom: 5px;">{nome}</h4>
                        <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: bold; color: #e65100;">{estrelas}</p>
                        <p style="margin: 5px 0; font-size: 12px;"><b>📍 Endereço:</b><br>{endereco}</p>                
                        <p style="margin: 5px 0; font-size: 12px;"><b>📞 Contato:</b> {telefone}</p>
                        <div style="background-color: #e8f5e9; padding: 8px; border-radius: 5px; margin: 10px 0;">{ev_info}</div>
                        <p style="margin: 5px 0; font-size: 12px; color: #d84315;"><b>Distância do centro:</b> {distancia:.2f} km</p>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 10px; color: #666;">{p_lat:.5f}, {p_lng:.5f}</span>
                            <a href="{website}" target="_blank" style="font-size: 12px; color: #fff; background-color: #2e7d32; padding: 4px 8px; text-decoration: none; border-radius: 4px;">Web</a>
                        </div>
                    </div>
                    """
                    
                    folium.CircleMarker(
                        [p_lat, p_lng],
                        radius=7, # Ligeiramente maior que os POIs (4)
                        color='green', fill=True, fillColor='green', fillOpacity=0.9,
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"⚡ {nome}"
                    ).add_to(mapa)

        # --- LEGENDA DINÂMICA ---
        legend_html = f'''
         <div style="position: fixed; 
                     bottom: 30px; right: 30px; width: 230px; height: auto; 
                     border:2px solid grey; z-index:9999; font-size:13px;
                     background-color:white; opacity: 0.95; padding: 10px;
                     border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
             <b>Convenções do mapa</b><br>
             <i class="fa fa-circle" style="color:blue;"></i> Varejo e lazer<br>
             <i class="fa fa-circle" style="color:red;"></i> Transporte<br>
             <i class="fa fa-circle" style="color:purple;"></i> Serviços e saúde<br>
             {"<i class='fa fa-circle' style='color:green; font-size: 16px;'></i> Eletroposto (Concorrência)<br>" if mostrar_eletropostos else ""}
             <hr style="margin: 5px 0;">
             <div style="width:12px; height:12px; background-color:lightblue; display:inline-block; border:1px solid blue;"></div> Área de cobertura<br>
             <i class="fa fa-wrench fa-1x" style="color:black;"></i> Nodo candidato (centroide)<br>
             {"<hr style='margin: 5px 0;'><span style='background: linear-gradient(to right, blue, lime, red); width: 100%; height: 10px; display: block;'></span> Densidade de demanda" if mostrar_heatmap else ""}
         </div>
         '''
        mapa.get_root().html.add_child(folium.Element(legend_html))
            
        st_folium(mapa, use_container_width=True, height=850, returned_objects=[])

else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")







