# Primeira proposta MILP para localização de eletropostos

Otimização de localização e dimensionamento de estações de recarga para veículos elétricos (eletropostos) usando programação linear inteira mista.

**Status:** Fase 1 - Modelo matemático simplificado (prova de conceito)

---

## 📋 Visão Geral

Este repositório documenta a pesquisa de doutorado sobre otimização de localização de estações de recarga para veículos elétricos (EV). O projeto integra:

- **Pré-processamento multicritério**: Filtragem de candidatos viáveis com maior potencial
- **Simulação de lucro**: Computação de retornos esperados por candidato e suas interações
- **Otimização MILP simplificada**: Seleção de candidatos que maximize lucro respeitando qualidade de rede
- **Validação de capacidade de rede**: Garantia de viabilidade técnica de operação conjunta

### Foco da fase 1

Desenvolvimento e validação de um **modelo matemático simplificado e linear** que:
- Capture a essência do problema de localização com interações entre candidatos vizinhos
- Seja resolúvel em tempo polinomial usando solvers comerciais (CPLEX, Gurobi)
- Sirva como base para futuras extensões (dinâmica temporal, meta-heurísticas, robustez)

---

## Objetivo

Propor uma abordagem inovadora para otimizar a designação e dimensionamento de eletropostos em contexto urbano/regional, considerando:

1. **Maximização de lucro** ao longo de um horizonte de 10 anos
2. **Cobertura mínima de pontos de interesse** (POIs: hospitais, educação, transporte, comércio, recreação)
3. **Viabilidade técnica da rede elétrica** (capacidade de nós de distribuição)
4. **Interações espaciais** entre candidatos vizinhos (canibalização de demanda)

---

## Categoria do modelo

| Aspecto | Classificação |
|--------|---------------|
| **Tipo de problema** | Localização de Facilidades (capacitado) |
| **Tipo matemático** | Programação Linear Inteira Mista (MILP) |
| **Estratégia de solução** | Linearização via pre-computação de lucro |
| **Domínio de aplicação** | Planejamento de infraestrutura / design de Rede |

---

## Estrutura do projeto
