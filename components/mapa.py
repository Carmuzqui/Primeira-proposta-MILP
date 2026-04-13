# components\mapa.py

"""
Componente: Renderização interativa do mapa espacial com Legenda/Controle de Camadas Integrado
"""

import folium
import math
from folium.plugins import HeatMap
from folium.features import DivIcon
from streamlit_folium import st_folium

def renderizar_mapa_completo(lat, lng, raio, df_pois, df_cand, grid, dados_eletropostos, categorias_pois, nodos_otimizados=None):
    """Constrói e renderiza o mapa com controle estrito de camadas, ícones e auto-zoom."""
    
    if nodos_otimizados is None:
        nodos_otimizados = []

    # Flag para saber se já rodamos o otimizador
    otimizacao_rodou = len(nodos_otimizados) > 0

    if raio > 0:
        zoom_calculado = 14.5 - math.log2(raio / 2000.0)
        zoom_start = int(round(zoom_calculado))
    else:
        zoom_start = 14

    # 1. Instância base do mapa (SEM FUNDO INICIALMENTE)
    mapa = folium.Map(location=[lat, lng], zoom_start=zoom_start, tiles=None)
    
    # 2. ADICIONAMOS O FUNDO E OCULTAMOS DO MENU (control=False)
    folium.TileLayer(
        tiles='CartoDB positron',
        name='Mapa Base',
        control=False  # Oculta o fundo do controle de camadas
    ).add_to(mapa)
    
    # Criar um painel personalizado para garantir que os POIs fiquem sempre por cima da malha/heatmap
    folium.map.CustomPane('pois_top_pane', z_index=650).add_to(mapa)

    # ==========================================
    # 3. CRIAÇÃO DOS GRUPOS DE CAMADAS (Com HTML na Legenda)
    # ==========================================
    
    # POIs separados por categoria
    fg_pois_dict = {
        "Varejo e lazer": folium.FeatureGroup(name="<i class='fa fa-circle' style='color:blue; margin-right: 4px;'></i> Varejo e lazer", show=True),
        "Transporte": folium.FeatureGroup(name="<i class='fa fa-circle' style='color:red; margin-right: 4px;'></i> Transporte", show=True),
        "Serviços e saúde": folium.FeatureGroup(name="<i class='fa fa-circle' style='color:purple; margin-right: 4px;'></i> Serviços e saúde", show=True)
    }

    # Ícone complexo do eletroposto formatado para caber no menu
    icone_ev_html = "<div style='display:inline-flex; align-items:center; justify-content:center; background-color:#2e7d32; border:1px solid cyan; border-radius:50%; width:14px; height:14px; margin-right:4px; box-shadow: 0 0 2px rgba(0,0,0,0.5);'><i class='fa fa-bolt' style='color:cyan; font-size:8px;'></i></div> Eletroposto"
    fg_existentes = folium.FeatureGroup(name=icone_ev_html, show=True)
    
    # Malha e Heatmap
    fg_grid = folium.FeatureGroup(name="<div style='width:12px; height:12px; background-color:lightblue; display:inline-block; border:1px solid blue; margin-right: 4px;'></div> Malha de análise", show=False)
    fg_heatmap = folium.FeatureGroup(name="<span style='background: linear-gradient(to right, blue, lime, red); width: 14px; height: 14px; display: inline-block; margin-right: 4px; border-radius: 2px;'></span> Demanda estimada", show=False)

    # Nodos de Otimização
    if otimizacao_rodou:
        fg_designados = folium.FeatureGroup(name="<i class='fa fa-check' style='color:green; margin-right: 4px;'></i> Candidato designado", show=True)
        fg_rejeitados = folium.FeatureGroup(name="<i class='fa fa-wrench' style='color:gray; margin-right: 4px;'></i> Nodo rejeitado", show=False) 
    else:
        fg_candidatos = folium.FeatureGroup(name="<i class='fa fa-wrench' style='color:black; margin-right: 4px;'></i> Nodo candidato", show=True)

    # ==========================================
    # 4. ADICIONAR ELEMENTOS AOS SEUS RESPECTIVOS GRUPOS
    # ==========================================

    # --- Área de Busca e Centro (Direto no mapa base) ---
    folium.Circle([lat, lng], radius=raio, color='gray', fill=False, dash_array='5, 5', weight=2).add_to(mapa)
    folium.CircleMarker([lat, lng], radius=5, color='black', fill=True, popup="Centro da Busca").add_to(mapa)

    # --- HeatMap ---
    if not df_pois.empty:
        heat_data = [[row['Lat'], row['Lng'], row['Peso']] for index, row in df_pois.iterrows()]
        HeatMap(
            heat_data,
            name="Demanda Gravitacional",
            radius=25, blur=15, min_opacity=0.4,
            gradient={0.2: 'blue', 0.6: 'lime', 1.0: 'red'} 
        ).add_to(fg_heatmap)

    # --- POIs (Pontos de Interesse) ---
    for _, row in df_pois.iterrows():
        cat = row['Categoria']
        cat_info = categorias_pois[cat]
        folium.CircleMarker(
            [row['Lat'], row['Lng']],
            radius=4,
            color=cat_info['color'], fill=True, fillOpacity=0.9,
            pane='pois_top_pane',
            tooltip=f"{row['Nome']} ({row['Tipo']}) - Peso: {row['Peso']:.1f}"
        ).add_to(fg_pois_dict[cat]) 

    # --- Nodos Candidatos / Designados / Grade ---
    if df_cand is not None and not df_cand.empty:
        for index, row in df_cand.iterrows():
            i, j = row['cell_i'], row['cell_j']
            c_lat_min = grid['lat_min'] + (i * grid['lat_step'])
            c_lat_max = c_lat_min + grid['lat_step']
            c_lng_min = grid['lng_min'] + (j * grid['lng_step'])
            c_lng_max = c_lng_min + grid['lng_step']
            
            folium.Rectangle(
                bounds=[[c_lat_min, c_lng_min], [c_lat_max, c_lng_max]],
                color='blue', weight=1, fill=True, fillColor='blue', fillOpacity=0.05
            ).add_to(fg_grid)
            
            lat_nodo = row['Lat_Centroide']
            lng_nodo = row['Lng_Centroide']
            
            candidato_id = f"C{index}"
            foi_selecionado = candidato_id in nodos_otimizados
            
            if otimizacao_rodou:
                if foi_selecionado:
                    cor_marcador = 'green'
                    cor_icone = 'white'
                    icone_marcador = 'check'
                    titulo_popup = "Designado"
                else:
                    cor_marcador = 'lightgray'
                    cor_icone = 'gray'
                    icone_marcador = 'wrench'
                    titulo_popup = "Rejeitado"
            else:
                cor_marcador = 'black'
                cor_icone = 'white'
                icone_marcador = 'wrench'
                titulo_popup = "Nodo candidato"
            
            popup_nodo_html = f"""
            <div style="font-family: Arial, sans-serif; width: 210px;">
                <h4 style="margin: 0 0 8px 0; color: {cor_marcador if cor_marcador != 'lightgray' else 'gray'}; border-bottom: 1px solid #ccc; padding-bottom: 5px;">{titulo_popup}</h4>
                <p style="margin: 5px 0; font-size: 12px;"><b>POIs na área:</b> {row['Qtd_POIs']}</p>
                <p style="margin: 5px 0; font-size: 12px;"><b>Score base:</b> {row['Score_Estimado']:.1f}</p>
                
                <div style="margin-top: 12px; display: flex; justify-content: space-between;">
                    <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat_nodo},{lng_nodo}" target="_blank" style="font-size: 11px; color: #fff; background-color: #4285F4; padding: 5px 8px; text-decoration: none; border-radius: 4px; text-align: center; flex: 1; margin-right: 4px;">Street View</a>
                    <a href="https://www.google.com/maps/search/?api=1&query={lat_nodo},{lng_nodo}" target="_blank" style="font-size: 11px; color: #fff; background-color: #0F9D58; padding: 5px 8px; text-decoration: none; border-radius: 4px; text-align: center; flex: 1; margin-left: 4px;">Mapa</a>
                </div>
            </div>
            """
            
            marcador = folium.Marker(
                [lat_nodo, lng_nodo],
                popup=folium.Popup(popup_nodo_html, max_width=250),
                tooltip=titulo_popup,
                icon=folium.Icon(color=cor_marcador, icon_color=cor_icone, icon=icone_marcador, prefix='fa')
            )

            if otimizacao_rodou:
                if foi_selecionado:
                    marcador.add_to(fg_designados)
                else:
                    marcador.add_to(fg_rejeitados)
            else:
                marcador.add_to(fg_candidatos)

    # --- Eletropostos Concorrentes ---
    if dados_eletropostos:
        for posto in dados_eletropostos:
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
                
                # --- RECUPERANDO A LÓGICA DE DETALHES DE CONECTORES ---
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

                # --- LÓGICA DO BOTÃO WEB (Oculta se não houver site) ---
                botao_web_html = ""
                if website != '#':
                    botao_web_html = f'<a href="{website}" target="_blank" style="font-size: 12px; color: #fff; background-color: #2e7d32; padding: 4px 8px; text-decoration: none; border-radius: 4px;">Web</a>'

                # --- HTML COMPLETO DO POPUP (Com Endereço limpo) ---
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width: 280px;">
                    <h4 style="margin: 0 0 8px 0; color: #2e7d32; border-bottom: 1px solid #ccc; padding-bottom: 5px;">{nome}</h4>
                    <p style="margin: 0 0 10px 0; font-size: 13px; font-weight: bold; color: #e65100;">{estrelas}</p>
                    <p style="margin: 5px 0; font-size: 12px;"><b>Endereço:</b><br>{endereco}</p>                
                    <p style="margin: 5px 0; font-size: 12px;"><b>📞 Contato:</b> {telefone}</p>
                    <div style="background-color: #e8f5e9; padding: 8px; border-radius: 5px; margin: 10px 0;">{ev_info}</div>
                    <p style="margin: 5px 0; font-size: 12px; color: #d84315;"><b>Distância do centro:</b> {distancia:.2f} km</p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 10px; color: #666;">{p_lat:.5f}, {p_lng:.5f}</span>
                        {botao_web_html}
                    </div>
                </div>
                """
                
                html_eletroposto = """
                <div style="background-color: #2e7d32; border: 2px solid cyan; border-radius: 50%; width: 18px; height: 18px; display: flex; justify-content: center; align-items: center; box-shadow: 0 0 4px rgba(0,0,0,0.6);">
                    <i class="fa fa-bolt" style="color: cyan; font-size: 10px; margin-top: 1px;"></i>
                </div>
                """
                folium.Marker(
                    [p_lat, p_lng],
                    icon=DivIcon(html=html_eletroposto, icon_size=(18, 18), icon_anchor=(10, 10)),
                    popup=folium.Popup(popup_html, max_width=400),
                    tooltip=f"{nome}"
                ).add_to(fg_existentes)

    # ==========================================
    # 5. ANEXAR GRUPOS AO MAPA NA ORDEM DA LEGENDA
    # ==========================================
    fg_pois_dict["Varejo e lazer"].add_to(mapa)
    fg_pois_dict["Transporte"].add_to(mapa)
    fg_pois_dict["Serviços e saúde"].add_to(mapa)
    fg_existentes.add_to(mapa)
    fg_grid.add_to(mapa)

    if otimizacao_rodou:
        fg_designados.add_to(mapa)
        fg_rejeitados.add_to(mapa)
    else:
        fg_candidatos.add_to(mapa)

    fg_heatmap.add_to(mapa)

    # ==========================================
    # 6. ATIVAR CONTROLE INTERATIVO 
    # ==========================================
    folium.LayerControl(position='bottomright', collapsed=False).add_to(mapa)
        
    st_folium(mapa, use_container_width=True, height=850, returned_objects=[])