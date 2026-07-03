# """
# Dashboard principal para visualização de Fluxos O-D (Matrizes PNT)
# """
# import streamlit as st
# import os
# from components.sidebar_flujos import render_sidebar_flujos
# from utils.processador_matriz import preparar_candidatos_rotas
# from utils.api_rotas import obter_rotas_com_cache

# # Configuração da página Streamlit
# st.set_page_config(page_title="Mapa de Fluxos O-D", page_icon="🛣️", layout="wide")

# def main():
#     st.title("🛣️ Análise de Fluxos Rodoviários e Matrizes O-D")
#     st.markdown("""
#     Esta aplicação filtra pares Origem-Destino da matriz, consulta a API de Rotas do Google com 
#     limites rígidos de orçamento e agrega os trechos sobrepostos para identificar os principais corredores logísticos.
#     """)
    
#     # 1. Renderiza a Sidebar e pega os parâmetros
#     params = render_sidebar_flujos()
    
#     # Container para métricas
#     metricas_placeholder = st.container()
    
#     # 2. Lógica ao clicar no botão
#     if params["btn_processar"]:
#         st.write("---")
#         status_text = st.empty()
        
#         caminho_excel = 'dados/Matrizes PNT 2016-2017.xlsx'
#         db_path = 'geocache.db'
        
#         if not os.path.exists(caminho_excel):
#             st.error(f"Arquivo Excel não encontrado na pasta 'dados/'.")
#             return
            
#         if not os.path.exists(db_path):
#             st.error("Banco de dados 'geocache.db' não encontrado. Execute o geocode_centroides.py primeiro.")
#             return

#         try:
#             # ==========================================
#             # PASSOS 3 e 4: Filtros Locais (Custo Zero)
#             # ==========================================
#             status_text.info(f"Lendo Excel ({params['aba_matriz']}) e aplicando filtros espaciais...")
            
#             df_candidatos = preparar_candidatos_rotas(
#                 caminho_excel=caminho_excel,
#                 aba_matriz=params['aba_matriz'],
#                 db_path=db_path,
#                 fluxo_minimo=params['fluxo_minimo'],
#                 dist_minima_km=params['dist_minima_km']
#             )
            
#             if df_candidatos.empty:
#                 status_text.warning("Nenhuma rota sobreviveu aos filtros de distância e fluxo. Tente reduzir os valores na barra lateral.")
#                 return
                
#             # Mostrar impacto dos filtros
#             with metricas_placeholder:
#                 col1, col2, col3 = st.columns(3)
#                 col1.metric("Rotas Candidatas (Após Filtro)", f"{len(df_candidatos):,}")
                
#             # ==========================================
#             # PASSO 5: Consulta API / Cache
#             # ==========================================
#             status_text.info(f"Consultando Google Directions API (Limite: {params['limite_api']} novas rotas)...")
            
#             df_rotas, consultas_api, rotas_cache = obter_rotas_com_cache(
#                 df_candidatos=df_candidatos,
#                 db_path=db_path,
#                 limite_api=params['limite_api']
#             )
            
#             if df_rotas.empty:
#                 status_text.warning("Nenhuma rota pôde ser traçada.")
#                 return
                
#             with metricas_placeholder:
#                 col2.metric("Rotas Puxadas do Cache (Grátis)", f"{rotas_cache:,}")
#                 col3.metric("Novas Consultas na API", f"{consultas_api:,}", f"${(consultas_api / 1000) * 5.00:.2f} USD")
                
#             status_text.success("Rotas obtidas com sucesso! Preparando para decodificar e gerar o mapa...")
            
#             # TODO: Passo 6 - Quebrar e Somar Segmentos (Shapely)
#             # TODO: Passo 7 - Renderizar Mapa Folium
#             st.dataframe(df_rotas[['Origem_ID', 'Destino_ID', 'Fluxo', 'Distancia_Metros', 'Fonte']].head(10))
            
#         except Exception as e:
#             st.error(f"Erro durante o processamento: {e}")

# if __name__ == "__main__":
#     main()









"""
Dashboard principal para visualização de Fluxos O-D (Matrizes PNT)
"""
import streamlit as st
import os

# Importações dos nossos módulos modulares (components e utils)
from components.sidebar_flujos import render_sidebar_flujos
from utils.processador_matriz import preparar_candidatos_rotas
from utils.api_rotas import obter_rotas_com_cache
from utils.mapa_calor import gerar_mapa_calor_rotas
from streamlit_folium import st_folium

# Configuração da página Streamlit
st.set_page_config(page_title="Mapa de fluxos O-D", page_icon="🛣️", layout="wide")

def main():
    st.title("Fluxos rodoviários de matrizes O-D")
    # st.markdown("""
    # Esta aplicação filtra pares Origem-Destino da matriz, consulta a API de rotas do Google com 
    # limites rígidos de orçamento e agrega os trechos sobrepostos para identificar os principais corredores logísticos.
    # """)
    
    # 1. Renderiza a Sidebar e pega os parâmetros
    params = render_sidebar_flujos()
    
    # Container reservado para as métricas financeiras e de rotas
    metricas_placeholder = st.container()
    
    # 2. Lógica executada ao clicar no botão "Processar"
    if params["btn_processar"]:
        st.write("---")
        status_text = st.empty()
        
        caminho_excel = 'dados/Matrizes PNT 2016-2017.xlsx'
        db_path = 'geocache.db'
        
        # Validações iniciais de arquivos
        if not os.path.exists(caminho_excel):
            st.error(f"Arquivo Excel não encontrado na pasta 'dados/'.")
            return
            
        if not os.path.exists(db_path):
            st.error("Banco de dados 'geocache.db' não encontrado. Execute o geocode_centroides.py primeiro.")
            return

        try:
            # ==========================================
            # PASSOS 3 e 4: Filtros Locais (Custo Zero)
            # ==========================================
            status_text.info(f"Lendo Excel ({params['aba_matriz']}) e aplicando filtros espaciais (Haversine)...")
            
            df_candidatos = preparar_candidatos_rotas(
                caminho_excel=caminho_excel,
                aba_matriz=params['aba_matriz'],
                db_path=db_path,
                fluxo_minimo=params['fluxo_minimo'],
                dist_minima_km=params['dist_minima_km']
            )
            
            if df_candidatos.empty:
                status_text.warning("Nenhuma rota sobreviveu aos filtros de distância e fluxo. Tente reduzir os valores na barra lateral.")
                return
                
            # Exibir impacto dos filtros locais
            with metricas_placeholder:
                col1, col2, col3 = st.columns(3)
                col1.metric("Rotas candidatas (após filtro)", f"{len(df_candidatos):,}")
                
            # ==========================================
            # PASSO 5: Consulta API e Gerenciamento de Cache
            # ==========================================
            status_text.info(f"Verificando Cache e consultando Google Directions API (Limite: {params['limite_api']} novas rotas)...")
            
            df_rotas, consultas_api, rotas_cache = obter_rotas_com_cache(
                df_candidatos=df_candidatos,
                db_path=db_path,
                limite_api=params['limite_api']
            )
            
            if df_rotas.empty:
                status_text.warning("Nenhuma rota pôde ser traçada.")
                return
                
            # Exibir métricas de consumo financeiro
            with metricas_placeholder:
                col2.metric("Rotas puxadas do cache (grátis)", f"{rotas_cache:,}")
                col3.metric("Novas consultas na API", f"{consultas_api:,}", f"${(consultas_api / 1000) * 5.00:.2f} USD")
                
            status_text.success("Rotas obtidas com sucesso! Renderizando mapa de calor rodoviário...")
            
            # ==========================================
            # PASSOS 6 e 7: Processamento de Polilinhas e Mapa
            # ==========================================
            mapa = gerar_mapa_calor_rotas(df_rotas)
            
            if mapa:
                # 7.1 Renderiza o mapa interativo na interface Streamlit
                st_folium(mapa, use_container_width=True, height=750, returned_objects=[])
                
                # 7.2 Exibe a tabela detalhada minimizada abaixo do mapa
                with st.expander("Ver tabela detalhada de rotas"):
                    st.dataframe(df_rotas[['Origem_ID', 'Destino_ID', 'Fluxo', 'Distancia_Metros', 'Fonte']])
            else:
                st.warning("Não foi possível gerar o mapa com os dados fornecidos.")
                
            # Limpa as mensagens de carregamento
            status_text.empty()
            
        except Exception as e:
            st.error(f"Erro durante o processamento: {e}")

if __name__ == "__main__":
    main()