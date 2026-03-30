"""
Simulador de Atractividad e Canibalização para Eletropostos
Gera a tabela de lucros/retornos pré-computados R_c(S_c) para o solver CPLEX.
"""

import math
import itertools
import pandas as pd
from typing import List, Dict

def _distancia_rua_aproximada(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula a distância Haversine e aplica um fator de tortuosidade (1.3) para simular ruas."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist_linear = R * c
    return dist_linear * 1.3 # Fator de tortuosidade urbano padrão

def pré_computar_cenarios(df_cand: pd.DataFrame, dados_evs: List[Dict], raio_influencia_m: int = 1500, max_vizinhos: int = 4):
    """
    Calcula a atractividade líquida de cada candidato c sob todas as configurações possíveis de seus vizinhos.
    Retorna uma lista de dicionários pronta para alimentar o CPLEX.
    """
    if df_cand.empty:
        return []

    # 1. PARÂMETROS DO MODELO DE ATRACTIVIDADE
    BARRERA_VIABILIDADE = 20.0  # Score mínimo para um nodo "se pagar" (evita que todos sejam positivos)
    FATOR_PENALIDADE_EV_REAL = 0.5 # Peso do impacto da concorrência real
    FATOR_CANIBALIZACAO = 0.4      # Quanto % da demanda um vizinho pode "roubar"

    cenarios_cplex = []

    # Converter os candidatos para um formato iterável com IDs únicos
    candidatos = []
    for idx, row in df_cand.iterrows():
        candidatos.append({
            'id': f"C{idx}",
            'lat': row['Lat_Centroide'],
            'lng': row['Lng_Centroide'],
            'score_base': row['Score_Estimado']
        })

    for c in candidatos:
        # --- A. PENALIDADE DE CONCORRÊNCIA REAL (Eletropostos existentes) ---
        penalidade_existentes = 0
        for ev in dados_evs:
            if 'location' in ev:
                dist = _distancia_rua_aproximada(c['lat'], c['lng'], ev['location']['latitude'], ev['location']['longitude'])
                if dist <= raio_influencia_m:
                    # Inversamente proporcional: mais perto = maior penalidade
                    forca_penalidade = 1.0 - (dist / raio_influencia_m)
                    # Pode ser aprimorado multiplicando pelos conectores/kW do EV real
                    penalidade_existentes += (c['score_base'] * FATOR_PENALIDADE_EV_REAL * forca_penalidade)

        # Retorno se operasse sozinho no mundo ideal (Pode ser negativo!)
        R_c_proprio = c['score_base'] - BARRERA_VIABILIDADE - penalidade_existentes

        # --- B. ENCONTRAR VIZINHOS CANDIDATOS (Com duplo filtro) ---
        vizinhos_potenciais = []
        for outro_c in candidatos:
            if c['id'] != outro_c['id']:
                dist = _distancia_rua_aproximada(c['lat'], c['lng'], outro_c['lat'], outro_c['lng'])
                if dist <= raio_influencia_m: # Filtro 1: Distância máxima
                    impacto = c['score_base'] * FATOR_CANIBALIZACAO * (1.0 - (dist / raio_influencia_m))
                    vizinhos_potenciais.append({
                        'id': outro_c['id'],
                        'dist': dist,
                        'impacto': impacto
                    })

        # Filtro 2: Limite máximo de vizinhos (pegar os mais próximos/de maior impacto)
        vizinhos_potenciais = sorted(vizinhos_potenciais, key=lambda x: x['impacto'], reverse=True)[:max_vizinhos]
        ids_vizinhos = [v['id'] for v in vizinhos_potenciais]

        # --- C. GERAR TODAS AS CONFIGURAÇÕES S_c (A magia combinatória) ---
        # Ex: Se tem 3 vizinhos, gera 2^3 = 8 cenários de retornos diferentes
        combinacoes = []
        for tamanho in range(len(ids_vizinhos) + 1):
            for subset in itertools.combinations(vizinhos_potenciais, tamanho):
                combinacoes.append(list(subset))

        # --- D. REGISTRAR O MENU DE RETORNOS PARA O CPLEX ---
        for subset in combinacoes:
            perda_por_vizinhos = sum(v['impacto'] for v in subset)
            retorno_liquido = R_c_proprio - perda_por_vizinhos
            
            # Formato da chave de configuração: tupla ordenada de vizinhos ativos
            subset_ids = tuple(sorted([v['id'] for v in subset]))
            
            cenarios_cplex.append({
                'candidato_id': c['id'],
                'configuracao_ativa': subset_ids, # S_c
                'retorno_liquido': retorno_liquido # R_c(S_c)
            })

    return cenarios_cplex

def mock_resolver_cplex(cenarios_cplex: List[Dict]):
    """
    Função temporária apenas para exibir na tela (log) 
    o que o pre-processamento gerou, antes de integrarmos a biblioteca docplex.
    """
    if not cenarios_cplex:
        print("Nenhum cenário para otimizar.")
        return

    df_cenarios = pd.DataFrame(cenarios_cplex)
    
    print("\n" + "="*50)
    print("🟢 SIMULADOR DE ATRACTIVIDADE CONCLUÍDO 🟢")
    print("="*50)
    print(f"Total de combinações R_c(S_c) geradas: {len(df_cenarios)}")
    print(f"Número de candidatos únicos: {df_cenarios['candidato_id'].nunique()}")
    
    # Exibir um exemplo prático (pegar o primeiro candidato)
    exemplo_id = df_cenarios['candidato_id'].iloc[0]
    cenarios_exemplo = df_cenarios[df_cenarios['candidato_id'] == exemplo_id]
    
    print(f"\nExemplo de Menu de Retornos para o {exemplo_id}:")
    for _, row in cenarios_exemplo.iterrows():
        status_vizinhos = "Nenhum vizinho ativo" if not row['configuracao_ativa'] else f"Vizinhos ativos: {', '.join(row['configuracao_ativa'])}"
        print(f" -> {status_vizinhos} | Retorno Líquido: {row['retorno_liquido']:.2f}")
    print("="*50 + "\n")
    
    return True