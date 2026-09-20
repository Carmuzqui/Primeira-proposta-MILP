# # """
# # Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
# # Dois modos de varredura com a mesma lógica de busca:
# #   - Urbano (raio): círculo em torno de um ponto.
# #   - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
# # Ambos calculam o Potencial de Implantação (IP) normalizado em [1,5] e filtram por um corte.
# # """

# # import os
# # import math
# # import numpy as np
# # import pandas as pd
# # import streamlit as st
# # from scipy.spatial import cKDTree

# # from api.google_places import get_google_places_client
# # from components.sidebar import render_sidebar
# # from components.mapa import renderizar_mapa_completo
# # from utils.geo_math import processar_grid_e_centroides
# # from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
# # from utils.potencial import (carregar_sensores, carregar_municipios,
# #                              calcular_potencial, filtrar_por_potencial)
# # from modelo.simulador import pré_computar_cenarios
# # from modelo.otimizador import resolver_modelo_cplex

# # # Caminhos dos dados
# # SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
# # RODOVIAS_DIR = os.path.join("dados", "rodovias")
# # SENSORES_DIR = os.path.join("dados", "sensores")
# # MUNICIPIOS_PATH = os.path.join("dados", "municipios", "municipios_sp.json")

# # # Teto de NOVAS consultas à API por corrida (proteção de custo). None = sem limite.
# # LIMITE_NOVAS_CONSULTAS = 100
# # # Corte do potencial: candidatos com score_potencial >= CORTE_POTENCIAL passam ao modelo.
# # CORTE_POTENCIAL = 2.5
# # # No modo rodovia, POIs candidatos devem estar até esta distância do traçado (metros).
# # DIST_VIA_M = 300
# # # Categoria de POI usada como candidato no modo rodovia (paradas: hotéis, restaurantes, mercados...).
# # CANDIDATO_CATEGORIA = "Varejo e lazer"

# # # --- CONFIGURAÇÃO DA PÁGINA ---
# # st.set_page_config(page_title="Designação eletropostos", layout="wide")

# # st.markdown("""
# #     <style>
# #     .main .block-container { padding: 0.5rem 0.5rem 0rem 0.5rem; max-width: 100%; }
# #     iframe { width: 100%; height: 90vh; }
# #     </style>
# # """, unsafe_allow_html=True)

# # CATEGORIAS_POIS = {
# #     "Varejo e lazer": {
# #         "types": ["shopping_mall", "supermarket", "restaurant", "cafe", "lodging"],
# #         "color": "blue", "icon": "shopping-cart", "peso": 3.0
# #     },
# #     "Transporte": {
# #         "types": ["bus_station", "subway_station", "transit_station"],
# #         "color": "red", "icon": "bus", "peso": 2.0
# #     },
# #     "Serviços e saúde": {
# #         "types": ["hospital", "bank", "university"],
# #         "color": "purple", "icon": "heart", "peso": 1.5
# #     }
# # }

# # # --- INICIALIZAR ESTADO DA SESSÃO ---
# # for chave, valor in {
# #     'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
# #     'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
# #     'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
# #     'cadeia': None, 'raio_circulo': None,
# # }.items():
# #     if chave not in st.session_state:
# #         st.session_state[chave] = valor


# # # ==========================================================
# # # Dados do PI (sensores e municípios), carregados uma vez
# # # ==========================================================
# # @st.cache_resource
# # def _carregar_dados_pi():
# #     sens = carregar_sensores(SENSORES_DIR) if os.path.isdir(SENSORES_DIR) else pd.DataFrame()
# #     muni = carregar_municipios(MUNICIPIOS_PATH) if os.path.exists(MUNICIPIOS_PATH) else pd.DataFrame()
# #     return sens, muni


# # # ==========================================================
# # # Helpers
# # # ==========================================================
# # def _haversine_m(lat0, lon0, lats, lons):
# #     R = 6371000.0
# #     p = np.pi / 180.0
# #     lats = np.asarray(lats, dtype=float); lons = np.asarray(lons, dtype=float)
# #     a = (np.sin((lats - lat0) * p / 2) ** 2
# #          + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
# #     return 2 * R * np.arcsin(np.sqrt(a))


# # def _pois_proximos_tracado(df, comps, dist_m=DIST_VIA_M):
# #     """Retorna uma máscara booleana dos POIs de df que estão a até dist_m do traçado."""
# #     if df is None or df.empty or not comps:
# #         return pd.Series([False] * (0 if df is None else len(df)), index=(None if df is None else df.index))
# #     rpts = []
# #     for ln in comps:
# #         rpts += list(ln.coords)  # (lon, lat)
# #     rpts = np.asarray(rpts, float)
# #     lat0 = float(np.mean(rpts[:, 1]))
# #     kx = 111320.0 * math.cos(math.radians(lat0))
# #     ky = 111320.0
# #     road_xy = np.column_stack([rpts[:, 0] * kx, rpts[:, 1] * ky])
# #     tree = cKDTree(road_xy)
# #     poi_xy = np.column_stack([df["Lng"].to_numpy() * kx, df["Lat"].to_numpy() * ky])
# #     dist, _ = tree.query(poi_xy)
# #     return pd.Series(dist <= dist_m, index=df.index)


# # def _candidatos_de_pois(df_cand_pois, df_pois_todos, tamanho_grid_m=800, raio_ponto_m=800):
# #     """Constrói candidatos a partir de POIs (modo rodovia), no esquema esperado pelo mapa/simulador."""
# #     if df_cand_pois is None or df_cand_pois.empty:
# #         return pd.DataFrame(), None
# #     lats = df_cand_pois["Lat"].to_numpy(); lngs = df_cand_pois["Lng"].to_numpy()
# #     lat_ref = float(np.mean(lats))
# #     lat_step = tamanho_grid_m / 111320.0
# #     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

# #     tem = df_pois_todos is not None and not df_pois_todos.empty
# #     base_lat = list(df_pois_todos["Lat"]) if tem else list(lats)
# #     base_lng = list(df_pois_todos["Lng"]) if tem else list(lngs)
# #     lat_min = min(float(lats.min()), min(base_lat))
# #     lng_min = min(float(lngs.min()), min(base_lng))

# #     plat = df_pois_todos["Lat"].to_numpy() if tem else lats
# #     plng = df_pois_todos["Lng"].to_numpy() if tem else lngs

# #     linhas = []
# #     for la, lo in zip(lats, lngs):
# #         d = _haversine_m(la, lo, plat, plng)
# #         qtd = int((d <= raio_ponto_m).sum())
# #         linhas.append({
# #             "cell_i": int((la - lat_min) / lat_step),
# #             "cell_j": int((lo - lng_min) / lng_step),
# #             "Lat_Centroide": float(la), "Lng_Centroide": float(lo),
# #             "Qtd_POIs": qtd, "Score_Estimado": 0.0,
# #         })
# #     cand = pd.DataFrame(linhas)
# #     info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
# #     return cand, info_grid


# # # ==========================================================
# # # Coletores
# # # ==========================================================
# # def _coletar_urbano(cliente, cfg, sens, muni):
# #     df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
# #     eletr = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
# #     cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
# #     # Potencial (urbano: só critérios de POIs + vizinhos) e corte
# #     cand = calcular_potencial(cand, df_pois, eletr, modo="urbano")
# #     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)
# #     return df_pois, eletr, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"], None, None


# # def _coletar_rodovia(cliente, cfg, status, sens, muni):
# #     if not cfg.get("rodovias_sel"):
# #         st.warning("Selecione ao menos uma rodovia.")
# #         return None
# #     if not os.path.exists(SP_POLY_PATH):
# #         st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
# #         return None

# #     poly = carregar_poligono_estado(SP_POLY_PATH)
# #     dfs, evs, centros_all, comps_all = [], {}, [], []

# #     for rod in cfg["rodovias_sel"]:
# #         arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
# #         if not os.path.exists(arq):
# #             st.warning(f"Arquivo não encontrado: {arq}")
# #             continue
# #         comps, km = carregar_tracado(arq, rod["ref"], poly)
# #         comps_all += comps
# #         centros, passo = gerar_cadeia_circulos(comps, cfg["raio"], cfg.get("fator", 1.0))
# #         status.write(f"{rod['ref']}: {km:.0f} km em SP, {len(centros)} círculos (passo {passo:.1f} km)")
# #         centros_all += centros

# #         for c in centros:
# #             df = cliente.buscar_pois(c["lat"], c["lng"], cfg["raio"], CATEGORIAS_POIS)
# #             if df is not None and not df.empty:
# #                 dfs.append(df)
# #             for posto in cliente.buscar_eletropostos((c["lat"], c["lng"]), cfg["raio"]):
# #                 loc = posto.get("location", {}) or {}
# #                 chave = posto.get("id") or (loc.get("latitude"), loc.get("longitude"))
# #                 evs[chave] = posto

# #     df_pois = (pd.concat(dfs, ignore_index=True).drop_duplicates(subset="place_id")
# #                if dfs else pd.DataFrame())
# #     eletr = list(evs.values())

# #     # Candidatos = POIs geradores de parada (Varejo e lazer) SOBRE a via (<= DIST_VIA_M do traçado)
# #     if not df_pois.empty:
# #         df_par = df_pois[df_pois["Categoria"] == CANDIDATO_CATEGORIA]
# #         if not df_par.empty:
# #             mask = _pois_proximos_tracado(df_par, comps_all, DIST_VIA_M)
# #             df_par = df_par[mask]
# #     else:
# #         df_par = df_pois
# #     cand, grid = _candidatos_de_pois(df_par, df_pois, cfg["tamanho_grid"])

# #     # Potencial (rodovia: IP completo x1..x4) e corte
# #     cand = calcular_potencial(cand, df_pois, eletr, sens, muni, modo="rodovia")
# #     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)

# #     # Funil de candidatos (transparência do diagnóstico)
# #     n_pois = 0 if df_pois is None or df_pois.empty else len(df_pois)
# #     n_varejo = 0 if df_pois is None or df_pois.empty else int((df_pois['Categoria'] == CANDIDATO_CATEGORIA).sum())
# #     n_via = 0 if df_par is None or df_par.empty else len(df_par)
# #     n_corte = 0 if cand is None or cand.empty else len(cand)
# #     st.info(f"Funil rodovia: POIs {n_pois} | Varejo {n_varejo} | sobre a via (<= {DIST_VIA_M} m) {n_via} | apos corte {CORTE_POTENCIAL}: {n_corte}")

# #     if centros_all:
# #         mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
# #         mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
# #     else:
# #         mlat, mlng = -22.81, -47.06
# #     return df_pois, eletr, cand, grid, mlat, mlng, 0, centros_all, cfg["raio"]


# # # ==========================================================
# # # Sidebar
# # # ==========================================================
# # config = render_sidebar()

# # # ==========================================================
# # # Coleta e processamento
# # # ==========================================================
# # if config["btn_gerar"]:
# #     st.session_state.nodos_otimizados = []
# #     cliente = get_google_places_client()
# #     cliente.iniciar_sessao_consultas(LIMITE_NOVAS_CONSULTAS)
# #     sens, muni = _carregar_dados_pi()

# #     if config["modo"] == "Urbano (raio)":
# #         with st.spinner("Mapeando POIs e calculando potencial..."):
# #             resultado = _coletar_urbano(cliente, config, sens, muni)
# #     else:
# #         with st.spinner("Varrendo rodovia(s) e calculando potencial..."):
# #             status = st.empty()
# #             resultado = _coletar_rodovia(cliente, config, status, sens, muni)

# #     if resultado:
# #         df_pois, eletr, cand, grid, mlat, mlng, mraio, cadeia, raio_circulo = resultado
# #         n_cand = 0 if cand is None or cand.empty else len(cand)
# #         st.session_state.dados_pois = df_pois
# #         st.session_state.dados_eletropostos = eletr
# #         st.session_state.dados_candidatos = cand
# #         st.session_state.info_grid = grid
# #         st.session_state.map_lat = mlat
# #         st.session_state.map_lng = mlng
# #         st.session_state.map_raio = mraio
# #         st.session_state.cadeia = cadeia
# #         st.session_state.raio_circulo = raio_circulo
# #         st.session_state.analise_ativa = True
# #         st.success(f"{n_cand} candidatos com potencial >= {CORTE_POTENCIAL}.")

# # # ==========================================================
# # # Otimização (pré-processamento + CPLEX)
# # # ==========================================================
# # if config.get("btn_otimizar"):
# #     cand = st.session_state.dados_candidatos
# #     if st.session_state.analise_ativa and cand is not None and not cand.empty:
# #         with st.spinner("Otimizando rede..."):
# #             matriz_cplex, dados_cobertura = pré_computar_cenarios(
# #                 st.session_state.dados_candidatos,
# #                 st.session_state.dados_eletropostos or [],
# #                 st.session_state.dados_pois,
# #                 1500, 4, 800
# #             )
# #             resultado = resolver_modelo_cplex(matriz_cplex, dados_cobertura, 0.85)
# #             if resultado and resultado["status"] == "Optimal":
# #                 st.session_state.nodos_otimizados = resultado["nodos_selecionados"]
# #             else:
# #                 st.error("Modelo inviável. Verifique o terminal.")
# #                 st.session_state.nodos_otimizados = []
# #     else:
# #         st.warning("Gere a malha de candidatos primeiro.")

# # # ==========================================================
# # # Área principal (mapa)
# # # ==========================================================
# # if st.session_state.analise_ativa:
# #     if st.session_state.dados_pois is None or st.session_state.dados_pois.empty:
# #         st.warning("Nenhum POI encontrado.")
# #     else:
# #         renderizar_mapa_completo(
# #             lat=st.session_state.map_lat,
# #             lng=st.session_state.map_lng,
# #             raio=st.session_state.map_raio,
# #             df_pois=st.session_state.dados_pois,
# #             df_cand=st.session_state.dados_candidatos,
# #             grid=st.session_state.info_grid,
# #             dados_eletropostos=st.session_state.dados_eletropostos,
# #             categorias_pois=CATEGORIAS_POIS,
# #             nodos_otimizados=st.session_state.nodos_otimizados,
# #             cadeia_circulos=st.session_state.cadeia,
# #             raio_circulo_m=st.session_state.raio_circulo
# #         )
# # else:
# #     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")










# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
# Dois modos de varredura com a mesma lógica de busca:
#   - Urbano (raio): círculo em torno de um ponto.
#   - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
# Ambos calculam o Potencial de Implantação (IP) normalizado em [1,5] e filtram por um corte.
# """

# import os
# import math
# import numpy as np
# import pandas as pd
# import streamlit as st
# from scipy.spatial import cKDTree

# from api.google_places import get_google_places_client
# from components.sidebar import render_sidebar
# from components.mapa import renderizar_mapa_completo
# from utils.geo_math import processar_grid_e_centroides
# from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
# from utils.potencial import (carregar_sensores, carregar_municipios,
#                              calcular_potencial, filtrar_por_potencial)
# from modelo.simulador import pré_computar_cenarios
# from modelo.otimizador import resolver_modelo_cplex

# # Caminhos dos dados
# SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
# RODOVIAS_DIR = os.path.join("dados", "rodovias")
# SENSORES_DIR = os.path.join("dados", "sensores")
# MUNICIPIOS_PATH = os.path.join("dados", "municipios", "municipios_sp.json")

# # Teto de NOVAS consultas à API por corrida (proteção de custo). None = sem limite.
# LIMITE_NOVAS_CONSULTAS = 100
# # Corte do potencial: candidatos com score_potencial >= CORTE_POTENCIAL passam ao modelo.
# CORTE_POTENCIAL = 3.0
# # No modo rodovia, POIs candidatos devem estar até esta distância do traçado (metros).
# DIST_VIA_M = 300
# # Categoria de POI usada como candidato no modo rodovia (paradas: hotéis, restaurantes, mercados...).
# CANDIDATO_CATEGORIA = "Varejo e lazer"

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Designação eletropostos", layout="wide")

# st.markdown("""
#     <style>
#     .main .block-container { padding: 0.5rem 0.5rem 0rem 0.5rem; max-width: 100%; }
#     iframe { width: 100%; height: 90vh; }
#     </style>
# """, unsafe_allow_html=True)

# CATEGORIAS_POIS = {
#     "Varejo e lazer": {
#         "types": ["shopping_mall", "supermarket", "restaurant", "cafe", "lodging", "gas_station"],
#         "color": "blue", "icon": "shopping-cart", "peso": 3.0
#     },
#     "Transporte": {
#         "types": ["bus_station", "subway_station", "transit_station"],
#         "color": "red", "icon": "bus", "peso": 2.0
#     },
#     "Serviços e saúde": {
#         "types": ["hospital", "bank", "university"],
#         "color": "purple", "icon": "heart", "peso": 1.5
#     }
# }

# # --- INICIALIZAR ESTADO DA SESSÃO ---
# for chave, valor in {
#     'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
#     'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
#     'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
#     'cadeia': None, 'raio_circulo': None,
# }.items():
#     if chave not in st.session_state:
#         st.session_state[chave] = valor


# # ==========================================================
# # Dados do PI (sensores e municípios), carregados uma vez
# # ==========================================================
# @st.cache_resource
# def _carregar_dados_pi():
#     sens = carregar_sensores(SENSORES_DIR) if os.path.isdir(SENSORES_DIR) else pd.DataFrame()
#     muni = carregar_municipios(MUNICIPIOS_PATH) if os.path.exists(MUNICIPIOS_PATH) else pd.DataFrame()
#     return sens, muni


# # ==========================================================
# # Helpers
# # ==========================================================
# def _haversine_m(lat0, lon0, lats, lons):
#     R = 6371000.0
#     p = np.pi / 180.0
#     lats = np.asarray(lats, dtype=float); lons = np.asarray(lons, dtype=float)
#     a = (np.sin((lats - lat0) * p / 2) ** 2
#          + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
#     return 2 * R * np.arcsin(np.sqrt(a))


# def _pois_proximos_tracado(df, comps, dist_m=DIST_VIA_M):
#     """Retorna uma máscara booleana dos POIs de df que estão a até dist_m do traçado."""
#     if df is None or df.empty or not comps:
#         return pd.Series([False] * (0 if df is None else len(df)), index=(None if df is None else df.index))
#     rpts = []
#     for ln in comps:
#         rpts += list(ln.coords)  # (lon, lat)
#     rpts = np.asarray(rpts, float)
#     lat0 = float(np.mean(rpts[:, 1]))
#     kx = 111320.0 * math.cos(math.radians(lat0))
#     ky = 111320.0
#     road_xy = np.column_stack([rpts[:, 0] * kx, rpts[:, 1] * ky])
#     tree = cKDTree(road_xy)
#     poi_xy = np.column_stack([df["Lng"].to_numpy() * kx, df["Lat"].to_numpy() * ky])
#     dist, _ = tree.query(poi_xy)
#     return pd.Series(dist <= dist_m, index=df.index)


# def _candidatos_de_pois(df_cand_pois, df_pois_todos, tamanho_grid_m=800, raio_ponto_m=800):
#     """Constrói candidatos a partir de POIs (modo rodovia), no esquema esperado pelo mapa/simulador."""
#     if df_cand_pois is None or df_cand_pois.empty:
#         return pd.DataFrame(), None
#     lats = df_cand_pois["Lat"].to_numpy(); lngs = df_cand_pois["Lng"].to_numpy()
#     lat_ref = float(np.mean(lats))
#     lat_step = tamanho_grid_m / 111320.0
#     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

#     tem = df_pois_todos is not None and not df_pois_todos.empty
#     base_lat = list(df_pois_todos["Lat"]) if tem else list(lats)
#     base_lng = list(df_pois_todos["Lng"]) if tem else list(lngs)
#     lat_min = min(float(lats.min()), min(base_lat))
#     lng_min = min(float(lngs.min()), min(base_lng))

#     plat = df_pois_todos["Lat"].to_numpy() if tem else lats
#     plng = df_pois_todos["Lng"].to_numpy() if tem else lngs

#     linhas = []
#     for la, lo in zip(lats, lngs):
#         d = _haversine_m(la, lo, plat, plng)
#         qtd = int((d <= raio_ponto_m).sum())
#         linhas.append({
#             "cell_i": int((la - lat_min) / lat_step),
#             "cell_j": int((lo - lng_min) / lng_step),
#             "Lat_Centroide": float(la), "Lng_Centroide": float(lo),
#             "Qtd_POIs": qtd, "Score_Estimado": 0.0,
#         })
#     cand = pd.DataFrame(linhas)
#     info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
#     return cand, info_grid


# # ==========================================================
# # Coletores
# # ==========================================================
# def _coletar_urbano(cliente, cfg, sens, muni):
#     df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
#     eletr = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
#     cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
#     # Potencial (urbano: só critérios de POIs + vizinhos) e corte
#     cand = calcular_potencial(cand, df_pois, eletr, modo="urbano")
#     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)
#     return df_pois, eletr, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"], None, None


# def _coletar_rodovia(cliente, cfg, status, sens, muni):
#     if not cfg.get("rodovias_sel"):
#         st.warning("Selecione ao menos uma rodovia.")
#         return None
#     if not os.path.exists(SP_POLY_PATH):
#         st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
#         return None

#     poly = carregar_poligono_estado(SP_POLY_PATH)
#     dfs, evs, centros_all, comps_all = [], {}, [], []

#     for rod in cfg["rodovias_sel"]:
#         arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
#         if not os.path.exists(arq):
#             st.warning(f"Arquivo não encontrado: {arq}")
#             continue
#         comps, km = carregar_tracado(arq, rod["ref"], poly)
#         comps_all += comps
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
#     eletr = list(evs.values())

#     # Candidatos = POIs geradores de parada (Varejo e lazer) SOBRE a via (<= DIST_VIA_M do traçado)
#     if not df_pois.empty:
#         df_par = df_pois[df_pois["Categoria"] == CANDIDATO_CATEGORIA]
#         if not df_par.empty:
#             mask = _pois_proximos_tracado(df_par, comps_all, DIST_VIA_M)
#             df_par = df_par[mask]
#     else:
#         df_par = df_pois
#     cand, grid = _candidatos_de_pois(df_par, df_pois, cfg["tamanho_grid"])

#     # Potencial (rodovia: IP completo x1..x4) e corte
#     cand = calcular_potencial(cand, df_pois, eletr, sens, muni, modo="rodovia")
#     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)

#     # Funil de candidatos (transparência do diagnóstico)
#     n_pois = 0 if df_pois is None or df_pois.empty else len(df_pois)
#     n_varejo = 0 if df_pois is None or df_pois.empty else int((df_pois['Categoria'] == CANDIDATO_CATEGORIA).sum())
#     n_via = 0 if df_par is None or df_par.empty else len(df_par)
#     n_corte = 0 if cand is None or cand.empty else len(cand)
#     st.info(f"Funil rodovia: POIs {n_pois} | Varejo {n_varejo} | sobre a via (<= {DIST_VIA_M} m) {n_via} | apos corte {CORTE_POTENCIAL}: {n_corte}")

#     if centros_all:
#         mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
#         mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
#     else:
#         mlat, mlng = -22.81, -47.06
#     return df_pois, eletr, cand, grid, mlat, mlng, 0, centros_all, cfg["raio"]


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
#     cliente.iniciar_sessao_consultas(LIMITE_NOVAS_CONSULTAS)
#     sens, muni = _carregar_dados_pi()

#     if config["modo"] == "Urbano (raio)":
#         with st.spinner("Mapeando POIs e calculando potencial..."):
#             resultado = _coletar_urbano(cliente, config, sens, muni)
#     else:
#         with st.spinner("Varrendo rodovia(s) e calculando potencial..."):
#             status = st.empty()
#             resultado = _coletar_rodovia(cliente, config, status, sens, muni)

#     if resultado:
#         df_pois, eletr, cand, grid, mlat, mlng, mraio, cadeia, raio_circulo = resultado
#         n_cand = 0 if cand is None or cand.empty else len(cand)
#         st.session_state.dados_pois = df_pois
#         st.session_state.dados_eletropostos = eletr
#         st.session_state.dados_candidatos = cand
#         st.session_state.info_grid = grid
#         st.session_state.map_lat = mlat
#         st.session_state.map_lng = mlng
#         st.session_state.map_raio = mraio
#         st.session_state.cadeia = cadeia
#         st.session_state.raio_circulo = raio_circulo
#         st.session_state.analise_ativa = True
#         st.success(f"{n_cand} candidatos com potencial >= {CORTE_POTENCIAL}.")

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
# # Área principal (mapa)
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
#             nodos_otimizados=st.session_state.nodos_otimizados,
#             cadeia_circulos=st.session_state.cadeia,
#             raio_circulo_m=st.session_state.raio_circulo
#         )
# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")









# """
# Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
# Dois modos de varredura com a mesma lógica de busca:
#   - Urbano (raio): círculo em torno de um ponto.
#   - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
# Ambos calculam o Potencial de Implantação (IP) normalizado em [1,5] e filtram por um corte.
# """

# import os
# import math
# import numpy as np
# import pandas as pd
# import streamlit as st
# from scipy.spatial import cKDTree

# from api.google_places import get_google_places_client
# from components.sidebar import render_sidebar
# from components.mapa import renderizar_mapa_completo
# from utils.geo_math import processar_grid_e_centroides
# from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
# from utils.potencial import (carregar_sensores, carregar_municipios,
#                              calcular_potencial, filtrar_por_potencial)
# from modelo.simulador import pré_computar_cenarios
# from modelo.otimizador import resolver_modelo_cplex

# # Caminhos dos dados
# SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
# RODOVIAS_DIR = os.path.join("dados", "rodovias")
# SENSORES_DIR = os.path.join("dados", "sensores")
# MUNICIPIOS_PATH = os.path.join("dados", "municipios", "municipios_sp.json")

# # Teto de NOVAS consultas à API por corrida (proteção de custo). None = sem limite.
# LIMITE_NOVAS_CONSULTAS = 20
# # Corte do potencial: candidatos com score_potencial >= CORTE_POTENCIAL passam ao modelo.
# CORTE_POTENCIAL = 2.5
# # No modo rodovia, POIs candidatos devem estar até esta distância do traçado (metros).
# DIST_VIA_M = 300
# # Categoria de POI usada como candidato no modo rodovia (paradas: hotéis, restaurantes, mercados...).
# CANDIDATO_CATEGORIA = "Varejo e lazer"

# # --- CONFIGURAÇÃO DA PÁGINA ---
# st.set_page_config(page_title="Designação eletropostos", layout="wide")

# st.markdown("""
#     <style>
#     .main .block-container { padding: 0.5rem 0.5rem 0rem 0.5rem; max-width: 100%; }
#     iframe { width: 100%; height: 90vh; }
#     </style>
# """, unsafe_allow_html=True)

# CATEGORIAS_POIS = {
#     "Varejo e lazer": {
#         "types": ["shopping_mall", "supermarket", "restaurant", "cafe", "lodging", "gas_station"],
#         "color": "blue", "icon": "shopping-cart", "peso": 3.0
#     },
#     "Transporte": {
#         "types": ["bus_station", "subway_station", "transit_station"],
#         "color": "red", "icon": "bus", "peso": 2.0
#     },
#     "Serviços e saúde": {
#         "types": ["hospital", "bank", "university"],
#         "color": "purple", "icon": "heart", "peso": 1.5
#     }
# }

# # --- INICIALIZAR ESTADO DA SESSÃO ---
# for chave, valor in {
#     'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
#     'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
#     'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
#     'cadeia': None, 'raio_circulo': None, 'resultado_otim': None,
# }.items():
#     if chave not in st.session_state:
#         st.session_state[chave] = valor


# # ==========================================================
# # Dados do PI (sensores e municípios), carregados uma vez
# # ==========================================================
# @st.cache_resource
# def _carregar_dados_pi():
#     sens = carregar_sensores(SENSORES_DIR) if os.path.isdir(SENSORES_DIR) else pd.DataFrame()
#     muni = carregar_municipios(MUNICIPIOS_PATH) if os.path.exists(MUNICIPIOS_PATH) else pd.DataFrame()
#     return sens, muni


# # ==========================================================
# # Helpers
# # ==========================================================
# def _haversine_m(lat0, lon0, lats, lons):
#     R = 6371000.0
#     p = np.pi / 180.0
#     lats = np.asarray(lats, dtype=float); lons = np.asarray(lons, dtype=float)
#     a = (np.sin((lats - lat0) * p / 2) ** 2
#          + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
#     return 2 * R * np.arcsin(np.sqrt(a))


# def _pois_proximos_tracado(df, comps, dist_m=DIST_VIA_M):
#     """Retorna uma máscara booleana dos POIs de df que estão a até dist_m do traçado."""
#     if df is None or df.empty or not comps:
#         return pd.Series([False] * (0 if df is None else len(df)), index=(None if df is None else df.index))
#     rpts = []
#     for ln in comps:
#         rpts += list(ln.coords)  # (lon, lat)
#     rpts = np.asarray(rpts, float)
#     lat0 = float(np.mean(rpts[:, 1]))
#     kx = 111320.0 * math.cos(math.radians(lat0))
#     ky = 111320.0
#     road_xy = np.column_stack([rpts[:, 0] * kx, rpts[:, 1] * ky])
#     tree = cKDTree(road_xy)
#     poi_xy = np.column_stack([df["Lng"].to_numpy() * kx, df["Lat"].to_numpy() * ky])
#     dist, _ = tree.query(poi_xy)
#     return pd.Series(dist <= dist_m, index=df.index)


# def _candidatos_de_pois(df_cand_pois, df_pois_todos, tamanho_grid_m=800, raio_ponto_m=800):
#     """Constrói candidatos a partir de POIs (modo rodovia), no esquema esperado pelo mapa/simulador."""
#     if df_cand_pois is None or df_cand_pois.empty:
#         return pd.DataFrame(), None
#     lats = df_cand_pois["Lat"].to_numpy(); lngs = df_cand_pois["Lng"].to_numpy()
#     lat_ref = float(np.mean(lats))
#     lat_step = tamanho_grid_m / 111320.0
#     lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

#     tem = df_pois_todos is not None and not df_pois_todos.empty
#     base_lat = list(df_pois_todos["Lat"]) if tem else list(lats)
#     base_lng = list(df_pois_todos["Lng"]) if tem else list(lngs)
#     lat_min = min(float(lats.min()), min(base_lat))
#     lng_min = min(float(lngs.min()), min(base_lng))

#     plat = df_pois_todos["Lat"].to_numpy() if tem else lats
#     plng = df_pois_todos["Lng"].to_numpy() if tem else lngs

#     linhas = []
#     for la, lo in zip(lats, lngs):
#         d = _haversine_m(la, lo, plat, plng)
#         qtd = int((d <= raio_ponto_m).sum())
#         linhas.append({
#             "cell_i": int((la - lat_min) / lat_step),
#             "cell_j": int((lo - lng_min) / lng_step),
#             "Lat_Centroide": float(la), "Lng_Centroide": float(lo),
#             "Qtd_POIs": qtd, "Score_Estimado": 0.0,
#         })
#     cand = pd.DataFrame(linhas)
#     info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
#     return cand, info_grid


# # ==========================================================
# # Coletores
# # ==========================================================
# def _coletar_urbano(cliente, cfg, sens, muni):
#     df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
#     eletr = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
#     cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
#     # Potencial (urbano: só critérios de POIs + vizinhos) e corte
#     cand = calcular_potencial(cand, df_pois, eletr, modo="urbano")
#     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)
#     return df_pois, eletr, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"], None, None


# def _coletar_rodovia(cliente, cfg, status, sens, muni):
#     if not cfg.get("rodovias_sel"):
#         st.warning("Selecione ao menos uma rodovia.")
#         return None
#     if not os.path.exists(SP_POLY_PATH):
#         st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
#         return None

#     poly = carregar_poligono_estado(SP_POLY_PATH)
#     dfs, evs, centros_all, comps_all = [], {}, [], []

#     for rod in cfg["rodovias_sel"]:
#         arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
#         if not os.path.exists(arq):
#             st.warning(f"Arquivo não encontrado: {arq}")
#             continue
#         comps, km = carregar_tracado(arq, rod["ref"], poly)
#         comps_all += comps
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
#     eletr = list(evs.values())

#     # Candidatos = POIs geradores de parada (Varejo e lazer) SOBRE a via (<= DIST_VIA_M do traçado)
#     if not df_pois.empty:
#         df_par = df_pois[df_pois["Categoria"] == CANDIDATO_CATEGORIA]
#         if not df_par.empty:
#             mask = _pois_proximos_tracado(df_par, comps_all, DIST_VIA_M)
#             df_par = df_par[mask]
#     else:
#         df_par = df_pois
#     cand, grid = _candidatos_de_pois(df_par, df_pois, cfg["tamanho_grid"])

#     # Potencial (rodovia: IP completo x1..x4) e corte
#     cand = calcular_potencial(cand, df_pois, eletr, sens, muni, modo="rodovia")
#     cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)


#     if centros_all:
#         mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
#         mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
#     else:
#         mlat, mlng = -22.81, -47.06
#     return df_pois, eletr, cand, grid, mlat, mlng, 0, centros_all, cfg["raio"]



# def _render_contrato_saida():
#     """Painel formal do contrato de saída, exibido abaixo do mapa."""
#     cand = st.session_state.dados_candidatos
#     r = st.session_state.get("resultado_otim")
#     n = 0 if cand is None or cand.empty else len(cand)
#     st.markdown("#### Contrato de saída")
#     if r and r.get("status") == "Optimal":
#         st.markdown(
#             f"Resumo: {n} candidatos com potencial acima do corte; "
#             f"{len(r.get('nodos_selecionados', []))} selecionados para instalação, "
#             f"cobrindo {r.get('pct_cobertura', 0):.1f}% dos POIs."
#         )
#     else:
#         st.markdown(
#             f"Resumo: {n} candidatos com potencial acima do corte. "
#             f"Rode a otimização para obter o contrato da Etapa 2."
#         )
#     col1, col2 = st.columns(2)
#     with col1:
#         st.markdown("**Etapa 1: pré-processamento**")
#         if cand is not None and not cand.empty and "score_potencial" in cand:
#             e1 = pd.DataFrame(
#                 {"Valor": [n,
#                            f"{cand['score_potencial'].min():.2f}",
#                            f"{cand['score_potencial'].max():.2f}",
#                            f"{cand['score_potencial'].mean():.2f}",
#                            f"{CORTE_POTENCIAL:.1f}"]},
#                 index=["Candidatos gerados", "Potencial mínimo", "Potencial máximo",
#                        "Potencial médio", "Corte aplicado"])
#             st.table(e1)
#         else:
#             st.caption("Sem candidatos.")
#     with col2:
#         st.markdown("**Etapa 2: otimização**")
#         if r and r.get("status") == "Optimal":
#             cobertos = r.get("cobertura_final", 0)
#             total = r.get("total_pois", 0)
#             e2 = pd.DataFrame(
#                 {"Valor": [len(r.get("nodos_selecionados", [])),
#                            f"{r.get('lucro_total', 0):.2f}",
#                            f"{r.get('pct_cobertura', 0):.1f}% ({cobertos} de {total} POIs)"]},
#                 index=["Nós selecionados", "Atratividade total", "Cobertura atingida"])
#             st.table(e2)
#         else:
#             st.caption("Rode a otimização para ver o contrato da Etapa 2.")


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
#     cliente.iniciar_sessao_consultas(LIMITE_NOVAS_CONSULTAS)
#     sens, muni = _carregar_dados_pi()

#     if config["modo"] == "Urbano (raio)":
#         with st.spinner("Mapeando POIs e calculando potencial..."):
#             resultado = _coletar_urbano(cliente, config, sens, muni)
#     else:
#         with st.spinner("Varrendo rodovia(s) e calculando potencial..."):
#             status = st.empty()
#             resultado = _coletar_rodovia(cliente, config, status, sens, muni)

#     if resultado:
#         df_pois, eletr, cand, grid, mlat, mlng, mraio, cadeia, raio_circulo = resultado
#         st.session_state.resultado_otim = None
#         st.session_state.dados_pois = df_pois
#         st.session_state.dados_eletropostos = eletr
#         st.session_state.dados_candidatos = cand
#         st.session_state.info_grid = grid
#         st.session_state.map_lat = mlat
#         st.session_state.map_lng = mlng
#         st.session_state.map_raio = mraio
#         st.session_state.cadeia = cadeia
#         st.session_state.raio_circulo = raio_circulo
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
#                 st.session_state.resultado_otim = resultado
#             else:
#                 st.error("Modelo inviável. Verifique o terminal.")
#                 st.session_state.nodos_otimizados = []
#                 st.session_state.resultado_otim = None
#     else:
#         st.warning("Gere a malha de candidatos primeiro.")

# # ==========================================================
# # Área principal (mapa)
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
#             nodos_otimizados=st.session_state.nodos_otimizados,
#             cadeia_circulos=st.session_state.cadeia,
#             raio_circulo_m=st.session_state.raio_circulo
#         )
#         _render_contrato_saida()
# else:
#     st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")











"""
Dashboard Exploratório: Análise de Geradores de Viagem (POIs) e Geração de nodos candidatos.
Dois modos de varredura com a mesma lógica de busca:
  - Urbano (raio): círculo em torno de um ponto.
  - Rodovia: corrente de círculos ao longo do traçado (varredura híbrida).
Ambos calculam o Potencial de Implantação (IP) normalizado em [1,5] e filtram por um corte.
"""

import os
import io
import math
import numpy as np
import pandas as pd
import streamlit as st
from scipy.spatial import cKDTree

from api.google_places import get_google_places_client
from components.sidebar import render_sidebar
from components.mapa import renderizar_mapa_completo
from utils.geo_math import processar_grid_e_centroides
from utils.rodovias import carregar_poligono_estado, carregar_tracado, gerar_cadeia_circulos
from utils.potencial import (carregar_sensores, carregar_municipios,
                             calcular_potencial, filtrar_por_potencial)
from modelo.simulador import pré_computar_cenarios
from modelo.otimizador import resolver_modelo_cplex

# Caminhos dos dados
SP_POLY_PATH = os.path.join("dados", "limites", "sp_estado.geojson")
RODOVIAS_DIR = os.path.join("dados", "rodovias")
SENSORES_DIR = os.path.join("dados", "sensores")
MUNICIPIOS_PATH = os.path.join("dados", "municipios", "municipios_sp.json")

# Teto de NOVAS consultas à API por corrida (proteção de custo). None = sem limite.
LIMITE_NOVAS_CONSULTAS = 50
# Corte do potencial: candidatos com score_potencial >= CORTE_POTENCIAL passam ao modelo.
CORTE_POTENCIAL = 2.5
# No modo rodovia, POIs candidatos devem estar até esta distância do traçado (metros).
DIST_VIA_M = 300
# Categoria de POI usada como candidato no modo rodovia (paradas: hotéis, restaurantes, mercados...).
CANDIDATO_CATEGORIA = "Varejo e lazer"

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Designação eletropostos", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding: 0.5rem 0.5rem 0rem 0.5rem; max-width: 100%; }
    iframe { width: 100%; height: 90vh; }
    </style>
""", unsafe_allow_html=True)

CATEGORIAS_POIS = {
    "Varejo e lazer": {
        "types": ["shopping_mall", "supermarket", "restaurant", "cafe", "lodging", "gas_station"],
        "color": "blue", "icon": "shopping-cart", "peso": 3.0
    },
    "Transporte": {
        "types": ["bus_station", "subway_station", "transit_station"],
        "color": "red", "icon": "bus", "peso": 2.0
    },
    "Serviços e saúde": {
        "types": ["hospital", "bank", "university"],
        "color": "purple", "icon": "heart", "peso": 1.5
    }
}

# --- INICIALIZAR ESTADO DA SESSÃO ---
for chave, valor in {
    'dados_pois': None, 'dados_eletropostos': None, 'dados_candidatos': None,
    'info_grid': None, 'analise_ativa': False, 'nodos_otimizados': [],
    'map_lat': -22.8171, 'map_lng': -47.0698, 'map_raio': 2000,
    'cadeia': None, 'raio_circulo': None, 'resultado_otim': None,
}.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


# ==========================================================
# Dados do PI (sensores e municípios), carregados uma vez
# ==========================================================
@st.cache_resource
def _carregar_dados_pi():
    sens = carregar_sensores(SENSORES_DIR) if os.path.isdir(SENSORES_DIR) else pd.DataFrame()
    muni = carregar_municipios(MUNICIPIOS_PATH) if os.path.exists(MUNICIPIOS_PATH) else pd.DataFrame()
    return sens, muni


# ==========================================================
# Helpers
# ==========================================================
def _haversine_m(lat0, lon0, lats, lons):
    R = 6371000.0
    p = np.pi / 180.0
    lats = np.asarray(lats, dtype=float); lons = np.asarray(lons, dtype=float)
    a = (np.sin((lats - lat0) * p / 2) ** 2
         + np.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def _pois_proximos_tracado(df, comps, dist_m=DIST_VIA_M):
    """Retorna uma máscara booleana dos POIs de df que estão a até dist_m do traçado."""
    if df is None or df.empty or not comps:
        return pd.Series([False] * (0 if df is None else len(df)), index=(None if df is None else df.index))
    rpts = []
    for ln in comps:
        rpts += list(ln.coords)  # (lon, lat)
    rpts = np.asarray(rpts, float)
    lat0 = float(np.mean(rpts[:, 1]))
    kx = 111320.0 * math.cos(math.radians(lat0))
    ky = 111320.0
    road_xy = np.column_stack([rpts[:, 0] * kx, rpts[:, 1] * ky])
    tree = cKDTree(road_xy)
    poi_xy = np.column_stack([df["Lng"].to_numpy() * kx, df["Lat"].to_numpy() * ky])
    dist, _ = tree.query(poi_xy)
    return pd.Series(dist <= dist_m, index=df.index)


def _candidatos_de_pois(df_cand_pois, df_pois_todos, tamanho_grid_m=800, raio_ponto_m=800):
    """Constrói candidatos a partir de POIs (modo rodovia), no esquema esperado pelo mapa/simulador."""
    if df_cand_pois is None or df_cand_pois.empty:
        return pd.DataFrame(), None
    lats = df_cand_pois["Lat"].to_numpy(); lngs = df_cand_pois["Lng"].to_numpy()
    lat_ref = float(np.mean(lats))
    lat_step = tamanho_grid_m / 111320.0
    lng_step = tamanho_grid_m / (111320.0 * math.cos(math.radians(lat_ref)))

    tem = df_pois_todos is not None and not df_pois_todos.empty
    base_lat = list(df_pois_todos["Lat"]) if tem else list(lats)
    base_lng = list(df_pois_todos["Lng"]) if tem else list(lngs)
    lat_min = min(float(lats.min()), min(base_lat))
    lng_min = min(float(lngs.min()), min(base_lng))

    plat = df_pois_todos["Lat"].to_numpy() if tem else lats
    plng = df_pois_todos["Lng"].to_numpy() if tem else lngs

    linhas = []
    for _, prow in df_cand_pois.iterrows():
        la = float(prow["Lat"]); lo = float(prow["Lng"])
        d = _haversine_m(la, lo, plat, plng)
        qtd = int((d <= raio_ponto_m).sum())
        linhas.append({
            "cell_i": int((la - lat_min) / lat_step),
            "cell_j": int((lo - lng_min) / lng_step),
            "Lat_Centroide": la, "Lng_Centroide": lo,
            "Qtd_POIs": qtd, "Score_Estimado": 0.0,
            "Tipo": prow.get("Tipo", ""), "Nome": prow.get("Nome", ""),
        })
    cand = pd.DataFrame(linhas)
    info_grid = {"lat_min": lat_min, "lng_min": lng_min, "lat_step": lat_step, "lng_step": lng_step}
    return cand, info_grid


# ==========================================================
# Coletores
# ==========================================================
def _coletar_urbano(cliente, cfg, sens, muni):
    df_pois = cliente.buscar_pois(cfg["lat"], cfg["lng"], cfg["raio"], CATEGORIAS_POIS)
    eletr = cliente.buscar_eletropostos((cfg["lat"], cfg["lng"]), cfg["raio"])
    cand, grid = processar_grid_e_centroides(df_pois, cfg["lat"], cfg["lng"], cfg["raio"], cfg["tamanho_grid"])
    if cand is not None and not cand.empty:
        cand["Tipo"] = "centroide"; cand["Nome"] = ""
    # Potencial (urbano: só critérios de POIs + vizinhos) e corte
    cand = calcular_potencial(cand, df_pois, eletr, modo="urbano")
    cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)
    return df_pois, eletr, cand, grid, cfg["lat"], cfg["lng"], cfg["raio"], None, None


def _coletar_rodovia(cliente, cfg, status, sens, muni):
    if not cfg.get("rodovias_sel"):
        st.warning("Selecione ao menos uma rodovia.")
        return None
    if not os.path.exists(SP_POLY_PATH):
        st.error(f"Polígono do estado não encontrado em {SP_POLY_PATH}")
        return None

    poly = carregar_poligono_estado(SP_POLY_PATH)
    dfs, evs, centros_all, comps_all = [], {}, [], []

    for rod in cfg["rodovias_sel"]:
        arq = os.path.join(RODOVIAS_DIR, rod["arquivo"])
        if not os.path.exists(arq):
            st.warning(f"Arquivo não encontrado: {arq}")
            continue
        comps, km = carregar_tracado(arq, rod["ref"], poly)
        comps_all += comps
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
    eletr = list(evs.values())

    # Candidatos = POIs geradores de parada (Varejo e lazer) SOBRE a via (<= DIST_VIA_M do traçado)
    if not df_pois.empty:
        df_par = df_pois[df_pois["Categoria"] == CANDIDATO_CATEGORIA]
        if not df_par.empty:
            mask = _pois_proximos_tracado(df_par, comps_all, DIST_VIA_M)
            df_par = df_par[mask]
    else:
        df_par = df_pois
    cand, grid = _candidatos_de_pois(df_par, df_pois, cfg["tamanho_grid"])

    # Potencial (rodovia: IP completo x1..x4) e corte
    cand = calcular_potencial(cand, df_pois, eletr, sens, muni, modo="rodovia")
    cand = filtrar_por_potencial(cand, CORTE_POTENCIAL)


    if centros_all:
        mlat = sum(c["lat"] for c in centros_all) / len(centros_all)
        mlng = sum(c["lng"] for c in centros_all) / len(centros_all)
    else:
        mlat, mlng = -22.81, -47.06
    return df_pois, eletr, cand, grid, mlat, mlng, 0, centros_all, cfg["raio"]



def _excel_bytes(df):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Solucao")
    return buf.getvalue()


def _tabela_solucao_detalhada(cand, df_pois, nodos, raio_cobertura_m=800):
    """Detalhe dos nós designados: coordenadas, potencial, critérios, tipo e cobertura."""
    if cand is None or cand.empty or not nodos:
        return pd.DataFrame()
    tem = df_pois is not None and not df_pois.empty
    plat = df_pois["Lat"].to_numpy() if tem else None
    plng = df_pois["Lng"].to_numpy() if tem else None
    linhas = []
    for idx, row in cand.iterrows():
        cid = f"C{idx}"
        if cid not in nodos:
            continue
        la = float(row["Lat_Centroide"]); lo = float(row["Lng_Centroide"])
        cob = int((_haversine_m(la, lo, plat, plng) <= raio_cobertura_m).sum()) if tem else 0
        linhas.append({
            "id": cid,
            "latitude": round(la, 6),
            "longitude": round(lo, 6),
            "potencial": round(float(row.get("score_potencial", row.get("Score_Estimado", 0))), 2),
            "x1_trafego": row.get("x1", ""),
            "x2_populacao": row.get("x2", ""),
            "x3_servico": row.get("x3", ""),
            "x4_existentes": round(float(row.get("x4", 0)), 2),
            "tipo": row.get("Tipo", ""),
            "nome": row.get("Nome", ""),
            "pois_proximos": int(row.get("Qtd_POIs", 0)),
            "pois_cobertos": cob,
        })
    return pd.DataFrame(linhas)


def _render_contrato_saida():
    """Painel formal do contrato de saída, exibido abaixo do mapa."""
    cand = st.session_state.dados_candidatos
    r = st.session_state.get("resultado_otim")
    n = 0 if cand is None or cand.empty else len(cand)
    otimizou = bool(r and r.get("status") == "Optimal")
    st.markdown("#### Contrato de saída")

    def _tabela_e1(container):
        with container:
            st.markdown("**Etapa 1: pré-processamento**")
            if cand is not None and not cand.empty and "score_potencial" in cand:
                e1 = pd.DataFrame(
                    {"Valor": [n,
                               f"{cand['score_potencial'].min():.2f}",
                               f"{cand['score_potencial'].max():.2f}",
                               f"{cand['score_potencial'].mean():.2f}",
                               f"{CORTE_POTENCIAL:.1f}"]},
                    index=["Candidatos gerados", "Potencial mínimo", "Potencial máximo",
                           "Potencial médio", "Corte aplicado"])
                st.table(e1)
            else:
                st.caption("Sem candidatos.")

    if otimizou:
        st.markdown(
            f"Resumo: {n} candidatos com potencial acima do corte; "
            f"{len(r.get('nodos_selecionados', []))} selecionados para instalação, "
            f"cobrindo {r.get('pct_cobertura', 0):.1f}% dos POIs."
        )
        col1, col2 = st.columns(2)
        _tabela_e1(col1)
        with col2:
            st.markdown("**Etapa 2: otimização**")
            cobertos = r.get("cobertura_final", 0)
            total = r.get("total_pois", 0)
            e2 = pd.DataFrame(
                {"Valor": [len(r.get("nodos_selecionados", [])),
                           f"{r.get('lucro_total', 0):.2f}",
                           f"{r.get('pct_cobertura', 0):.1f}% ({cobertos} de {total} POIs)"]},
                index=["Nós selecionados", "Atratividade total", "Cobertura atingida"])
            st.table(e2)
        detalhe = _tabela_solucao_detalhada(cand, st.session_state.dados_pois, r.get("nodos_selecionados", []))
        if detalhe is not None and not detalhe.empty:
            st.download_button(
                "Baixar solução detalhada (Excel)",
                data=_excel_bytes(detalhe),
                file_name="solucao_eletropostos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.markdown(f"Resumo: {n} candidatos com potencial acima do corte.")
        _tabela_e1(st.container())


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
    cliente.iniciar_sessao_consultas(LIMITE_NOVAS_CONSULTAS)
    sens, muni = _carregar_dados_pi()

    if config["modo"] == "Urbano (raio)":
        with st.spinner("Mapeando POIs e calculando potencial..."):
            resultado = _coletar_urbano(cliente, config, sens, muni)
    else:
        with st.spinner("Varrendo rodovia(s) e calculando potencial..."):
            status = st.empty()
            resultado = _coletar_rodovia(cliente, config, status, sens, muni)

    if resultado:
        df_pois, eletr, cand, grid, mlat, mlng, mraio, cadeia, raio_circulo = resultado
        st.session_state.resultado_otim = None
        st.session_state.dados_pois = df_pois
        st.session_state.dados_eletropostos = eletr
        st.session_state.dados_candidatos = cand
        st.session_state.info_grid = grid
        st.session_state.map_lat = mlat
        st.session_state.map_lng = mlng
        st.session_state.map_raio = mraio
        st.session_state.cadeia = cadeia
        st.session_state.raio_circulo = raio_circulo
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
                st.session_state.resultado_otim = resultado
            else:
                st.error("Modelo inviável. Verifique o terminal.")
                st.session_state.nodos_otimizados = []
                st.session_state.resultado_otim = None
    else:
        st.warning("Gere a malha de candidatos primeiro.")

# ==========================================================
# Área principal (mapa)
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
            nodos_otimizados=st.session_state.nodos_otimizados,
            cadeia_circulos=st.session_state.cadeia,
            raio_circulo_m=st.session_state.raio_circulo
        )
        _render_contrato_saida()
else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Gerar malha e candidatos'.")