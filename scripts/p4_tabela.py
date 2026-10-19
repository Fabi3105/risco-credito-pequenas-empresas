# -*- coding: utf-8 -*-
"""Tabela de pontos v2 (decisão do Fabian em 16/10/2026, após a 1ª revisão): poucas variáveis, cada uma em faixas fixas e
explicáveis, com as parecidas reunidas num bloco só (perfil de dívida, histórico dos sócios, porte com natureza jurídica).
Saíram: e-mail, telefone, nome fantasia, dívida ajuizada, anos desde a 1ª dívida, saturação do setor e faixa etária dos sócios
(atributo de pessoa; risco de compliance). Esta especificação é a ÚNICA fonte das faixas: gera o SQL do modelo e o JSON da
calculadora do painel, para as duas contas serem idênticas."""
# faixas numéricas: (coluna de origem, limites, rótulos) — limite inferior incluído; rótulos têm len(limites)+1 itens
NUM = {
    'idade': ('idade_anos', [1, 2, 3, 5, 10, 20], ['menos de 1 ano', '1 a 2 anos', '2 a 3 anos', '3 a 5 anos', '5 a 10 anos', '10 a 20 anos', '20 anos ou mais']),
    'populacao_municipio': ('populacao', [20000, 100000, 500000, 1000000], ['até 20 mil hab.', '20 a 100 mil hab.', '100 a 500 mil hab.', '500 mil a 1 milhão hab.', 'mais de 1 milhão hab.']),
    'pib_per_capita_municipio': ('pib_per_capita', [20000, 30000, 45000, 65000], ['até R$ 20 mil', 'R$ 20 a 30 mil', 'R$ 30 a 45 mil', 'R$ 45 a 65 mil', 'mais de R$ 65 mil']),
    'capital_social': ('capital_social', [1000.01, 10000.01, 50000.01, 200000.01], ['até R$ 1 mil (inclui zero)', 'R$ 1 a 10 mil', 'R$ 10 a 50 mil', 'R$ 50 a 200 mil', 'mais de R$ 200 mil']),
    'atividades_secundarias': ('n_cnae_sec', [1, 3, 6], ['nenhuma', '1 a 2', '3 a 5', '6 ou mais']),
    'filiais': ('n_filiais', [1, 3], ['nenhuma', '1 a 2', '3 ou mais']),
    'socios_pf': ('n_socios_pf', [1, 2, 3], ['nenhum', '1', '2', '3 ou mais']),
}
# variáveis ordenadas em que o risco deve andar num só sentido (dívida previdenciária incluída na 2ª revisão) (conferido depois do ajuste; faixas vizinhas fora de ordem são juntadas)
ORDENADAS = {'simples': ['nunca optou', 'optante', 'excluída do Simples'],
             'divida_ativa': ['sem dívida', 'só parcelada ou garantida', 'em cobrança até R$ 10 mil', 'em cobrança de R$ 10 a 100 mil', 'em cobrança acima de R$ 100 mil'],
             'divida_previdenciaria': ['não', 'sim'],
             'historico_socios': ['sócio tem outra empresa ativa sem dívida', 'sócio já fechou empresa sem dívida', 'única empresa dos sócios', 'sócio tem outra empresa ativa com dívida', 'sócio já fechou empresa deixando dívida']}
NATUREZA = "CASE natureza_juridica::INT WHEN 2135 THEN 'empresário individual' WHEN 2062 THEN 'sociedade limitada' WHEN 2240 THEN 'sociedade simples' WHEN 2054 THEN 'S.A. fechada' WHEN 2305 THEN 'EIRELI' ELSE 'outra natureza' END"
# Regras de política (2ª revisão, decisão do Fabian): valem FORA da nota e prevalecem sobre ela. A empresa que cai em uma delas nunca é
# "bom cliente" e vai para análise manual, qualquer que seja a faixa. Motivo: a nota mede o risco médio; a exclusão do Simples não acrescenta
# risco depois que o perfil de dívida entra na conta (o ajuste juntou "excluída" com "optante"), mas é um evento de política que o banco quer ver.
REGRAS = [('idade_anos < 1', 'aberta há menos de 1 ano'), ("opcao_simples = 'N'", 'excluída do Simples'),
          ('coalesce(t1_em_cobranca, 0) > 0', 'dívida ativa em cobrança')]
SQL_BLOQUEIO = "CASE " + " ".join(f"WHEN {c} THEN '{r}'" for c, r in REGRAS) + " END"
def caso(col, lim, rot):
    s = "CASE WHEN " + col + " IS NULL THEN NULL " + " ".join(f"WHEN {col} < {l} THEN '{r}'" for l, r in zip(lim, rot)) + f" ELSE '{rot[-1]}' END"
    return s
def sql_tabela(fonte, extras="parte, y_nova_divida::TINYINT y_nova_divida, y_fechou::TINYINT y_fechou,"):
    """SELECT das variáveis da tabela v2 a partir das colunas de p4_montar (mai/2023) ou p3_base_2026 (hoje)."""
    num = ",\n  ".join(f"{caso(f'({c})', l, r)} {v}" for v, (c, l, r) in NUM.items())
    return f"""SELECT cnpj_basico, {extras}
  CASE WHEN grupo_23 = 'MEI' THEN 'MEI' ELSE grupo_23 || ' · ' || {NATUREZA} END porte_natureza,
  substr(cnae_principal, 1, 2) setor, uf,
  CASE opcao_simples WHEN 'S' THEN 'optante' WHEN 'N' THEN 'excluída do Simples' ELSE 'nunca optou' END simples,
  {num},
  CASE WHEN coalesce(n_socios_pj, 0) > 0 THEN 'sim' ELSE 'não' END socio_pj,
  CASE WHEN c1_socios_pf IS NULL THEN 'sem sócio pessoa física' WHEN n_outras_fechadas_divida > 0 THEN 'sócio já fechou empresa deixando dívida'
       WHEN n_outras_ativas_divida > 0 THEN 'sócio tem outra empresa ativa com dívida' WHEN n_outras_fechadas > 0 THEN 'sócio já fechou empresa sem dívida'
       WHEN n_outras_ativas > 0 THEN 'sócio tem outra empresa ativa sem dívida' ELSE 'única empresa dos sócios' END historico_socios,
  CASE WHEN coalesce(t1_inscricoes, 0) = 0 THEN 'sem dívida' WHEN coalesce(t1_em_cobranca, 0) = 0 THEN 'só parcelada ou garantida'
       WHEN t1_valor < 10000 THEN 'em cobrança até R$ 10 mil' WHEN t1_valor < 100000 THEN 'em cobrança de R$ 10 a 100 mil' ELSE 'em cobrança acima de R$ 100 mil' END divida_ativa,
  CASE WHEN coalesce(t1_previdenciaria, 0) > 0 THEN 'sim' ELSE 'não' END divida_previdenciaria,
  {SQL_BLOQUEIO} regra_politica
FROM {fonte}"""
VARIAVEIS = ['porte_natureza', 'setor', 'uf', 'simples', *NUM.keys(), 'socio_pj', 'historico_socios', 'divida_ativa', 'divida_previdenciaria']

if __name__ == "__main__":   # gera dados/processados_2023-05/p4_X2.parquet (amostra da P4 com as variáveis v2)
    import duckdb, pathlib, shutil
    from base import RAIZ
    P23 = RAIZ / "dados/processados_2023-05"
    con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'")
    tmp = pathlib.Path.home() / "tmp_X2.parquet"; fonte = f"read_parquet('{P23}/p4_amostra.parquet')"
    con.execute(f"COPY ({sql_tabela(fonte)}) TO '{tmp}' (FORMAT parquet)"); shutil.move(str(tmp), str(P23 / "p4_X2.parquet"))
    for v in VARIAVEIS:
        print(v, con.execute(f"select {v}, count(*), round(100*avg(y_nova_divida),1) from '{P23}/p4_X2.parquet' group by 1 order by 3").fetchall()[:12])
