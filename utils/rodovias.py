# utils/rodovias.py
# -*- coding: utf-8 -*-
"""
Leitura de rodovias e geração da "corrente de círculos" (varredura híbrida).

Ideia: em vez de varrer por um raio único em torno de um ponto, percorre-se o
traçado da rodovia colocando círculos de raio fixo espaçados ao longo do arco
(com sobreposição). Cada centro alimenta a busca circular que o dashboard já
faz (api/google_places), e o cache SQLite (malha universal) deduplica a
sobreposição entre círculos vizinhos, então o traslado não custa API dobrada.

Este módulo é isolado e testável: não depende de Streamlit nem do resto do app.
Contrato do index.json (manifesto por estado):
    {
      "SP": [
        {"ref": "BR-381", "nome": "Fernão Dias",    "arquivo": "br-381_fernao-dias.geojson"},
        {"ref": "BR-116", "nome": "Dutra",          "arquivo": "br-116_dutra.geojson"},
        {"ref": "BR-153", "nome": "Transbrasiliana","arquivo": "br-153_transbrasiliana.geojson"}
      ]
    }
Os arquivos de traçado são guardados COMPLETOS (originais); o recorte ao estado
é feito aqui, por código (interseção com o polígono do estado).
"""

import os
import json
import numpy as np
from shapely.geometry import shape, LineString, MultiLineString, GeometryCollection
from shapely.ops import linemerge, unary_union

# ── Critérios de isolamento da pista principal ─────────────────────
# Discrimina-se pela CLASSE da via (tag 'highway' do OSM), não pelo nome,
# porque muitos segmentos da pista principal vêm com name=None no OSM.
CLASSES_PRINCIPAIS = {
    "motorway", "trunk", "primary",
    "motorway_link", "trunk_link", "primary_link",
}
# Nomes que denunciam vias de serviço a descartar.
DESCARTAR_NOME = ("Marginal", "Anel", "Avenida", "Acesso", "Trevo", "Alça", "Retorno")


# ── Geometria auxiliar ─────────────────────────────────────────────
def _haversine_km(lat1, lon1, lat2, lon2):
    """Distância Haversine em km (escalares)."""
    R = 6371.0
    p = np.pi / 180.0
    a = (np.sin((lat2 - lat1) * p / 2) ** 2
         + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))


def _comprimento_km(coords):
    """Comprimento de uma polilinha [(lon,lat), ...] em km."""
    c = np.asarray(coords, dtype=float)
    if len(c) < 2:
        return 0.0
    return float(_haversine_km(c[:-1, 1], c[:-1, 0], c[1:, 1], c[1:, 0]).sum())


def _extrair_linhas(geom):
    """Extrai LineStrings de qualquer geometria (Line/MultiLine/Collection)."""
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, LineString):
        return [geom]
    if isinstance(geom, (MultiLineString, GeometryCollection)):
        out = []
        for g in geom.geoms:
            if isinstance(g, LineString) and not g.is_empty:
                out.append(g)
        return out
    return []


# ── Índice de rodovias (manifesto por estado) ──────────────────────
def carregar_indice(caminho_index):
    with open(caminho_index, encoding="utf-8") as f:
        return json.load(f)


def listar_rodovias(indice, estado):
    """Lista as rodovias que tocam um estado (para o multiselect futuro)."""
    return indice.get(estado, [])


# ── Polígono do estado (recorte) ───────────────────────────────────
def carregar_poligono_estado(caminho_geojson):
    with open(caminho_geojson, encoding="utf-8") as f:
        dados = json.load(f)
    return unary_union([shape(ft["geometry"]) for ft in dados["features"] if ft.get("geometry")])


# ── Carregar e isolar o traçado da pista principal ─────────────────
def carregar_tracado(caminho_geojson, ref, poligono_estado,
                     classes=CLASSES_PRINCIPAIS, descartar=DESCARTAR_NOME):
    """
    Filtra a pista principal por 'ref' (contido) + classe de via, descarta vias
    de serviço pelo nome, recorta ao polígono do estado e faz o merge.
    Retorna (componentes: list[LineString], km_total: float), ordenados por
    comprimento decrescente.
    """
    with open(caminho_geojson, encoding="utf-8") as f:
        dados = json.load(f)

    segs = []
    for ft in dados.get("features", []):
        g = ft.get("geometry")
        p = ft.get("properties", {}) or {}
        if not g or g.get("type") not in ("LineString", "MultiLineString"):
            continue
        if ref not in str(p.get("ref") or ""):
            continue
        if str(p.get("highway") or "") not in classes:
            continue
        nome = str(p.get("name") or "")
        if any(k in nome for k in descartar):
            continue
        segs += _extrair_linhas(shape(g))

    if not segs:
        return [], 0.0

    # Recorte ao estado
    recortadas = []
    for ln in segs:
        recortadas += _extrair_linhas(ln.intersection(poligono_estado))
    if not recortadas:
        return [], 0.0

    # Merge em componentes contínuos
    fundido = linemerge(unary_union(recortadas))
    componentes = _extrair_linhas(fundido) or ([fundido] if isinstance(fundido, LineString) else [])
    componentes.sort(key=lambda ln: _comprimento_km(list(ln.coords)), reverse=True)
    km_total = sum(_comprimento_km(list(ln.coords)) for ln in componentes)
    return componentes, km_total


# ── Corrente de círculos ───────────────────────────────────────────
def _pontos_equidistantes(coords, passo_km):
    """Emite pontos a cada passo_km ao longo da polilinha [(lon,lat), ...]."""
    if len(coords) < 2:
        return [tuple(coords[0])] if coords else []
    pontos = [tuple(coords[0])]
    dist_acum = 0.0
    proximo = passo_km
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]
        d = float(_haversine_km(lat1, lon1, lat2, lon2))
        if d <= 0:
            continue
        while dist_acum + d >= proximo:
            frac = (proximo - dist_acum) / d
            pontos.append((lon1 + (lon2 - lon1) * frac, lat1 + (lat2 - lat1) * frac))
            proximo += passo_km
        dist_acum += d
    return pontos


def gerar_cadeia_circulos(componentes, raio_m, fator_espacamento=1.0,
                          min_componente_mult=2.0):
    """
    Gera os centros dos círculos ao longo dos componentes do traçado.
      passo entre centros = raio_m * fator_espacamento  (fator=1.0 -> forte sobreposição)
    Varre todos os componentes cujo comprimento >= min_componente_mult * passo,
    ignorando cotos pequenos. O raio grande cobre a pista paralela (pistas duplas),
    e o cache SQLite deduplica a sobreposição, então varrer tudo não custa API extra.
    Retorna (centros, passo_km): centros = [{ordem, componente, lat, lng}, ...].
    """
    passo_km = (raio_m * fator_espacamento) / 1000.0
    limite = min_componente_mult * passo_km
    centros = []
    ordem = 0
    for ci, ln in enumerate(componentes):
        coords = list(ln.coords)
        if _comprimento_km(coords) < limite:
            continue
        for lon, lat in _pontos_equidistantes(coords, passo_km):
            centros.append({"ordem": ordem, "componente": ci,
                            "lat": round(lat, 6), "lng": round(lon, 6)})
            ordem += 1
    return centros, passo_km


# ── Teste de fumaça (offline, com arquivos reais) ──────────────────
if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads"
    SP = carregar_poligono_estado(os.path.join(base, "1789641771967_sp_estado.geojson"))

    print("=== BR-381 (export.geojson, original completo) ===")
    comps, km = carregar_tracado(os.path.join(base, "1789643416240_export.geojson"), "BR-381", SP)
    print(f"componentes: {len(comps)} | km dentro de SP: {km:.1f}")
    if comps:
        print(f"maior componente: {_comprimento_km(list(comps[0].coords)):.1f} km")
    centros, passo = gerar_cadeia_circulos(comps, raio_m=2000, fator_espacamento=1.0)
    print(f"passo entre centros: {passo:.2f} km | centros gerados: {len(centros)}")
    # sanidade: todos os centros caem dentro de SP?
    from shapely.geometry import Point
    dentro = sum(SP.buffer(0.01).contains(Point(c['lng'], c['lat'])) for c in centros)
    print(f"centros dentro de SP: {dentro}/{len(centros)}")
    print("primeiros 3:", centros[:3])

    print("\n=== BR-116 (dutra_sp.geojson, ref combinado SP-060;BR-116) ===")
    comps2, km2 = carregar_tracado(os.path.join(base, "1789644180434_dutra_sp.geojson"), "BR-116", SP)
    print(f"componentes: {len(comps2)} | km dentro de SP: {km2:.1f}")
    centros2, passo2 = gerar_cadeia_circulos(comps2, raio_m=2000, fator_espacamento=1.0)
    print(f"centros gerados: {len(centros2)}")