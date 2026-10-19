# -*- coding: utf-8 -*-
"""Conferência automática do relatório: cada número-chave é recalculado dos CSVs, formatado como no texto e procurado
DENTRO DO CONTEXTO da frase (o número e palavras vizinhas). Também procura valores antigos proibidos.
Sai com erro se algo falhar. Rodar depois de toda edição de RELATORIO.md (e do painel)."""
import re, sys, pandas as pd, numpy as np
from base import RAIZ, RES
T = (RAIZ / "RELATORIO.md").read_text(encoding='utf-8')
br = lambda x, c=1: f"{x:,.{c}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
pct = lambda x: br(abs(x), 0)
ok, falhas = 0, []
def chk(nome, valor, contexto):
    """contexto: regex com {v} no lugar do número"""
    global ok
    padrao = contexto.replace('{v}', re.escape(valor))
    if re.search(padrao, T, flags=re.S): ok += 1
    else: falhas.append(f"{nome}: '{valor}' não encontrado no contexto /{contexto}/")
g = pd.read_csv(RES / "q1_oficial_grupo.csv").set_index('grupo')
for p in ['MEI', 'ME', 'EPP']:
    for h in ['1a', '3a', '5a']: chk(f"sobrevive {h} {p}", br(g.loc[p, f'sobrevive_{h}']), p + r" [^.\n]{0,40}{v}%")
    chk(f"10 anos {p}", br(g.loc[p, 'sobrevive_10a']), r"10 anos[^\n]{0,80}" + p + r" {v}%")
chk("MEI 10a voluntária", br(g.loc['MEI', 'sobrevive_10a_so_baixa_voluntaria']), r"sobrevive {v}% em 10 anos")
chk("validação vol MEI", br(100 - g.loc['MEI', 'sobrevive_5a_so_baixa_voluntaria']), r"MEI {v}%, ME")
chk("validação vol ME", br(100 - g.loc['ME', 'sobrevive_5a_so_baixa_voluntaria']), r"ME {v}%, EPP")
chk("validação vol EPP", br(100 - g.loc['EPP', 'sobrevive_5a_so_baixa_voluntaria']), r"EPP {v}% nesta base")
r = pd.read_csv(RES / "q1_oficial_risco_anual.csv"); r1 = r[r.ano_de_vida == 1].set_index('grupo').risco_baixa_voluntaria_pct
chk("risco 1º ano MEI", br(r1['MEI']), r"MEI {v}%"); chk("risco 1º ano ME", br(r1['ME']), r"1º ano: MEI [0-9,]+%, ME {v}%"); chk("risco 1º ano EPP", br(r1['EPP']), r"EPP {v}%; do 3º")
s = pd.read_csv(RES / "q1_oficial_secao.csv"); me = s[s.grupo == 'ME'].set_index('secao')
chk("ME alimentação 5a", br(me.loc['I2', 'sobrevive_5a']), r"{v}% na alimentação"); chk("ME hotéis 5a", br(me.loc['I1', 'sobrevive_5a']), r"meio da tabela \({v}%\)"); chk("ME comércio 5a", br(me.loc['G', 'sobrevive_5a']), r"{v}% no comércio")
chk("dívida I2", br(me.loc['I2', 'fechou_com_divida_5a']), r"dívida ativa \({v}% e"); chk("dívida G", br(me.loc['G', 'fechou_com_divida_5a']), r"e {v}%\)")
f = pd.read_csv(RES / "p2b_fatores_2023.csv"); f['valor'] = f.valor.astype(str)
def fv(c, v, col): return f[(f.caracteristica.str.startswith(c)) & (f.valor == v)][col].iloc[0]
chk("dívida até 10 mil fecha", pct(100 * (fv('dívida ativa', '1 dívida até R$ 10 mil', 'razao') - 1)), r"fecharam {v}% mais")
chk("dívida até 10 mil nova", pct(100 * (fv('dívida ativa', '1 dívida até R$ 10 mil', 'razao_nova_divida') - 1)), r"receberam {v}% mais nova dívida")
chk("dívida >100 mil nova", pct(100 * (fv('dívida ativa', '3 dívida acima de R$ 100 mil', 'razao_nova_divida') - 1)), r"100 mil, {v}% mais nova dívida")
chk("excluída Simples fecha", pct(100 * (fv('no Simples', 'false', 'razao') - 1)), r"fecha {v}% mais e recebe")
chk("excluída Simples nova", pct(100 * (fv('no Simples', 'false', 'razao_nova_divida') - 1)), r"recebe {v}% mais nova dívida\.")
chk("sócio fechou c/ dívida fecha", pct(100 * (fv('histórico', '4 sócio já fechou empresa com dívida ativa', 'razao') - 1)), r"fechamento {v}% maior")
chk("sócio fechou c/ dívida nova", pct(100 * (fv('histórico', '4 sócio já fechou empresa com dívida ativa', 'razao_nova_divida') - 1)), r"maior e {v}% mais nova dívida")
chk("sócio outra sem dívida", pct(100 * (fv('histórico', '1 sócio tem outra empresa ativa', 'razao') - 1)), r"associado a {v}% menos fechamento")
chk("3+ sócios", pct(100 * (fv('número de sócios', '3 três ou mais', 'razao') - 1)), r"três ou mais sócios \({v}% menos\)")
chk("3+ filiais fecha", pct(100 * (fv('filiais', '2 3 ou mais', 'razao') - 1)), r"três ou mais filiais \({v}% menos\)")
chk("3+ filiais nova", pct(100 * (fv('filiais', '2 3 ou mais', 'razao_nova_divida') - 1)), r"nova dívida \({v}% mais\)")
chk("alimentação fecha", pct(100 * (fv('setor', 'I2 Alimentação', 'razao') - 1)), r"alimentação {v}% acima"); chk("hotéis fecham", pct(100 * (fv('setor', 'I1 Alojamento', 'razao') - 1)), r"hotéis e pousadas {v}% abaixo")
chk("sumário alimentação", pct(100 * (fv('setor', 'I2 Alimentação', 'razao') - 1)), r"fecha {v}% mais que empresas do mesmo porte"); chk("sumário hotéis", pct(100 * (fv('setor', 'I1 Alojamento', 'razao') - 1)), r"hotéis e pousadas fecham {v}% menos")
chk("imobiliário fecha", pct(100 * (fv('setor', 'L Imobiliário', 'razao') - 1)), r"imobiliário {v}% abaixo")
chk("saúde fecha", pct(100 * (fv('setor', 'Q Saúde', 'razao') - 1)), r"saúde {v}% abaixo")
c3 = pd.read_csv(RES / "c3_semestres.csv").set_index('semestre').razao_vol_3a
chk("C3 2020-S2", pct(100 * (c3['2020-S2'] - 1)), r"{v}% \(2020/2\)"); chk("C3 2021-S1", pct(100 * (c3['2021-S1'] - 1)), r"{v}% \(2021/1\)"); chk("C3 2021-S2", pct(100 * (c3['2021-S2'] - 1)), r"{v}% \(2021/2\)")
fx = pd.read_csv(RES / "p4_faixas.csv").set_index('faixa')
for k in 'ABCDE': chk(f"faixa {k} real", br(fx.loc[k, 'alvo_real_pct']), r"{v}% na " + (r"faixa " if k in 'AE' else '') + k)
chk("faixa E maus", br(fx.loc['E', 'participacao_maus_pct']), r"reúne {v}% dos maus")
chk("faixa A fechou", br(fx.loc['A', 'fechou_pct']), r"{v}% das empresas fecharam")
ff = pd.read_csv(RES / "p4_faixas_fechou.csv").set_index('faixa')
chk("fechamento A", br(ff.loc['A', 'alvo_real_pct']), r"{v}% de fechamento na faixa A"); chk("fechamento E", br(ff.loc['E', 'alvo_real_pct']), r"{v}% na E\.")
cv = pd.read_csv(RES / "p4_curva_aprovacao.csv").set_index('aprovacao_pct')
chk("curva 100", br(cv.loc[100, 'alvo_aprovados_pct']), r"de {v}% para"); chk("curva 80", br(cv.loc[80, 'alvo_aprovados_pct']), r"cai de [0-9,]+% para {v}%")
chk("curva 50", br(cv.loc[50, 'alvo_aprovados_pct']), r"para {v}% e"); chk("curva 50 evitados", br(cv.loc[50, 'maus_evitados_pct']), r"{v}% dos maus ficam")
chk("curva 80 evitados", br(cv.loc[80, 'maus_evitados_pct']), r"com {v}% dos maus")
cmp_ = pd.concat([pd.read_csv(RES / f"p4_comparacao_{a}_{e}.csv") for a in ['y_nova_divida', 'y_fechou'] for e in ['geral', 'scorecard']])
auc = lambda a, m: cmp_[(cmp_.alvo == a) & (cmp_.modelo.str.startswith(m))].auc.iloc[0]
# AUC com 2 casas no texto (o CSV guarda 4; 3 casas a partir de 4 dariam arredondamento duplo)
chk("AUC scorecard", br(auc('y_nova_divida', 'Scorecard'), 2), r"{v} contra"); chk("AUC LGBM", br(auc('y_nova_divida', 'LightGBM, com'), 2), r"contra {v}")
chk("AUC fechamento", br(auc('y_fechou', 'Scorecard'), 2), r"fechamento {v} e"); chk("AUC fechamento LGBM", br(auc('y_fechou', 'LightGBM, com'), 2), r"fechamento [0-9,]+ e {v}")
bc = pd.read_csv(RES / "p4_bons_clientes.csv").set_index('grupo')
of = bc[bc.index.str.contains('definição oficial')].iloc[0]; ba = bc[bc.index.str.contains('barrada')].iloc[0]
chk("bons teste nova dívida", br(of.nova_divida_pct), r"receberam nova dívida em {v}% dos casos"); chk("bons teste na seção 5", br(of.nova_divida_pct), r"taxa de {v}% dos bons")
chk("barrados nova dívida", br(ba.nova_divida_pct), r"nova dívida em {v}% dos casos e fecharam"); chk("barrados fechou", br(ba.fechou_pct, 0), r"fecharam em {v}%, contra")
chk("oficial vs barrados", br(of.nova_divida_pct), r"contra {v}% e"); chk("oficial fechou", br(of.fechou_pct, 0), r"e {v}% das demais")
cps = pd.read_csv(RES / "p4_calibragem_scr_secao_porte.csv").groupby('porte').fator_scr_sobre_nota.median()
chk("fator micro", br(cps['Micro'], 2), r"\({v} para MEIs e MEs"); chk("fator pequenas", br(cps['Pequeno'], 2), r"{v} para EPPs")
fx_ = pd.read_csv(RES / "p4_faixas.csv"); chk("previsto x real < 1 ponto", "1" if (fx_.alvo_previsto_pct - fx_.alvo_real_pct).abs().max() < 1 else "X", r"a menos de {v} ponto em todas")
al = pd.read_csv(RES / "p4_alerta_discordancia.csv"); forte = al[al.caso.str.contains('2\\+')].participacao_pct.sum()
chk("alerta", br(forte), r"\({v}% das empresas\)")
cs = pd.read_csv(RES / "p4_calibragem_scr_secao.csv"); cu = pd.read_csv(RES / "p4_calibragem_scr_uf.csv")
from scipy.stats import spearmanr
chk("Spearman seção", br(spearmanr(cs.nova_divida_prevista_pct, cs.inad_scr_pct)[0], 2), r"{v} por setor"); chk("Spearman UF", br(spearmanr(cu.nova_divida_prevista_pct, cu.inad_scr_pct)[0], 2), r"{v} por estado")
seg = pd.read_csv(RES / "p3_segmentos.csv"); pa = pd.read_csv(RES / "p3_pouco_atendidos.csv"); pr = pd.read_csv(RES / "p3_oportunidades_prioritarias.csv")
chk("bons total", br(seg.bons.sum() / 1e6), r"{v} milhões"); chk("bons pct", br(100 * seg.bons.sum() / seg.empresas.sum()), r"{v}% dos MEIs")
chk("pouco atendidos", str(len(pa)), r"\*\*{v}\*\*|{v} segmentos"); chk("prioritários", str(len(pr)), r"{v} segmentos|\*\*{v}\*\*")
chk("prioritários SP", str((pr.uf == "SP").sum()), r"{v} deles em São Paulo"); chk("bons prioritários", br(pr.bons.sum() / 1000, 0), r"{v} mil bons clientes")
chk("outros pouco atendidos", str(len(pa) - len(pr)), r"outros {v} segmentos")
sen = pd.read_csv(RES / "p3_sensibilidade_mei.csv").set_index('tolerancia_pontos')
chk("sensibilidade 5", str(sen.loc[5, 'prioritarios']), r"com 5 pontos, ficam {v} prioritários"); chk("sensibilidade 15", str(sen.loc[15, 'prioritarios']), r"com 15 pontos, os mesmos {v}")
peso = pr[(pr.porte_scr == 'Micro') & (((pr.uf == 'SP') & (pr.secao == 'H')) | ((pr.uf == 'MG') & (pr.secao == 'F')))]
chk("peso transporte+construção", br(100 * peso.bons.sum() / pr.bons.sum(), 0), r"somam {v}% dos bons clientes prioritários")
chk("bons transporte SP", br(peso[peso.uf == 'SP'].bons.iloc[0] / 1000, 0), r"{v} mil bons clientes\) e construção"); chk("bons construção MG", br(peso[peso.uf == 'MG'].bons.iloc[0] / 1000, 0), r"construção em MG \({v} mil\)")
sp = pr[(pr.uf == 'SP') & (pr.porte_scr == 'Pequeno')]
chk("SP EPP n", str(len(sp)), r"\({v} dos [0-9]+\)"); chk("SP EPP índice faixa", br(sp.indice_atendimento.min(), 3), r"índice de {v} a"); chk("SP EPP índice faixa max", br(sp.indice_atendimento.max(), 3), r"a {v}\)")
chk("SP EPP índice min", pct(100 * (1 - sp.indice_atendimento.max())), r"fica {v}% a"); chk("SP EPP índice max", pct(100 * (1 - sp.indice_atendimento.min())), r"a {v}% abaixo")
uf = pd.read_csv(RES / "p3_resumo_uf.csv").set_index('uf')
chk("RS índice", pct(100 * (uf.loc['RS', 'indice_atendimento'] - 1)), r"recebe {v}% mais crédito")
rs = seg[seg.uf == 'RS'].set_index(['secao', 'porte_scr'])
chk("RS construção", pct(100 * (1 - rs.loc[('F', 'Micro'), 'indice_atendimento'])), r"construção \({v}% menos"); chk("RS imobiliário", pct(100 * (1 - rs.loc[('L', 'Micro'), 'indice_atendimento'])), r"imobiliário \({v}% menos")
de = pd.read_csv(RES / "c4_mei_destino.csv").set_index('destino')
cr = de[de.index.str.startswith('2')].iloc[0]; sa = de[de.index.str.startswith('3')].iloc[0]
chk("MEI cresceu pct", br(cr.pct), r"{v}% saíram do MEI"); chk("MEI cresceu nova", br(cr.nova_divida_pct), r"{v}% deles receberam"); chk("MEI cresceu mil", br(cr.n / 1000, 0), r"\({v} mil;")
chk("MEI virou EPP", br(cr.virou_epp / 1000), r"{v} mil já são EPP"); chk("saiu MEI e Simples", br(sa.nova_divida_pct), r"em {v}% dos casos")
pi = pd.read_csv(RES / "p5_pilotos.csv")
def pn(porte, cen): return pi[(pi.porte == porte) & (pi.cenario.str.startswith(cen))].iloc[0]
for porte, nome in [('Micro', 'MEI e ME'), ('Pequeno', 'EPP')]:
    for cen, rot in [('otimista', 'otimista'), ('conservador', 'conservador')]:
        r_ = pn(porte, cen)
        chk(f"piloto {porte} {cen}", br(r_.concessoes_por_grupo, 0), rf"\| {nome} \| {rot} \(−{pct(r_.reducao_relativa_pct)}%\) \| {br(r_.inad_hoje_pct, 2)}% \| {br(r_.inad_esperada_pct, 2)}% \| {{v}} \|")
        chk(f"piloto {porte} {cen} no sumário", br(r_.concessoes_por_grupo, 0), r"{v}")
conv = pi[pi.piloto.str.startswith('2')].iloc[0]; chk("conversão n", br(conv.concessoes_por_grupo, 0), r"{v} empresas")
vi = pd.read_csv(RES / "p5_viabilidade.csv").set_index('propostas_aprovaveis_por_mes_no_porte'); nc = pn('Micro', 'conservador').concessoes_por_grupo
chk("viabilidade 1000/mês", br(vi.loc[1000, 'meses_minimos_micro_conservador'], 0), r"isso leva {v} meses"); chk("viabilidade n", br(nc, 0), r"precisa de {v} concessões")
chk("viabilidade 6 meses", br(round(nc / (0.5 * 0.8 * 6), -2), 0), r"cerca de {v} por mês"); chk("viabilidade 6 meses no calendário", br(round(nc / (0.5 * 0.8 * 6), -2), 0), r"cerca de {v} propostas aprováveis")
fl = pd.read_csv(RES / "p4_fluxo_decisao.csv"); fe = lambda k: fl[fl.etapa.str.startswith(k)].iloc[0]
chk("fluxo recusa", br(fe('recusa').participacao_pct), r"recusa {v}% das propostas"); chk("fluxo manual", br(fe('análise manual').participacao_pct), r"manda {v}% para análise manual")
chk("fluxo aprova", br(fe('aprovação').participacao_pct), r"aprova {v}% pela nota"); chk("fluxo 1 em 4", "1 em cada 4" if 20 <= fe('análise manual').pct_das_aprovaveis <= 30 else "X", r"Cerca de {v} propostas")
chk("fila novas", br(fe('  motivo: aberta').participacao_pct), r"abertas há menos de 1 ano \({v}% das propostas"); chk("fila novas dívida", br(fe('  motivo: aberta').nova_divida_pct), r"aprovadas pela nota \({v}% contra")
chk("aprovados dívida", br(fe('aprovação').nova_divida_pct), r"contra {v}%\), mas"); chk("fila novas fechou", br(fe('  motivo: aberta').fechou_pct), r"fecham mais \({v}% contra"); chk("aprovados fechou", br(fe('aprovação').fechou_pct), r"contra {v}%\): o analista")
chk("três quartos da fila", "três quartos" if 0.70 <= fe('  motivo: aberta').participacao_pct / fe('análise manual').participacao_pct <= 0.80 else "X", r"(?i)cerca de {v} da fila"); r_ = fe('recusa'); n_rec = round(10 * r_.participacao_pct); n_mau = round(10 * r_.participacao_pct * r_.nova_divida_pct / 100)
chk("por mil recusadas", str(n_rec), r"entre as {v} recusadas"); chk("por mil maus", str(n_mau), r"recusadas, {v} ficariam"); chk("por mil bons recusados", str(n_rec - n_mau), r"e {v} não\.")
chk("por mil analistas", str(round(10 * fe('análise manual').participacao_pct)), r"{v} para analistas"); chk("por mil aprovadas", str(round(10 * fe('aprovação').participacao_pct)), r"são {v} aprovadas")
for porte, rot in [('Micro', 'para MEIs e MEs'), ('Pequeno', 'para EPPs')]:
    inad = round(n_rec * cps[porte] * r_.nova_divida_pct / 100)   # inadimplentes bancários aproximados (fator do SCR por porte)
    rb = 10 * r_.participacao_pct; ib = rb * cps[porte] * r_.nova_divida_pct / 100   # razão com os valores sem arredondar
    chk(f"equilíbrio {porte}", br((rb - ib) / ib), r"{v} " + rot)
    if porte == 'Micro': chk("inadimplentes recusados", str(inad), r"cerca de {v} maus pagadores"); chk("bons recusados SCR", str(n_rec - inad), r"e {v} bons pagadores")
chk("por mil fila sem novas", str(round(10 * fe('  fila sem').participacao_pct)), r"\({v} a cada 1.000\)")
qs = pd.read_csv(RES / "q1_oficial_secao.csv"); chk("agro MEI 2016-20", br(100 - qs[(qs.grupo == 'MEI') & (qs.secao == 'A')].sobrevive_5a.iloc[0]), r"{v}% nas de 2016 a 2020")
q5 = pd.read_csv(RES / "q1e_atividades.csv").set_index('atividade'); qa = pd.read_csv(RES / "q1e_aberturas.csv").set_index('atividade'); qp = pd.read_csv(RES / "q1e_pandemia_turmas.csv").set_index('atividade')
H, RE, EN = '1 Hotéis, pousadas e outros alojamentos', '2 Restaurantes', '6 Comida preparada para consumo em casa (marmitas, entrega)'
chk("hotéis 5a", br(q5.loc[H, 'sobrevive_5a']), r"{v}% seguem abertos após 5 anos \(dois terços"); chk("hotéis razão", pct(100 * (1 - q5.loc[H, 'razao_fechamento_5a'])), r"com {v}% menos fechamento")
chk("aberturas restaurantes", pct(qa.loc[RE, 'cresc_2021_vs_2019_pct']), r"cresceram {v}% em restaurantes"); chk("aberturas entrega", pct(qa.loc[EN, 'cresc_2021_vs_2019_pct']), r"e {v}% em comida para entrega \(")
chk("pandemia restaurantes", pct(100 * (qp.loc[RE, 'razao_pandemia_vs_antes'] - 1)), r"encerraram {v}% e"); chk("pandemia entrega", pct(100 * (qp.loc[EN, 'razao_pandemia_vs_antes'] - 1)), r"e {v}% mais em três anos")
chk("pandemia hotéis", pct(100 * (qp.loc[H, 'razao_pandemia_vs_antes'] - 1)), r"\(hotéis e pousadas, {v}%\)")
al = q5.drop(index=[H, '7 Alimentação para empresas e eventos (bufê, cantinas)']).razao_fechamento_5a
chk("alimentação razão min", pct(100 * (al.min() - 1)), r"fecham {v}% a"); chk("alimentação razão max", pct(100 * (al.max() - 1)), r"a {v}% mais que as outras atividades")
chk("fila sem novas", br(fe('  fila sem').participacao_pct), r"fila cai para {v}%")
bc2 = pd.read_csv(RES / "p4_bons_clientes.csv").set_index('grupo')
chk("regra idade nova dívida", br(bc2.loc['regra: aberta há menos de 1 ano', 'nova_divida_pct']), r"menos nova dívida \({v}%"); chk("regra idade fechou", br(bc2.loc['regra: aberta há menos de 1 ano', 'fechou_pct']), r"fecham mais \({v}%")
chk("todas fechou", br(bc2.loc['todas as empresas do teste', 'fechou_pct']), r"contra {v}%\)")
# valores antigos proibidos (números que mudaram ao longo do estudo)
PROIBIDOS = [r"6,1% na faixa A", r"41,8% na", r"45,2%", r"0,730 contra", r"\(2,3% das", r"6,3 milhões", r"26,3%", r"32 segmentos", r"2\.176", r"1\.571", r"3,4 anos", r"Só 7,2%", r"porque pagam", r"\bprotege\b", r"não explicam", r"0,726\b", r"AUC 0,726", r"6,77 milhões de empresas", r"\b70,0%\b", r"\b60,2%\b", r"49,1%", r"62,9%", r"2,65 vez", r"13 deles em São Paulo", r"5,6 milhões", r"23,6%", r"247 mil", r"0,722", r"74,2%", r"por isso há duas notas", r"sempre no sentido esperado", r"\(4,6%", r"0,39 para micro", r"\b7,9%", r"0,730", r"0,698", r"8 deles em São Paulo", r"leva à exclusão", r"72 a 91", r"Um modelo por setor não foi melhor", r"3\.400", r"leva 20 meses", r"1,4 vez", r"propostas por mês:\*\*", r"_lixo", r"projeto 9,0", r"para que declarar zero não renda", r"Quase toda empresa excluída", r"fila é quase toda", r"17% menos fechamento", r"4% a 10% mais", r"\bmicro de 5,85", r"grande de micro", r"alojamento e alimentação, e comércio", r"alojamento e alimentação 18%", r"22% a 31% abaixo do padrão nacional do setor, com mais bons clientes e inadimplência menor\.$"]
for p_ in PROIBIDOS:
    if re.search(p_, T, flags=re.M): falhas.append(f"valor antigo encontrado: /{p_}/")
print(f"{ok} conferências OK, {len(falhas)} falhas")
for x in falhas: print(" -", x)
sys.exit(1 if falhas else 0)
