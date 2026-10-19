# -*- coding: utf-8 -*-
"""P3 — Onde estão os bons clientes pouco atendidos.
Bom cliente = faixa A ou B nas DUAS notas (dívida e fechamento) e fora das regras de política (p4_tabela.REGRAS: menos de 1 ano,
excluída do Simples ou dívida ativa em cobrança), aplicadas às empresas ativas hoje (amostra de 10%, x10).
Crédito: SCR.data (Banco Central), carteira ativa e inadimplência de Micro (MEI + ME) e Pequeno (EPP), média dos 12 meses até ago/2026.
Índice de atendimento = crédito do segmento ÷ crédito esperado para o seu número de empresas, no padrão nacional do setor e porte
(mesma ideia do "observado ÷ esperado" do C2). Micro só entra no ranking com proporção de MEIs a até 10 pontos da nacional do setor.
Pouco atendido = índice abaixo de 0,8 com bons clientes iguais ou acima do esperado para a mistura
(fora atividades financeiras e segmentos com menos de 2 mil empresas).
Prioritária = pouco atendida e com inadimplência igual ou menor que a nacional do setor e porte.
Saídas: resultados/p3_segmentos.csv, p3_pouco_atendidos.csv, p3_oportunidades_prioritarias.csv, p3_resumo_uf.csv, p3_resumo_setor.csv"""
import duckdb, pandas as pd
from base import PROC, salvar
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1800MB'; SET enable_progress_bar=false")
SEC = {'A': 'Agricultura', 'B': 'Indústrias extrativas', 'C': 'Indústrias de transformação', 'DE': 'Eletricidade', 'F': 'Construção', 'G': 'Comércio',
       'H': 'Transporte', 'I': 'Alojamento', 'J': 'Informação', 'K': 'Atividades financeiras', 'L': 'Atividades imobiliárias',
       'M': 'Atividades profissionais', 'N': 'Atividades administrativas', 'P': 'Educação', 'Q': 'Saúde', 'R': 'Artes', 'S': 'Outras atividades'}
case_sec = "CASE " + " ".join(f"WHEN cnae_secao LIKE 'PJ - {v}%' THEN '{k}'" for k, v in SEC.items()) + " END"
con.execute(f"""CREATE TABLE scr AS SELECT {case_sec} secao, uf, CASE porte WHEN 'PJ - Micro' THEN 'Micro' ELSE 'Pequeno' END porte_scr,
  sum(carteira_ativa) / 12 carteira, sum(carteira_inadimplida_arrastada) / 12 inad, sum(numero_de_operacoes) / 12 operacoes
  FROM read_parquet('{PROC}/scr/*.parquet') WHERE porte IN ('PJ - Micro', 'PJ - Pequeno') AND data_base > DATE '2025-08-31' GROUP BY ALL""")
con.execute(f"""CREATE TABLE emp AS SELECT uf, secao, CASE WHEN grupo = 'EPP' THEN 'Pequeno' ELSE 'Micro' END porte_scr,
  10 * count(*) empresas, 10 * count(*) FILTER (WHERE grupo = 'MEI') n_mei, 10 * count(*) FILTER (WHERE grupo = 'ME') n_me,
  10 * count(*) FILTER (WHERE faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL) bons,
  10 * count(*) FILTER (WHERE grupo = 'MEI' AND faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL) bons_mei,
  10 * count(*) FILTER (WHERE grupo <> 'MEI' AND faixa_divida IN ('A','B') AND faixa_fechamento IN ('A','B') AND regra_politica IS NULL) bons_outros,
  avg(p_divida) p_divida_media, avg(p_fechamento) p_fechamento_media
  FROM read_parquet('{PROC}/p3/p3_notas_*.parquet') WHERE grupo IN ('MEI', 'ME', 'EPP') GROUP BY ALL""")
seg = con.execute("SELECT e.*, s.carteira, s.inad, s.operacoes FROM emp e JOIN scr s USING (uf, secao, porte_scr) ORDER BY uf, secao, porte_scr").df()
# Mistura MEI x ME (revisão da camada 2): o porte Micro do SCR junta MEI e ME, que tomam crédito muito diferente, e o SCR não separa os dois.
# Tentou-se estimar o crédito por MEI e por ME entre as UFs (mínimos quadrados), mas as duas contagens andam juntas e os coeficientes
# saíram instáveis (crédito por MEI zero em 12 de 17 setores). Regra adotada: o crédito esperado é o padrão nacional por empresa do setor e
# porte, e um segmento Micro só entra no ranking se a sua proporção de MEIs estiver a até 10 pontos da nacional do setor ("comparável").
# Bons esperados: MEIs × taxa nacional de bons do MEI no setor + MEs × taxa das MEs (Pequeno: taxa nacional das EPPs).
import numpy as np
esp_cred, esp_bons, comp, desv = np.zeros(len(seg)), np.zeros(len(seg)), np.ones(len(seg), dtype=bool), np.zeros(len(seg))
for (sec, porte), g in seg.groupby(['secao', 'porte_scr']):
    esp_cred[g.index] = g.empresas * g.carteira.sum() / g.empresas.sum()
    if porte == 'Micro':
        rm = g.bons_mei.sum() / max(g.n_mei.sum(), 1); ro = g.bons_outros.sum() / max(g.n_me.sum(), 1)
        esp_bons[g.index] = g.n_mei * rm + g.n_me * ro
        mei_nac = g.n_mei.sum() / g.empresas.sum(); desv[g.index] = (g.n_mei / g.empresas - mei_nac).abs(); comp[g.index] = desv[g.index] <= 0.10
    else:
        esp_bons[g.index] = g.empresas * g.bons.sum() / g.empresas.sum()
seg['credito_esperado'] = esp_cred; seg['bons_esperados'] = esp_bons; seg['comparavel'] = comp; seg['desvio_mei_pontos'] = 100 * desv
nac = seg.groupby(['secao', 'porte_scr']).apply(lambda g: g.inad.sum() / g.carteira.sum()).rename('inad_br').reset_index()
seg = seg.merge(nac, on=['secao', 'porte_scr'])
seg['credito_por_empresa'] = seg.carteira / seg.empresas; seg['credito_esperado_por_empresa'] = seg.credito_esperado / seg.empresas
seg['indice_atendimento'] = seg.carteira / seg.credito_esperado
seg['bons_pct'] = seg.bons / seg.empresas; seg['bons_pct_esperado'] = seg.bons_esperados / seg.empresas; seg['inad_scr'] = seg.inad / seg.carteira
seg['pct_mei'] = seg.n_mei / seg.empresas
# Atividades financeiras (K) ficam fora do ranking: o crédito delas no SCR inclui operações entre empresas do próprio setor
# (factorings, holdings) e não é crédito de pequena empresa; o crédito por empresa do setor é 10 vezes o dos demais.
seg['pouco_atendido'] = (seg.indice_atendimento < 0.8) & (seg.bons >= seg.bons_esperados) & (seg.empresas >= 2000) & (seg.secao != 'K') & seg.comparavel
seg['inadimplencia_ate_nacional'] = seg.inad_scr <= seg.inad_br
# lacuna: crédito que faltaria para o segmento chegar a 80% do padrão nacional, só sobre os bons clientes
seg['lacuna_credito_bons_rs'] = ((0.8 * seg.credito_esperado_por_empresa - seg.credito_por_empresa).clip(lower=0) * seg.bons).where(seg.pouco_atendido, 0)
salvar(seg.round(4), "p3_segmentos.csv")
pa = seg[seg.pouco_atendido].sort_values('lacuna_credito_bons_rs', ascending=False)
salvar(pa.round(4), "p3_pouco_atendidos.csv")
# prioritárias: pouco atendidas e com inadimplência do SCR igual ou menor que a nacional do mesmo setor e porte
salvar(pa[pa.inadimplencia_ate_nacional].round(4), "p3_oportunidades_prioritarias.csv")
# sensibilidade à tolerância da mistura MEI/ME (2ª revisão): quantos segmentos ficam com 5, 10 (oficial) e 15 pontos
base_pa = (seg.indice_atendimento < 0.8) & (seg.bons >= seg.bons_esperados) & (seg.empresas >= 2000) & (seg.secao != 'K')
sens = []
for tol in [5, 10, 15]:
    m = base_pa & (seg.desvio_mei_pontos <= tol); pr = m & seg.inadimplencia_ate_nacional
    sens.append(dict(tolerancia_pontos=tol, pouco_atendidos=int(m.sum()), prioritarios=int(pr.sum()), bons_prioritarios=int(seg.bons[pr].sum()),
                     prioritarios_micro=int((pr & (seg.porte_scr == 'Micro')).sum()), mesmos_prioritarios_da_oficial=int((pr & seg.pouco_atendido).sum())))
salvar(pd.DataFrame(sens), "p3_sensibilidade_mei.csv"); print(pd.DataFrame(sens).to_string())
uf = seg.groupby('uf').agg(empresas=('empresas', 'sum'), bons=('bons', 'sum'), carteira=('carteira', 'sum'), inad=('inad', 'sum'),
     esperado=('credito_esperado', 'sum'), lacuna=('lacuna_credito_bons_rs', 'sum')).reset_index()
uf['bons_pct'] = uf.bons / uf.empresas; uf['indice_atendimento'] = uf.carteira / uf.esperado; uf['inad_scr'] = uf.inad / uf.carteira
salvar(uf.round(4), "p3_resumo_uf.csv")
st = seg.groupby('secao').agg(empresas=('empresas', 'sum'), bons=('bons', 'sum'), carteira=('carteira', 'sum'), inad=('inad', 'sum'),
     p_divida=('p_divida_media', 'mean'), lacuna=('lacuna_credito_bons_rs', 'sum')).reset_index()
st['bons_pct'] = st.bons / st.empresas; st['credito_por_empresa'] = st.carteira / st.empresas; st['inad_scr'] = st.inad / st.carteira
salvar(st.round(4), "p3_resumo_setor.csv")
pd.set_option('display.width', 220)
print('empresas (x10):', int(seg.empresas.sum()), 'bons:', int(seg.bons.sum()), f"({seg.bons.sum()/seg.empresas.sum():.1%})")
print(st.sort_values('bons_pct', ascending=False)[['secao', 'empresas', 'bons_pct', 'credito_por_empresa', 'inad_scr', 'lacuna']].round(3).to_string())
print(uf.sort_values('indice_atendimento')[['uf', 'empresas', 'bons_pct', 'indice_atendimento', 'inad_scr', 'lacuna']].round(3).to_string())
print(len(pa), 'segmentos pouco atendidos'); print(pa.head(25)[['uf', 'secao', 'porte_scr', 'empresas', 'bons', 'bons_pct', 'bons_pct_esperado', 'pct_mei', 'indice_atendimento', 'inad_scr', 'inad_br', 'lacuna_credito_bons_rs']].round(3).to_string())
