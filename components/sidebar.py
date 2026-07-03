# components\sidebar.py

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
        btn_gerar = st.button("Gerar malha e candidatos", use_container_width=True)

        # Foram removidos os toggles de exibição de camadas, pois agora 
        # o controle de camadas é feito nativamente dentro do mapa (LayerControl)

        st.divider()
        # st.header("Otimização Matemática")
        # st.caption("Gera os lucros pré-computados e resolve o modelo MILP (CPLEX).")
        # Botão de Otimização destacado
        btn_otimizar = st.button("🟢 Otimizar designação", type="primary", use_container_width=True)

    # Converte o raio de km para metros internamente antes de enviar ao app.py, 
    # mantendo a compatibilidade com a matemática das APIs.
    raio_metros = int(raio_km * 1000)

    # Retorna um dicionário com todos os estados estritamente necessários para o app.py
    return {
        "lat": lat,
        "lng": lng,
        "raio": raio_metros,
        "tamanho_grid": tamanho_grid,
        "btn_gerar": btn_gerar,
        "btn_otimizar": btn_otimizar
    }