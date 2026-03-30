"""
Componente: renderização interativa do mapa espacial
"""

import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

def renderizar_mapa_completo(lat, lng, raio, df_pois, df_cand, grid, mostrar_heatmap, mostrar_eletropostos, dados_eletropostos, categorias_pois):
    """Constrói e renderiza o mapa com todas as camadas selecionadas."""
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
        cat_info = categorias_pois[row['Categoria']]
        folium.CircleMarker(
            [row['Lat'], row['Lng']],
            radius=4,
            color=cat_info['color'], fill=True, fillOpacity=0.8,
            tooltip=f"{row['Nome']} ({row['Tipo']}) - Peso: {row['Peso']:.1f}"
        ).add_to(mapa)

    # --- CAMADA: ELETROPOSTOS (Concorrência) ---
    if mostrar_eletropostos and dados_eletropostos:
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
                    radius=7, 
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