# # components\sidebar.py

# """
# Componente: Barra lateral de controles e parâmetros
# """

# import streamlit as st

# def render_sidebar():
#     """Renderiza a sidebar e retorna os parâmetros configurados pelo usuário."""
#     with st.sidebar:    
#         st.header("Parâmetros espaciais")
#         lat = st.number_input("Latitude inicial", value=-22.817100, format="%.6f")
#         lng = st.number_input("Longitude inicial", value=-47.069800, format="%.6f")
        
#         # Adicionado format="%.1f" para exibir apenas uma casa decimal (ex: 2.0, 2.5)
#         raio_km = st.slider("Raio de busca (km)", min_value=1.0, max_value=50.0, value=2.0, step=0.5, format="%.1f")
#         tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)
            
#         st.divider()
#         btn_gerar = st.button("Gerar malha e candidatos", use_container_width=True)

#         # Foram removidos os toggles de exibição de camadas, pois agora 
#         # o controle de camadas é feito nativamente dentro do mapa (LayerControl)

#         st.divider()
#         # st.header("Otimização Matemática")
#         # st.caption("Gera os lucros pré-computados e resolve o modelo MILP (CPLEX).")
#         # Botão de Otimização destacado
#         btn_otimizar = st.button("🟢 Otimizar designação", type="primary", use_container_width=True)

#     # Converte o raio de km para metros internamente antes de enviar ao app.py, 
#     # mantendo a compatibilidade com a matemática das APIs.
#     raio_metros = int(raio_km * 1000)

#     # Retorna um dicionário com todos os estados estritamente necessários para o app.py
#     return {
#         "lat": lat,
#         "lng": lng,
#         "raio": raio_metros,
#         "tamanho_grid": tamanho_grid,
#         "btn_gerar": btn_gerar,
#         "btn_otimizar": btn_otimizar
#     }








# components\sidebar.py

"""
Componente: Barra lateral de controles e parâmetros.
Suporta dois modos de varredura com a mesma lógica de busca:
  - Urbano (raio): um círculo em torno de um ponto (comportamento tradicional).
  - Rodovia: corrente de círculos ao longo do traçado (utils/rodovias.py).
"""

import os
import streamlit as st
from utils.rodovias import carregar_indice, listar_rodovias

INDEX_PATH = os.path.join("dados", "rodovias", "index.json")


def render_sidebar():
    """Renderiza a sidebar e retorna os parâmetros configurados pelo usuário."""
    with st.sidebar:
        st.header("Modo de varredura")
        modo = st.radio(
            "Como explorar a área?",
            ["Urbano (raio)", "Rodovia"],
            index=0,
            help="Urbano: círculo em torno de um ponto. Rodovia: corrente de círculos ao longo do traçado.",
        )

        st.divider()
        # Parâmetros comuns aos dois modos
        raio_km = st.slider("Raio de busca (km)", min_value=0.5, max_value=50.0, value=2.0, step=0.5, format="%.1f")
        tamanho_grid = st.number_input("Tamanho da grade (metros)", min_value=100, max_value=1000, value=800, step=100)

        cfg = {
            "modo": modo,
            "raio": int(raio_km * 1000),   # metros
            "tamanho_grid": int(tamanho_grid),
        }

        st.divider()
        if modo == "Urbano (raio)":
            st.subheader("Parâmetros espaciais")
            cfg["lat"] = st.number_input("Latitude inicial", value=-22.817100, format="%.6f")
            cfg["lng"] = st.number_input("Longitude inicial", value=-47.069800, format="%.6f")
            cfg["rodovias_sel"] = []
            cfg["fator"] = 1.0
        else:
            st.subheader("Rodovias")
            indice = {}
            if os.path.exists(INDEX_PATH):
                try:
                    indice = carregar_indice(INDEX_PATH)
                except Exception as e:
                    st.error(f"Falha ao ler o index.json: {e}")
            else:
                st.warning(f"index.json não encontrado em {INDEX_PATH}")

            estados = list(indice.keys())
            estado = st.selectbox("Estado", estados, index=0) if estados else None
            cfg["estado"] = estado

            opcoes = listar_rodovias(indice, estado) if estado else []
            nomes = [f"{o['ref']} ({o['nome']})" for o in opcoes]
            escolha = st.multiselect("Selecione as rodovias", nomes)
            cfg["rodovias_sel"] = [opcoes[nomes.index(n)] for n in escolha]

            cfg["fator"] = st.slider(
                "Sobreposição (fator do raio)", min_value=0.5, max_value=2.0, value=1.0, step=0.1,
                help="Espaço entre centros = raio × fator. Menor valor, mais sobreposição.",
            )
            # No modo rodovia o centro do mapa é calculado no app.py
            cfg["lat"] = None
            cfg["lng"] = None

        st.divider()
        cfg["btn_gerar"] = st.button("Gerar malha e candidatos", use_container_width=True)

        st.divider()
        cfg["btn_otimizar"] = st.button("🟢 Otimizar designação", type="primary", use_container_width=True)

    return cfg