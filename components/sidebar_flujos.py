# """
# Componente: Barra lateral para o Dashboard de Fluxos O-D
# """
# import streamlit as st

# def render_sidebar_flujos():
#     """Renderiza a sidebar para controle de orçamento e filtros de matriz."""
#     with st.sidebar:
#         st.header("⚙️ Filtros de Orçamento e API")
        
#         # O famoso "Safety Switch" de orçamento
#         limite_api = st.number_input(
#             "Limitar consultas à API (Máx. Rotas)", 
#             min_value=10, max_value=1000, value=200, step=10,
#             help="Define o número máximo de rotas inéditas que o Google será consultado."
#         )
        
#         st.divider()
#         st.header("📍 Filtros Espaciais e Matriz")
        
#         # Filtro de Distância (Haversine Local)
#         dist_minima_km = st.slider(
#             "Distância mínima em linha reta (km)", 
#             min_value=0, max_value=1000, value=150, step=10,
#             help="Filtra rotas curtas antes mesmo de pensar em chamar a API."
#         )
        
#         # Filtro de Volume de Tráfego
#         fluxo_minimo = st.number_input(
#             "Fluxo mínimo de veículos (por O-D)", 
#             min_value=1, max_value=10000, value=10, step=1,
#             help="Ignorar pares Origem-Destino que tenham menos que este volume."
#         )
        
#         st.divider()
#         st.info("💡 Rotas já salvas no banco de dados (geocache.db) não descontam do limite da API.")
        
#         btn_processar = st.button("🚀 Processar e Gerar Mapa", type="primary", use_container_width=True)
        
#     return {
#         "limite_api": limite_api,
#         "dist_minima_km": dist_minima_km,
#         "fluxo_minimo": fluxo_minimo,
#         "btn_processar": btn_processar
#     }










"""
Componente: Barra lateral para o Dashboard de Fluxos O-D
"""
import streamlit as st

def render_sidebar_flujos():
    """Renderiza a sidebar para controle de orçamento e filtros de matriz."""
    with st.sidebar:
        st.header("Filtros de orçamento e API")
        
        limite_api = st.number_input(
            "Limitar consultas à API (Máx. Rotas)", 
            min_value=10, max_value=1000, value=200, step=10,
            help="Define o número máximo de rotas inéditas que o Google será consultado."
        )
        
        st.divider()
        st.header("Filtros espaciais e matriz")
        
        # NOVO: Seletor de Matriz do Excel
        abas_disponiveis = ["Matriz_P_I", "Matriz_P_II", "Matriz_P_III"] # Adicione outras se existirem
        aba_matriz = st.selectbox(
            "Matriz O-D (aba do Excel)", 
            abas_disponiveis, 
            index=1, # Começa na Matriz_P_II por padrão
            help="Selecione qual matriz de origem-destino será processada."
        )
        
        # Filtro de Distância (Haversine Local)
        dist_minima_km = st.slider(
            "Distância mínima em linha reta (km)", 
            min_value=0, max_value=1000, value=150, step=10,
            help="Filtra rotas curtas antes mesmo de pensar em chamar a API."
        )
        
        # Filtro de Volume de Tráfego
        fluxo_minimo = st.number_input(
            "Fluxo mínimo de veículos (por O-D)", 
            min_value=1, max_value=10000, value=10, step=1,
            help="Ignorar pares Origem-Destino que tenham menos que este volume."
        )
        
        st.divider()
        # st.info("💡 Rotas já salvas no banco de dados (geocache.db) não descontam do limite da API.")
        
        btn_processar = st.button("Processar e gerar mapa", type="primary", use_container_width=True)
        
    return {
        "limite_api": limite_api,
        "aba_matriz": aba_matriz, # NOVO parâmetro retornado
        "dist_minima_km": dist_minima_km,
        "fluxo_minimo": fluxo_minimo,
        "btn_processar": btn_processar
    }