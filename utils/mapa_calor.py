# """
# utils/mapa_calor.py
# Processa as polilinhas do Google, soma os fluxos dos trechos sobrepostos
# e renderiza o mapa de calor rodoviário.
# """

# import folium
# import polyline
# import branca.colormap as cm

# def processar_e_somar_segmentos(df_rotas):
#     """
#     Decodifica as polilinhas e soma os fluxos de trechos rodoviários que se sobrepõem.
#     """
#     segmentos = {}
    
#     for _, row in df_rotas.iterrows():
#         fluxo = row['Fluxo']
#         linha_codificada = row['Polyline']
        
#         # Decodifica a string do Google para uma lista de (lat, lng)
#         coords = polyline.decode(linha_codificada)
        
#         # Arredonda as coordenadas para 3 casas decimais (margem de ~110 metros)
#         # Isso faz o "snap" (encaixe) de rotas que passam pela mesma rodovia
#         coords_arredondadas = [(round(lat, 3), round(lng, 3)) for lat, lng in coords]
        
#         # Cria segmentos de reta (Ponto A -> Ponto B)
#         for i in range(len(coords_arredondadas) - 1):
#             p1 = coords_arredondadas[i]
#             p2 = coords_arredondadas[i+1]
            
#             # Ordenar os pontos garante que viagens de "ida" e "volta" no mesmo trecho sejam somadas juntas
#             segmento = tuple(sorted((p1, p2)))
            
#             if segmento not in segmentos:
#                 segmentos[segmento] = 0
#             # Soma o fluxo neste trecho específico
#             segmentos[segmento] += fluxo
            
#     return segmentos

# def gerar_mapa_calor_rotas(df_rotas):
#     """
#     Gera o mapa Folium com os trechos somados e cores baseadas no volume de tráfego.
#     """
#     if df_rotas.empty:
#         return None
        
#     # 1. Processar e somar os trechos locais
#     segmentos_somados = processar_e_somar_segmentos(df_rotas)
    
#     # 2. Descobrir o centro do mapa (usando o meio da primeira rota para centralizar a câmera)
#     primeira_rota = polyline.decode(df_rotas.iloc[0]['Polyline'])
#     centro_lat = primeira_rota[len(primeira_rota)//2][0]
#     centro_lng = primeira_rota[len(primeira_rota)//2][1]
    
#     # Usar um fundo escuro (dark_matter) faz as cores do fluxo brilharem muito mais
#     mapa = folium.Map(location=[centro_lat, centro_lng], zoom_start=5, tiles='CartoDB dark_matter')
    
#     # 3. Criar uma escala de cores (Azul para rotas vazias, Vermelho para engarrafadas)
#     max_fluxo = max(segmentos_somados.values()) if segmentos_somados else 1
#     min_fluxo = min(segmentos_somados.values()) if segmentos_somados else 0
    
#     colormap = cm.LinearColormap(
#         colors=['#0088ff', '#00ff00', '#ffff00', '#ff8800', '#ff0000'],
#         vmin=min_fluxo,
#         vmax=max_fluxo,
#         caption='Fluxo total de veículos no trecho'
#     )
#     mapa.add_child(colormap)
    
#     # 4. Desenhar os segmentos agregados no mapa
#     for segmento, fluxo in segmentos_somados.items():
#         (p1, p2) = segmento
        
#         # A cor vem do fluxo total calculado para este trecho específico
#         cor = colormap(fluxo)
        
#         # Ajustamos levemente a espessura para dar ênfase visual aos maiores fluxos
#         peso_linha = 2.5 + (fluxo / max_fluxo) * 4
        
#         # Popup com o total exato ao clicar, como você solicitou
#         popup_html = f"""
#         <div style='width: 160px; font-family: Arial;'>
#             <h4 style='margin-bottom: 5px; color: #333;'>Trecho Rodoviário</h4>
#             Fluxo Acumulado:<br>
#             <b style='font-size: 16px; color: {cor};'>{fluxo:,} veículos</b>
#         </div>
#         """
        
#         folium.PolyLine(
#             locations=[p1, p2],
#             color=cor,
#             weight=peso_linha,
#             opacity=0.85,
#             popup=folium.Popup(popup_html, max_width=200),
#             tooltip=f"Fluxo: {fluxo:,} veículos"
#         ).add_to(mapa)
        
#     return mapa












"""
utils/mapa_calor.py
Processa as polilinhas do Google, soma os fluxos dos trechos sobrepostos
e renderiza o mapa de calor rodoviário com suporte a temas claro/escuro.
"""

import folium
import polyline
import branca.colormap as cm

def processar_e_somar_segmentos(df_rotas):
    """
    Decodifica as polilinhas e soma os fluxos de trechos rodoviários que se sobrepõem.
    """
    segmentos = {}
    
    for _, row in df_rotas.iterrows():
        fluxo = row['Fluxo']
        linha_codificada = row['Polyline']
        
        # Decodifica a string do Google para uma lista de (lat, lng)
        coords = polyline.decode(linha_codificada)
        
        # Arredonda as coordenadas para 3 casas decimais (margem de ~110 metros)
        # Isso faz o "snap" (encaixe) de rotas que passam pela mesma rodovia
        coords_arredondadas = [(round(lat, 3), round(lng, 3)) for lat, lng in coords]
        
        # Cria segmentos de reta (Ponto A -> Ponto B)
        for i in range(len(coords_arredondadas) - 1):
            p1 = coords_arredondadas[i]
            p2 = coords_arredondadas[i+1]
            
            # Ordenar os pontos garante que viagens de "ida" e "volta" no mesmo trecho sejam somadas juntas
            segmento = tuple(sorted((p1, p2)))
            
            if segmento not in segmentos:
                segmentos[segmento] = 0
            # Soma o fluxo neste trecho específico
            segmentos[segmento] += fluxo
            
    return segmentos

def gerar_mapa_calor_rotas(df_rotas, tema='escuro'):
    """
    Gera o mapa Folium com os trechos somados e cores baseadas no volume de tráfego.
    Aceita tema='escuro' (padrão) ou tema='claro'.
    """
    if df_rotas.empty:
        return None
        
    # 1. Processar e somar os trechos locais
    segmentos_somados = processar_e_somar_segmentos(df_rotas)
    
    # 2. Descobrir o centro do mapa (usando o meio da primeira rota para centralizar a câmera)
    primeira_rota = polyline.decode(df_rotas.iloc[0]['Polyline'])
    centro_lat = primeira_rota[len(primeira_rota)//2][0]
    centro_lng = primeira_rota[len(primeira_rota)//2][1]
    
    # Configurar o tipo de mapa e a cor do texto da legenda consoante o tema
    if tema == 'escuro':
        tiles = 'CartoDB dark_matter'
        cor_texto_legenda = 'white'
    else:
        tiles = 'CartoDB positron'
        cor_texto_legenda = 'black'
    
    mapa = folium.Map(location=[centro_lat, centro_lng], zoom_start=5, tiles=tiles)
    
    # 3. Criar uma escala de cores (Azul para rotas vazias, Vermelho para engarrafadas)
    max_fluxo = max(segmentos_somados.values()) if segmentos_somados else 1
    min_fluxo = min(segmentos_somados.values()) if segmentos_somados else 0
    
    colormap = cm.LinearColormap(
        colors=['#0088ff', '#00ff00', '#ffff00', '#ff8800', '#ff0000'],
        vmin=min_fluxo,
        vmax=max_fluxo,
        caption='Fluxo total de veículos no trecho'
    )
    mapa.add_child(colormap)
    
    # --- INJEÇÃO DE CSS PARA CORRIGIR A LEGENDA ---
    # Altera a cor do texto para contrastar com o fundo e desce o título (caption) para evitar sobreposição
    css_legenda = f"""
    <style>
        .leaflet-control svg text {{
            fill: {cor_texto_legenda} !important;
        }}
        /* Alvo específico no título da legenda para o afastar da barra de cores */
        .leaflet-control svg text.caption {{
            transform: translateY(8px);
        }}
        /* Dá um pouco mais de altura ao SVG para o texto não ficar cortado em baixo */
        .leaflet-control svg {{
            padding-bottom: 12px;
        }}
    </style>
    """
    mapa.get_root().html.add_child(folium.Element(css_legenda))
    
    # 4. Desenhar os segmentos agregados no mapa
    for segmento, fluxo in segmentos_somados.items():
        (p1, p2) = segmento
        
        # A cor vem do fluxo total calculado para este trecho específico
        cor = colormap(fluxo)
        
        # Ajustamos levemente a espessura para dar ênfase visual aos maiores fluxos
        peso_linha = 2.5 + (fluxo / max_fluxo) * 4
        
        # Popup com o total exato ao clicar (mantemos o texto escuro aqui pois o fundo do popup é branco)
        popup_html = f"""
        <div style='width: 160px; font-family: Arial;'>
            <h4 style='margin-bottom: 5px; color: #333;'>Trecho Rodoviário</h4>
            Fluxo Acumulado:<br>
            <b style='font-size: 16px; color: {cor};'>{fluxo:,} veículos</b>
        </div>
        """
        
        folium.PolyLine(
            locations=[p1, p2],
            color=cor,
            weight=peso_linha,
            opacity=0.85,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"Fluxo: {fluxo:,} veículos"
        ).add_to(mapa)
        
    return mapa