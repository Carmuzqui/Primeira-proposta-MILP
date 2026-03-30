# """
# Otimizador MILP (CPLEX) para Designação de Eletropostos.
# Implementa a Função Objetivo e as Restrições R1 e R2 da formulação linear.
# """

# from docplex.mp.model import Model
# import pandas as pd
# from typing import List, Dict

# def resolver_modelo_cplex(cenarios_cplex: List[Dict]):
#     """
#     Constrói e resolve o modelo MILP usando IBM CPLEX.
#     """
#     if not cenarios_cplex:
#         print("Erro: Nenhum cenário fornecido ao otimizador.")
#         return None

#     print("\n" + "="*50)
#     print("🚀 INICIANDO SOLVER CPLEX...")
#     print("="*50)

#     # 1. INICIALIZAR O MODELO
#     mdl = Model(name='EVCS_Otimizacao_Designacao')

#     # 2. IDENTIFICAR CONJUNTOS (C e V(c))
#     candidatos = set()
#     vizinhos_por_candidato = {}
    
#     for cenario in cenarios_cplex:
#         c = cenario['candidato_id']
#         candidatos.add(c)
#         if c not in vizinhos_por_candidato:
#             vizinhos_por_candidato[c] = set()
#         # Adiciona os vizinhos desta configuração ao conjunto total de vizinhos de 'c'
#         vizinhos_por_candidato[c].update(cenario['configuracao_ativa'])

#     # 3. CRIAR VARIÁVEIS DE DECISÃO
#     # x_c: 1 se o eletroposto 'c' for instalado, 0 caso contrário
#     x_vars = mdl.binary_var_dict(candidatos, name="x")

#     # z_{c, S_c}: 1 se 'c' for instalado E a configuração exata de vizinhos S_c ocorrer
#     z_vars = {}
#     for cenario in cenarios_cplex:
#         c = cenario['candidato_id']
#         S_c = cenario['configuracao_ativa']
#         # Usamos a tupla como chave do dicionário de variáveis
#         z_vars[(c, S_c)] = mdl.binary_var(name=f"z_{c}_{S_c}")

#     # 4. FUNÇÃO OBJETIVO (Equação eq:objetivo_linear)
#     # Maximizar Z = Soma( R_c(S_c) * z_{c, S_c} )
#     objetivo = mdl.sum(
#         cenario['retorno_liquido'] * z_vars[(cenario['candidato_id'], cenario['configuracao_ativa'])]
#         for cenario in cenarios_cplex
#     )
#     mdl.maximize(objetivo)

#     # 5. RESTRIÇÕES
#     for c in candidatos:
#         # Encontrar todos os cenários (S_c) disponíveis para o candidato c
#         cenarios_de_c = [cen for cen in cenarios_cplex if cen['candidato_id'] == c]
        
#         # Restrição R1: Atribuição de configuração
#         # Soma(z_{c, S_c}) == x_c
#         mdl.add_constraint(
#             mdl.sum(z_vars[(c, cen['configuracao_ativa'])] for cen in cenarios_de_c) == x_vars[c],
#             ctname=f"R1_config_{c}"
#         )

#         # Restrição R2: Consistência de designações
#         V_c = vizinhos_por_candidato[c]
#         for cen in cenarios_de_c:
#             S_c = set(cen['configuracao_ativa'])
#             var_z = z_vars[(c, cen['configuracao_ativa'])]
            
#             # Para vizinhos DENTRO da configuração ativa (devem estar ligados)
#             for c_linha in S_c:
#                 if c_linha in x_vars: # Verificação de segurança
#                     mdl.add_constraint(x_vars[c_linha] >= var_z, ctname=f"R2_in_{c}_{c_linha}")
                    
#             # Para vizinhos FORA da configuração ativa (devem estar desligados)
#             vizinhos_fora = V_c - S_c
#             for c_linha in vizinhos_fora:
#                 if c_linha in x_vars: # Verificação de segurança
#                     mdl.add_constraint(x_vars[c_linha] <= 1 - var_z, ctname=f"R2_out_{c}_{c_linha}")

#     # 6. RESOLVER O MODELO
#     solucao = mdl.solve(log_output=False) # Mude para True se quiser ver o log matemático do CPLEX

#     # 7. PROCESSAR E EXIBIR RESULTADOS
#     if solucao:
#         lucro_total = solucao.get_objective_value()
#         print(f"✅ SOLUÇÃO ÓTIMA ENCONTRADA!")
#         print(f"💰 Lucro Global Estimado (Atractividade Líquida): {lucro_total:.2f}")
#         print("\n📍 Eletropostos Selecionados para Instalação:")
        
#         nodos_selecionados = []
#         for c in candidatos:
#             if solucao.get_value(x_vars[c]) > 0.5: # Evitar problemas de ponto flutuante do solver
#                 nodos_selecionados.append(c)
#                 print(f"  -> Instalar no nodo: {c}")
                
#         print(f"\nResumo: {len(nodos_selecionados)} de {len(candidatos)} candidatos foram aprovados pelo modelo.")
#         print("="*50 + "\n")
        
#         return {
#             'status': 'Optimal',
#             'lucro_total': lucro_total,
#             'nodos_selecionados': nodos_selecionados
#         }
#     else:
#         print("❌ O modelo não encontrou uma solução viável.")
#         return {'status': 'Infeasible', 'lucro_total': 0, 'nodos_selecionados': []}














# """
# Otimizador MILP (CPLEX) para Designação de Eletropostos.
# Implementa a Função Objetivo e as Restrições R1, R2, R3 e R4.
# """

# from docplex.mp.model import Model
# import pandas as pd
# import math
# from typing import List, Dict

# def resolver_modelo_cplex(cenarios_cplex: List[Dict], dados_cobertura: Dict, meta_cobertura_pct: float = 0.85):
#     """
#     Constrói e resolve o modelo MILP exigindo qualidade de rede (cobertura).
#     """
#     if not cenarios_cplex:
#         print("Erro: Nenhum cenário fornecido ao otimizador.")
#         return None

#     mdl = Model(name='EVCS_Otimizacao_Designacao')

#     candidatos = set()
#     vizinhos_por_candidato = {}
#     for cenario in cenarios_cplex:
#         c = cenario['candidato_id']
#         candidatos.add(c)
#         if c not in vizinhos_por_candidato:
#             vizinhos_por_candidato[c] = set()
#         vizinhos_por_candidato[c].update(cenario['configuracao_ativa'])

#     # Variáveis Principais
#     x_vars = mdl.binary_var_dict(candidatos, name="x")
    
#     z_vars = {}
#     for cenario in cenarios_cplex:
#         z_vars[(cenario['candidato_id'], cenario['configuracao_ativa'])] = mdl.binary_var(name=f"z")

#     # Variáveis de Cobertura (y_p)
#     y_vars = {}
#     mapeamento_pois = dados_cobertura['mapeamento_candidatos']
#     for poi_id in mapeamento_pois.keys():
#         y_vars[poi_id] = mdl.binary_var(name=f"y_{poi_id}")

#     # FUNÇÃO OBJETIVO
#     objetivo = mdl.sum(
#         cenario['retorno_liquido'] * z_vars[(cenario['candidato_id'], cenario['configuracao_ativa'])]
#         for cenario in cenarios_cplex
#     )
#     mdl.maximize(objetivo)

#     # RESTRIÇÕES
#     for c in candidatos:
#         cenarios_de_c = [cen for cen in cenarios_cplex if cen['candidato_id'] == c]
        
#         # R1
#         mdl.add_constraint(mdl.sum(z_vars[(c, cen['configuracao_ativa'])] for cen in cenarios_de_c) == x_vars[c])

#         # R2
#         V_c = vizinhos_por_candidato[c]
#         for cen in cenarios_de_c:
#             S_c = set(cen['configuracao_ativa'])
#             var_z = z_vars[(c, cen['configuracao_ativa'])]
            
#             for c_linha in S_c:
#                 if c_linha in x_vars: 
#                     mdl.add_constraint(x_vars[c_linha] >= var_z)
                    
#             vizinhos_fora = V_c - S_c
#             for c_linha in vizinhos_fora:
#                 if c_linha in x_vars: 
#                     mdl.add_constraint(x_vars[c_linha] <= 1 - var_z)

#     # R3: Indicador de Cobertura (Um POI só está coberto se um de seus cobridores for instalado)
#     for poi_id, cands_cobridores in mapeamento_pois.items():
#         # y_p <= soma(x_c)
#         mdl.add_constraint(
#             y_vars[poi_id] <= mdl.sum(x_vars[c] for c in cands_cobridores if c in x_vars),
#             ctname=f"R3_{poi_id}"
#         )

#     # R4: Meta de Cobertura Global
#     total_pois = dados_cobertura['total_pois']
#     cobertos_existentes = dados_cobertura['cobertos_existentes']
#     meta_absoluta = math.ceil(total_pois * meta_cobertura_pct)
    
#     # Opcional: Calcular a capacidade máxima teórica de cobertura
#     # Se os existentes + todos os mapeados não chegam em 85%, o modelo seria inviável.
#     cobertura_maxima_possivel = cobertos_existentes + len(mapeamento_pois)
#     if cobertura_maxima_possivel < meta_absoluta:
#         print(f"⚠️ AVISO: É impossível atingir {meta_cobertura_pct*100}% de cobertura com a malha atual.")
#         print(f"Forçando a meta para o máximo possível ({cobertura_maxima_possivel} POIs).")
#         meta_absoluta = cobertura_maxima_possivel

#     mdl.add_constraint(
#         cobertos_existentes + mdl.sum(y_vars.values()) >= meta_absoluta,
#         ctname="R4_Meta"
#     )

#     solucao = mdl.solve(log_output=False) 

#     if solucao:
#         lucro_total = solucao.get_objective_value()
#         cobertura_final = cobertos_existentes + sum(1 for poi_id in y_vars if solucao.get_value(y_vars[poi_id]) > 0.5)
#         pct_cobertura = (cobertura_final / total_pois) * 100

#         nodos_selecionados = [c for c in candidatos if solucao.get_value(x_vars[c]) > 0.5]
        
#         return {
#             'status': 'Optimal',
#             'lucro_total': lucro_total,
#             'nodos_selecionados': nodos_selecionados,
#             'cobertura_final': cobertura_final,
#             'pct_cobertura': pct_cobertura,
#             'total_pois': total_pois
#         }
#     else:
#         return {'status': 'Infeasible', 'lucro_total': 0, 'nodos_selecionados': []}












"""
Otimizador MILP (CPLEX) para Designação de Eletropostos.
Implementa a Função Objetivo e as Restrições R1, R2, R3 e R4.
"""

from docplex.mp.model import Model
import pandas as pd
import math
from typing import List, Dict

def resolver_modelo_cplex(cenarios_cplex: List[Dict], dados_cobertura: Dict, meta_cobertura_pct: float = 0.85):
    """
    Constrói e resolve o modelo MILP exigindo qualidade de rede (cobertura).
    """
    if not cenarios_cplex:
        print("Erro: Nenhum cenário fornecido ao otimizador.")
        return None

    mdl = Model(name='EVCS_Otimizacao_Designacao')

    candidatos = set()
    vizinhos_por_candidato = {}
    for cenario in cenarios_cplex:
        c = cenario['candidato_id']
        candidatos.add(c)
        if c not in vizinhos_por_candidato:
            vizinhos_por_candidato[c] = set()
        vizinhos_por_candidato[c].update(cenario['configuracao_ativa'])

    # Variáveis Principais
    x_vars = mdl.binary_var_dict(candidatos, name="x")
    
    # CORREÇÃO: Nomes únicos para evitar "Warning: Duplicate variable name"
    z_vars = {}
    for cenario in cenarios_cplex:
        c_id = cenario['candidato_id']
        conf_str = "_".join(cenario['configuracao_ativa']) if cenario['configuracao_ativa'] else "vazio"
        nome_z = f"z_{c_id}_{conf_str}"
        z_vars[(c_id, cenario['configuracao_ativa'])] = mdl.binary_var(name=nome_z)

    # Variáveis de Cobertura (y_p)
    y_vars = {}
    mapeamento_pois = dados_cobertura['mapeamento_candidatos']
    for poi_id in mapeamento_pois.keys():
        y_vars[poi_id] = mdl.binary_var(name=f"y_{poi_id}")

    # FUNÇÃO OBJETIVO
    objetivo = mdl.sum(
        cenario['retorno_liquido'] * z_vars[(cenario['candidato_id'], cenario['configuracao_ativa'])]
        for cenario in cenarios_cplex
    )
    mdl.maximize(objetivo)

    # RESTRIÇÕES
    for c in candidatos:
        cenarios_de_c = [cen for cen in cenarios_cplex if cen['candidato_id'] == c]
        
        # R1
        mdl.add_constraint(mdl.sum(z_vars[(c, cen['configuracao_ativa'])] for cen in cenarios_de_c) == x_vars[c])

        # R2
        V_c = vizinhos_por_candidato[c]
        for cen in cenarios_de_c:
            S_c = set(cen['configuracao_ativa'])
            var_z = z_vars[(c, cen['configuracao_ativa'])]
            
            for c_linha in S_c:
                if c_linha in x_vars: 
                    mdl.add_constraint(x_vars[c_linha] >= var_z)
                    
            vizinhos_fora = V_c - S_c
            for c_linha in vizinhos_fora:
                if c_linha in x_vars: 
                    mdl.add_constraint(x_vars[c_linha] <= 1 - var_z)

    # R3: Indicador de Cobertura 
    for poi_id, cands_cobridores in mapeamento_pois.items():
        mdl.add_constraint(
            y_vars[poi_id] <= mdl.sum(x_vars[c] for c in cands_cobridores if c in x_vars),
            ctname=f"R3_{poi_id}"
        )

    # R4: Meta de Cobertura Global
    total_pois = dados_cobertura['total_pois']
    cobertos_existentes = dados_cobertura['cobertos_existentes']
    meta_absoluta = math.ceil(total_pois * meta_cobertura_pct)
    
    cobertura_maxima_possivel = cobertos_existentes + len(mapeamento_pois)
    if cobertura_maxima_possivel < meta_absoluta:
        print(f"⚠️ AVISO: É impossível atingir {meta_cobertura_pct*100}% de cobertura com a malha atual.")
        meta_absoluta = cobertura_maxima_possivel

    mdl.add_constraint(
        cobertos_existentes + mdl.sum(y_vars.values()) >= meta_absoluta,
        ctname="R4_Meta"
    )

    solucao = mdl.solve(log_output=False) 

    if solucao:
        lucro_total = solucao.get_objective_value()
        cobertura_final = cobertos_existentes + sum(1 for poi_id in y_vars if solucao.get_value(y_vars[poi_id]) > 0.5)
        pct_cobertura = (cobertura_final / total_pois) * 100

        nodos_selecionados = [c for c in candidatos if solucao.get_value(x_vars[c]) > 0.5]
        
        # Log limpo no terminal
        print(f"\n✅ SOLUÇÃO ÓTIMA ENCONTRADA!")
        print(f"💰 Lucro Global Estimado: {lucro_total:.2f}")
        print(f"🎯 Cobertura Atingida: {pct_cobertura:.1f}% ({cobertura_final}/{total_pois} POIs)")
        print(f"📍 Nodos Selecionados: {', '.join(nodos_selecionados)}\n")

        return {
            'status': 'Optimal',
            'lucro_total': lucro_total,
            'nodos_selecionados': nodos_selecionados,
            'cobertura_final': cobertura_final,
            'pct_cobertura': pct_cobertura,
            'total_pois': total_pois
        }
    else:
        print("❌ O modelo não encontrou uma solução viável.")
        return {'status': 'Infeasible', 'lucro_total': 0, 'nodos_selecionados': []}