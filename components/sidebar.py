# """
# Componente: barra lateral de controles e parâmetros
# """

# import streamlit as st

# def render_sidebar():
#     """Renderiza a sidebar e retorna os parâmetros configurados pelo usuário."""
#     with st.sidebar:    
#         st.header("Parâmetros espaciais")
#         lat = st.number_input("Latitude inicial", value=-22.815313, format="%.6f")
#         lng = st.number_input("Longitude inicial", value=-47.06914, format="%.6f")
        
#         raio = st.slider("Raio de busca (metros)", min_value=500, max_value=10000, value=2000, step=500)
#         tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)
            
#         st.divider()
#         btn_gerar = st.button("Gerar malha e candidatos", type="primary", use_container_width=True)

#         st.divider()
#         mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
#         mostrar_eletropostos = st.toggle("Mostrar eletropostos (concorrência)", value=False, help="Exibe a infraestrutura de recarga já existente na área.")

#     # Retorna um dicionário com todos os estados para o app.py
#     return {
#         "lat": lat,
#         "lng": lng,
#         "raio": raio,
#         "tamanho_grid": tamanho_grid,
#         "btn_gerar": btn_gerar,
#         "mostrar_heatmap": mostrar_heatmap,
#         "mostrar_eletropostos": mostrar_eletropostos
#     }







# """
# Componente: barra lateral de controles e parâmetros
# """

# import streamlit as st

# def render_sidebar():
#     """Renderiza a sidebar e retorna os parâmetros configurados pelo usuário."""
#     with st.sidebar:    
#         st.header("Parâmetros espaciais")
#         lat = st.number_input("Latitude inicial", value=-22.815313, format="%.6f")
#         lng = st.number_input("Longitude inicial", value=-47.06914, format="%.6f")
        
#         # Adicionado format="%.1f" para exibir apenas uma casa decimal (ex: 2.0, 2.5)
#         raio_km = st.slider("Raio de busca (km)", min_value=1.0, max_value=50.0, value=2.0, step=0.5, format="%.1f")
#         tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)
            
#         st.divider()
#         btn_gerar = st.button("Gerar malha e candidatos", type="primary", use_container_width=True)

#         st.divider()
#         mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
#         mostrar_eletropostos = st.toggle("Mostrar eletropostos (concorrência)", value=False, help="Exibe a infraestrutura de recarga já existente na área.")

#     # Converte o raio de km para metros internamente antes de enviar ao app.py, 
#     # mantendo a compatibilidade com a matemática das APIs.
#     raio_metros = int(raio_km * 1000)

#     # Retorna um dicionário com todos os estados para o app.py
#     return {
#         "lat": lat,
#         "lng": lng,
#         "raio": raio_metros,
#         "tamanho_grid": tamanho_grid,
#         "btn_gerar": btn_gerar,
#         "mostrar_heatmap": mostrar_heatmap,
#         "mostrar_eletropostos": mostrar_eletropostos
#     }







"""
Componente: Barra lateral de controles e parâmetros
"""

import streamlit as st

def render_sidebar():
    """Renderiza a sidebar e retorna os parâmetros configurados pelo usuário."""
    with st.sidebar:    
        st.header("Parâmetros espaciais")
        lat = st.number_input("Latitude inicial", value=-22.817100, format="%.6f")
        lng = st.number_input("Longitude inicial", value=-47.069800, format="%.6f")
        
        # Adicionado format="%.1f" para exibir apenas uma casa decimal (ex: 2.0, 2.5)
        raio_km = st.slider("Raio de busca (km)", min_value=1.0, max_value=50.0, value=2.0, step=0.5, format="%.1f")
        tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)
            
        st.divider()
        btn_gerar = st.button("Gerar malha e candidatos", type="primary", use_container_width=True)

        st.divider()
        # Novo toggle para os Nodos Candidatos (Ativo por padrão)
        mostrar_nodos = st.toggle("Mostrar nodos candidatos", value=True, help="Exibe as opções de locais potenciais para instalação (centroides da malha).")
        mostrar_heatmap = st.toggle("Ativar mapa de calor (demanda)", value=False, help="Estima a demanda combinando o perfil do local e o fluxo de visitantes.")
        mostrar_eletropostos = st.toggle("Mostrar eletropostos (concorrência)", value=False, help="Exibe a infraestrutura de recarga já existente na área.")

    # Converte o raio de km para metros internamente antes de enviar ao app.py, 
    # mantendo a compatibilidade com a matemática das APIs.
    raio_metros = int(raio_km * 1000)

    # Retorna um dicionário com todos os estados para o app.py
    return {
        "lat": lat,
        "lng": lng,
        "raio": raio_metros,
        "tamanho_grid": tamanho_grid,
        "btn_gerar": btn_gerar,
        "mostrar_nodos": mostrar_nodos,
        "mostrar_heatmap": mostrar_heatmap,
        "mostrar_eletropostos": mostrar_eletropostos
    }