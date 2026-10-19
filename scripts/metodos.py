# -*- coding: utf-8 -*-
"""Regras do estudo, definidas uma vez e usadas em todas as análises (decisões do Fabian em 15/10/2026).
Cada regra é um trecho SQL aplicado à view `base` e tem teste em testes.py."""

# Universo: só natureza jurídica empresarial (grupo 2), fora do exterior, com datas coerentes
UNIVERSO = """substr(lpad(natureza_juridica::varchar, 4, '0'), 1, 1) = '2' AND uf <> 'EX'
  AND data_inicio >= DATE '1900-01-01' AND NOT (situacao IN (4, 8) AND data_situacao < data_inicio)"""

# Motivos de baixa que não são fechamento do negócio (reorganização societária)
MOTIVOS_REORGANIZACAO = (2, 3, 4)   # incorporação, fusão, cisão total

# Fechamento: baixada (menos reorganização) ou inapta
FECHOU = f"(situacao IN (4, 8) AND coalesce(motivo_situacao, 0) NOT IN {MOTIVOS_REORGANIZACAO})"
# Sensibilidade: só baixa voluntária (encerramento, LC 123, não início de atividade)
BAIXA_VOLUNTARIA = "(situacao = 8 AND motivo_situacao IN (1, 54, 9))"
# Baixas de ofício em massa (para teste de sensibilidade)
BAIXA_OFICIO_MASSA = "(situacao = 8 AND motivo_situacao IN (67, 71, 73))"

# Grupo de porte na abertura: MEI = opção pelo MEI em até 180 dias da abertura; ME e EPP pelo porte atual
GRUPO = """CASE WHEN data_opcao_mei IS NOT NULL AND data_opcao_mei <= data_inicio + INTERVAL 180 DAY THEN 'MEI'
  WHEN porte = 1 THEN 'ME' WHEN porte = 3 THEN 'EPP' ELSE 'Demais' END"""

# Turmas maduras: pelo menos 5 anos de acompanhamento até a extração (tempo para a inaptidão aparecer)
TURMA_MIN, TURMA_MAX = 2012, 2021
DATA_BASE = "2026-10-11"

# Duração em anos até o fechamento ou até a data da extração (censura)
DURACAO = f"""(CASE WHEN {FECHOU} THEN date_diff('day', data_inicio, data_situacao)
  ELSE date_diff('day', data_inicio, DATE '{DATA_BASE}') END) / 365.25"""

def br(v, c=0):
    """Número no formato brasileiro (ponto de milhar, vírgula decimal)."""
    return f"{v:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- Revisão de 15/10/2026 (aprovada pelo Fabian) ---
# Medida direta por turma: cada prazo só usa turmas em que todas as empresas o completaram e no mesmo regime de fiscalização
TURMAS_CURTO = (2016, 2020)   # 1, 3 e 5 anos (inaptidão contínua a partir de 2016)
TURMAS_10A = (2012, 2015)     # 10 anos, com aviso (época das baixas de ofício em massa)
# Encerramento planejado: incorporação imobiliária (empresa criada para uma obra) fica fora do ranking de risco
PLANEJADO = "(cnae_principal = '4110700')"
# Fechamento com dívida ativa da União (devedor principal) = fechamento com problema; sem dívida = encerramento limpo
FECHOU_COM_DIVIDA = f"({FECHOU} AND coalesce(n_inscricoes_pgfn, 0) > 0)"
