# -*- coding: utf-8 -*-
"""Variáveis do modelo de risco (P4), todas como estavam em mai/2023, calculadas no DuckDB para caber na memória da VM.
Gera dados/processados_2023-05/p4_X.parquet (números em float32; categorias como texto curto).
Dívida ativa: posição de mar/2023 (arquivo PGFN 2023 T1), sem informação do futuro."""
import duckdb, pathlib, shutil
from base import RAIZ
P23 = RAIZ / "dados/processados_2023-05"
CATEG = ['grupo', 'divisao', 'secao', 'uf', 'natureza', 'simples', 'qualificacao']
DIVIDA = ['n_inscricoes_pgfn', 'ln_valor_pgfn', 'pgfn_em_cobranca', 'pgfn_beneficio_fiscal', 'pgfn_ajuizado', 'pgfn_previdenciaria', 'pgfn_anos_desde_1a']
D = "substr(cnae_principal, 1, 2)"
SECAO = f"""CASE WHEN {D} <= '03' THEN 'A' WHEN {D} <= '09' THEN 'B' WHEN {D} <= '33' THEN 'C' WHEN {D} <= '39' THEN 'DE'
  WHEN {D} <= '43' THEN 'F' WHEN {D} <= '47' THEN 'G' WHEN {D} <= '53' THEN 'H' WHEN {D} <= '56' THEN 'I' WHEN {D} <= '63' THEN 'J'
  WHEN {D} <= '66' THEN 'K' WHEN {D} <= '68' THEN 'L' WHEN {D} <= '75' THEN 'M' WHEN {D} <= '82' THEN 'N' WHEN {D} <= '84' THEN 'O'
  WHEN {D} <= '85' THEN 'P' WHEN {D} <= '88' THEN 'Q' WHEN {D} <= '93' THEN 'R' ELSE 'S' END"""
F = lambda e: f"({e})::FLOAT"
def sql_variaveis(fonte, extras="parte, y_nova_divida::TINYINT y_nova_divida, y_fechou::TINYINT y_fechou, y_fechou_div::TINYINT y_fechou_div,", data_ref="2023-05-15"):
    """SELECT das 33 variáveis do modelo a partir de uma tabela com as colunas de p4_montar (mai/2023) ou p3_base_2026 (hoje)."""
    return f"""SELECT cnpj_basico, {extras}
  grupo_23 grupo, {D} divisao, {SECAO} secao, uf, natureza_juridica::VARCHAR natureza, qualificacao_responsavel::VARCHAR qualificacao,
  CASE opcao_simples WHEN 'S' THEN 'no Simples' WHEN 'N' THEN 'excluída do Simples' ELSE 'nunca optou' END simples,
  {F('idade_anos')} idade_anos, {F('ln(populacao)')} ln_pop, {F('ln(pib_per_capita)')} ln_pibpc, {F('ln(saturacao_2020)')} ln_saturacao,
  {F('ln(1 + coalesce(capital_social, 0))')} ln_capital, {F('n_cnae_sec')} n_cnae_sec,
  {F('tem_email::INT')} tem_email, {F('tem_telefone::INT')} tem_telefone, {F('tem_fantasia::INT')} tem_fantasia,
  {F("(opcao_mei = 'N')::INT")} mei_excluido, {F('n_filiais')} n_filiais, {F('n_socios_pf')} n_socios_pf, {F('n_socios_pj')} n_socios_pj,
  {F('faixa_etaria_max')} faixa_etaria_max, {F('faixa_etaria_min')} faixa_etaria_min,
  {F('n_outras')} n_outras, {F('n_outras_fechadas')} n_outras_fechadas, {F('n_outras_fechadas_divida')} n_outras_fechadas_divida,
  {F('n_outras_ativas')} n_outras_ativas, {F('n_outras_ativas_divida')} n_outras_ativas_divida, {F('mudou_socio_12m::INT')} mudou_socio_12m,
  {F('t1_inscricoes')} n_inscricoes_pgfn, {F('ln(1 + coalesce(t1_valor, 0))')} ln_valor_pgfn, {F('coalesce(t1_em_cobranca, 0)')} pgfn_em_cobranca,
  {F('coalesce(t1_beneficio_fiscal, 0)')} pgfn_beneficio_fiscal, {F('coalesce(t1_ajuizado::INT, 0)')} pgfn_ajuizado,
  {F('coalesce(t1_previdenciaria, 0)')} pgfn_previdenciaria, {F(f"date_diff('day', t1_primeira_inscricao, DATE '{data_ref}') / 365.25")} pgfn_anos_desde_1a
FROM {fonte}"""
SQL = sql_variaveis(f"read_parquet('{P23}/p4_amostra.parquet')")
if __name__ == "__main__":
    con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'")
    tmp = pathlib.Path.home() / "tmp_p4_X.parquet"
    con.execute(f"COPY ({SQL}) TO '{tmp}' (FORMAT parquet)"); shutil.move(str(tmp), str(P23 / "p4_X.parquet"))
    print(con.execute(f"select count(*) from '{P23}/p4_X.parquet'").fetchone())

# --- Faixas do scorecard (usadas em p4_scorecard.py e p4_modelo.py) ---
import numpy as np
def limites_faixas(v):
    """Limites das faixas de uma variável numérica, calculados só no treino.
    Regra: até 10 faixas pelos decis. Se mais da metade dos valores for zero (contagens raras, como filiais ou dívidas
    parceladas), o zero vira uma faixa própria e os decis são calculados só entre os valores acima de zero."""
    v = v[~np.isnan(v)]
    if (v == 0).mean() > 0.5:
        pos = v[v > 0]
        q = np.nanquantile(pos, np.linspace(0.1, 0.9, 9)) if len(pos) else np.array([])
        return np.unique(np.concatenate([[0.0, 1e-9], q]))
    return np.unique(np.nanquantile(v, np.linspace(0.1, 0.9, 9)))
# conversão dos limites para a unidade original, só para leitura da tabela de pontos
UNIDADE = {'ln_pop': (np.exp, 'habitantes'), 'ln_pibpc': (np.exp, 'R$ de PIB per capita'), 'ln_saturacao': (np.exp, 'observadas ÷ esperadas'),
           'ln_capital': (np.expm1, 'R$ de capital social'), 'ln_valor_pgfn': (np.expm1, 'R$ de dívida ativa')}
def rotulo_faixa(c, lo, hi):
    f, u = UNIDADE.get(c, (lambda x: x, ''))
    def fmt(x):
        if np.isinf(x): return '∞' if x > 0 else '−∞'
        x = float(f(x)) if np.isfinite(x) else x
        return f"{x:,.0f}".replace(',', '.') if abs(x) >= 1000 else f"{x:.3g}".replace('.', ',')
    if hi == 1e-9 and lo == 0.0: return f"= 0 {u}".strip()
    if lo == 1e-9: lo = 0.0; return f"acima de 0 até {fmt(hi)} {u}".strip()
    return f"de {fmt(lo)} até {fmt(hi)} {u}".strip()
