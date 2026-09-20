# utils/potencial.py
# -*- coding: utf-8 -*-
"""
Motor do Potencial de Implantação (IP).

Calcula, para cada candidato, um score normalizado em [1, 5]:

  Rodovia:  IP = 0.70*x1 + 0.20*x2 + 0.10*x3 + x4
  Urbano:   IP = x3 + x4            (só critérios de POIs + vizinhos)

  x1 tráfego (VMD do sensor mais próximo)      -> 1..5
  x2 população (município mais próximo)        -> 1..5
  x3 nível de serviço (variedade de POIs perto)-> 1..5
  x4 efeito dos eletropostos vizinhos          -> -5..+4

Normalização determinística (Opção A): a parte ponderada de x1..x3 fica em [1,5]
e x4 em [-5,+4], logo o IP bruto sempre cai em [-4, 9]. Reescalamos essa faixa
teórica FIXA para [1,5] e recortamos. Assim o score não depende do conjunto de
candidatos (um mesmo lugar dá sempre o mesmo valor) e o corte de 3.0 é estável.
"""

import os
import glob
import json
import math
import numpy as np
import pandas as pd

# ── Parâmetros (alinháveis com o teste_v2; recalibráveis) ──────────
PESOS = (0.70, 0.20, 0.10)               # pesos de x1, x2, x3 (somam 1.0)
ALFA_KM, BETA_KM = 15.0, 50.0            # faixas de x4 (efeito das existentes)

# Faixas fixas (thresholds) para categorizar em 1..5.
# BINS_X1: VMD de veículos leves. BINS_X2: população do município.
BINS_X1 = [3000, 6000, 10000, 20000]     # < : 1 | 2 | 3 | 4 | >= último: 5
BINS_X2 = [5000, 10000, 20000, 50000]

# Faixa teórica do IP para a normalização determinística.
IP_MIN, IP_MAX = -4.0, 9.0


# ── Utilidades ─────────────────────────────────────────────────────
def _haversine_km(lat0, lon0, lats, lons):
    R = 6371.0
    p = math.pi / 180.0
    lats = np.asarray(lats, float); lons = np.asarray(lons, float)
    a = (np.sin((lats - lat0) * p / 2) ** 2
         + math.cos(lat0 * p) * np.cos(lats * p) * np.sin((lons - lon0) * p / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(a))

def _categoria(valor, bins):
    """Devolve 1..5 conforme quantos limiares 'valor' ultrapassa."""
    c = 1
    for b in bins:
        if valor >= b:
            c += 1
    return min(c, 5)

def _normalizar_ip(ip):
    """Reescala IP de [IP_MIN, IP_MAX] para [1, 5] e recorta."""
    s = 1.0 + 4.0 * (ip - IP_MIN) / (IP_MAX - IP_MIN)
    return float(min(5.0, max(1.0, s)))


# ── Carregadores de dados ──────────────────────────────────────────
def carregar_sensores(dir_sensores, tipos=("Veículo leve",)):
    """Lê todos os CSV de sensores (latin-1, sep=';') e consolida um VMD por sensor.
    Retorna DataFrame [identificador, rodovia, lat, lon, vmd]."""
    arquivos = sorted(glob.glob(os.path.join(dir_sensores, "*.csv")))
    frames = []
    for arq in arquivos:
        try:
            df = pd.read_csv(arq, sep=";", encoding="latin-1")
            frames.append(df)
        except Exception as e:
            print(f"Sensor: falha ao ler {arq}: {e}")
    if not frames:
        return pd.DataFrame(columns=["identificador", "rodovia", "lat", "lon", "vmd"])
    dados = pd.concat(frames, ignore_index=True)
    if tipos:
        dados = dados[dados["tipo_de_veiculo"].isin(tipos)]
    g = dados.groupby("identificador").agg(
        rodovia=("rodovia", "first"),
        lat=("latitude", "first"),
        lon=("longitude", "first"),
        vol=("volume_total", "sum"),
        ndias=("data_de_passagem", "nunique"),
    ).reset_index()
    g["ndias"] = g["ndias"].clip(lower=1)
    g["vmd"] = g["vol"] / g["ndias"]
    return g[["identificador", "rodovia", "lat", "lon", "vmd"]]

def carregar_municipios(caminho_json):
    """Lê municipios_sp.json -> DataFrame [municipio, lat, lon, populacao]."""
    with open(caminho_json, encoding="utf-8") as f:
        dados = json.load(f)
    return pd.DataFrame(dados)


# ── Critérios ──────────────────────────────────────────────────────
def _valor_vizinho_mais_proximo(la, lo, lats, lons, valores):
    d = _haversine_km(la, lo, lats, lons)
    return valores[int(np.argmin(d))], float(d.min())

def calcular_x1(cand, sensores):
    if sensores is None or sensores.empty:
        return np.ones(len(cand))  # sem dado -> neutro mínimo
    slat = sensores["lat"].to_numpy(); slon = sensores["lon"].to_numpy(); svmd = sensores["vmd"].to_numpy()
    out = []
    for la, lo in zip(cand["Lat_Centroide"], cand["Lng_Centroide"]):
        vmd, _ = _valor_vizinho_mais_proximo(la, lo, slat, slon, svmd)
        out.append(_categoria(vmd, BINS_X1))
    return np.array(out, float)

def calcular_x2(cand, municipios):
    if municipios is None or municipios.empty:
        return np.ones(len(cand))
    mlat = municipios["lat"].to_numpy(); mlon = municipios["lon"].to_numpy(); mpop = municipios["populacao"].to_numpy()
    out = []
    for la, lo in zip(cand["Lat_Centroide"], cand["Lng_Centroide"]):
        pop, _ = _valor_vizinho_mais_proximo(la, lo, mlat, mlon, mpop)
        out.append(_categoria(pop, BINS_X2))
    return np.array(out, float)

def calcular_x3(cand, df_pois, raio_m=800):
    """Nível de serviço pela variedade de categorias de POI perto do candidato.
    0 categorias -> 1 | 1 -> 2 | 2 -> 4 | 3 -> 5."""
    mapa = {0: 1, 1: 2, 2: 4, 3: 5}
    if df_pois is None or df_pois.empty:
        return np.ones(len(cand))
    plat = df_pois["Lat"].to_numpy(); plon = df_pois["Lng"].to_numpy()
    pcat = df_pois["Categoria"].to_numpy()
    out = []
    for la, lo in zip(cand["Lat_Centroide"], cand["Lng_Centroide"]):
        d = _haversine_km(la, lo, plat, plon)
        perto = d <= (raio_m / 1000.0)
        n = len(set(pcat[perto])) if perto.any() else 0
        out.append(mapa.get(n, 5))
    return np.array(out, float)

def calcular_x4(cand, eletropostos, alfa_km=ALFA_KM, beta_km=BETA_KM):
    """Efeito das estações existentes (vizinhas). d<=alfa: penalidade -5..0;
    alfa<d<=beta: +4 (faixa ideal); d>beta: 0."""
    lats, lons = [], []
    for e in (eletropostos or []):
        loc = e.get("location", {}) or {}
        if "latitude" in loc and "longitude" in loc:
            lats.append(loc["latitude"]); lons.append(loc["longitude"])
    if not lats:
        return np.zeros(len(cand))
    lats = np.array(lats); lons = np.array(lons)
    out = []
    for la, lo in zip(cand["Lat_Centroide"], cand["Lng_Centroide"]):
        d = float(_haversine_km(la, lo, lats, lons).min())
        if d <= alfa_km:
            out.append(-5.0 * (1.0 - d / alfa_km))   # -5 em d=0, 0 em d=alfa
        elif d <= beta_km:
            out.append(4.0)
        else:
            out.append(0.0)
    return np.array(out, float)


# ── Cálculo do potencial ───────────────────────────────────────────
def calcular_potencial(cand, df_pois, eletropostos, sensores=None, municipios=None,
                       modo="rodovia", raio_x3_m=800):
    """Adiciona colunas x1..x4, IP e score_potencial (em [1,5]) ao DataFrame de candidatos."""
    cand = cand.copy()
    if cand.empty:
        for c in ["x1", "x2", "x3", "x4", "IP", "score_potencial"]:
            cand[c] = []
        return cand

    x3 = calcular_x3(cand, df_pois, raio_x3_m)
    x4 = calcular_x4(cand, eletropostos)

    if modo == "rodovia":
        x1 = calcular_x1(cand, sensores)
        x2 = calcular_x2(cand, municipios)
        base = PESOS[0] * x1 + PESOS[1] * x2 + PESOS[2] * x3
    else:  # urbano: só critérios de POIs
        x1 = np.full(len(cand), np.nan)
        x2 = np.full(len(cand), np.nan)
        base = x3

    ip = base + x4
    cand["x1"], cand["x2"], cand["x3"], cand["x4"] = x1, x2, x3, x4
    cand["IP"] = ip
    cand["score_potencial"] = [round(_normalizar_ip(v), 2) for v in ip]
    # Mantém compatibilidade: o restante do app usa Score_Estimado como score base.
    cand["Score_Estimado"] = cand["score_potencial"]
    return cand

def filtrar_por_potencial(cand, corte=3.0):
    """Mantém apenas candidatos com score_potencial >= corte."""
    if cand is None or cand.empty or "score_potencial" not in cand:
        return cand
    return cand[cand["score_potencial"] >= corte].reset_index(drop=True)


# ── Teste offline com dados reais ──────────────────────────────────
if __name__ == "__main__":
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads"
    sens = carregar_sensores(base)  # lê os CSV que estiverem na pasta
    muni = carregar_municipios(os.path.join(base, "1789857346191_municipios_sp.json"))
    print("sensores:", len(sens), "| municípios:", len(muni))

    # candidatos sintéticos perto da BR-116 (SAT01 ~ -23.71,-46.88) e um urbano
    cand = pd.DataFrame({
        "Lat_Centroide": [-23.713, -24.214, -23.55],
        "Lng_Centroide": [-46.878, -47.368, -46.63],
    })
    pois = pd.DataFrame({
        "Lat": [-23.7131, -23.7132, -23.5501], "Lng": [-46.8781, -46.8782, -46.6301],
        "Categoria": ["Varejo e lazer", "Transporte", "Serviços e saúde"],
    })
    evs = [{"location": {"latitude": -23.60, "longitude": -46.80}}]  # ~a algumas dezenas de km

    r = calcular_potencial(cand, pois, evs, sens, muni, modo="rodovia")
    print("\n-- modo rodovia --")
    print(r[["Lat_Centroide", "x1", "x2", "x3", "x4", "IP", "score_potencial"]].to_string(index=False))
    print("score em [1,5]?", bool((r["score_potencial"].between(1, 5)).all()))
    print("acima de 3.0:", int((r["score_potencial"] >= 3.0).sum()), "de", len(r))

    u = calcular_potencial(cand, pois, evs, modo="urbano")
    print("\n-- modo urbano --")
    print(u[["Lat_Centroide", "x3", "x4", "IP", "score_potencial"]].to_string(index=False))
    print("score em [1,5]?", bool((u["score_potencial"].between(1, 5)).all()))