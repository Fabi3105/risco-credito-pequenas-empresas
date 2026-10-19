# -*- coding: utf-8 -*-
"""Gráficos do relatório (PNG), com a identidade visual do painel "Mesa de crédito":
azul-petróleo, verde-dinheiro e âmbar; faixas A a E do verde ao vermelho, sempre com a letra escrita (não depender só da cor).
Saída: graficos/*.png"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.ticker
from base import RAIZ, RES
G = RAIZ / "graficos"; G.mkdir(exist_ok=True)
COR = dict(petroleo='#0E3B43', verde='#1F7A4D', ambar='#C98A1B', vermelho='#B03A2E', cinza='#6B7B80', claro='#DCE5E6', fundo='#FFFFFF')
FAIXA = {'A': '#1F6B45', 'B': '#78B088', 'C': '#A9AAA2', 'D': '#E0956A', 'E': '#B03A2E'}   # escala divergente ordinal, cinza no meio
PORTE = {'MEI': '#B07A12', 'ME': '#2F6FA0', 'EPP': '#2E8B57'}   # validada (validate_palette.js): CVD e contraste OK
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.edgecolor': COR['cinza'], 'axes.labelcolor': COR['petroleo'],
                     'xtick.color': COR['petroleo'], 'ytick.color': COR['petroleo'], 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.titleweight': 'bold', 'axes.titlesize': 12, 'axes.titlecolor': COR['petroleo'], 'axes.titlelocation': 'left'})
br = lambda x, c=1: f"{x:,.{c}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
def salvar(fig, nome, fonte):
    fig.text(0.01, 0.01, fonte, fontsize=7.5, color=COR['cinza'], ha='left')
    fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(G / nome, dpi=160, facecolor='white'); plt.close(fig)

# 1. Sobrevivência por porte
g = pd.read_csv(RES / "q1_oficial_grupo.csv").set_index('grupo').loc[['MEI', 'ME', 'EPP']]
fig, ax = plt.subplots(figsize=(7.2, 3.8)); x = np.array([1, 3, 5, 10])
for p, r in g.iterrows():
    y = [r.sobrevive_1a, r.sobrevive_3a, r.sobrevive_5a, r.sobrevive_10a]
    ax.plot(x, y, marker='o', color=PORTE[p], lw=2.2, label=p, ls='-')
    dy = {'EPP': 8, 'ME': -14, 'MEI': -14}[p]
    for xi, yi in zip(x, y): ax.annotate(br(yi), (xi, yi), textcoords='offset points', xytext=(0, dy), ha='center', fontsize=8, color=PORTE[p])
ax.axvspan(7.5, 10.5, color=COR['claro'], alpha=0.6, lw=0); ax.text(9, 101, '10 anos: turmas 2012-2015\n(com aviso)', ha='center', fontsize=7.5, color=COR['cinza'], va='bottom')
ax.set_xticks(x, ['1 ano', '3 anos', '5 anos', '10 anos']); ax.set_ylim(0, 112); ax.set_ylabel('% de empresas abertas')
ax.set_title('Quantas empresas continuam abertas, por porte na abertura'); ax.legend(frameon=False, loc='lower left')
salvar(fig, 'g1_sobrevivencia_porte.png', 'Fonte: Receita Federal (CNPJ, out/2026). Turmas 2016-2020 (1 a 5 anos) e 2012-2015 (10 anos). Fora incorporação imobiliária.')

# 2. Risco anual de baixa voluntária
r = pd.read_csv(RES / "q1_oficial_risco_anual.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.4)); w = 0.26
for i, p in enumerate(['MEI', 'ME', 'EPP']):
    d = r[r.grupo == p]; ax.bar(d.ano_de_vida + (i - 1) * w, d.risco_baixa_voluntaria_pct, w, color=PORTE[p], label=p)
    for xi, yi in zip(d.ano_de_vida + (i - 1) * w, d.risco_baixa_voluntaria_pct): ax.text(xi, yi + 0.2, br(yi), ha='center', fontsize=7)
ax.set_xticks([1, 2, 3, 4, 5], [f'{k}º ano' for k in range(1, 6)]); ax.set_ylabel('% das que chegaram ao ano')
ax.set_title('Encerramento voluntário em cada ano de vida'); ax.legend(frameon=False)
salvar(fig, 'g2_risco_anual.png', 'Fonte: Receita Federal. Turmas 2016-2020. Só baixa voluntária (comparável entre épocas de fiscalização).')

# 3. Setores (ME): sobrevivência em 5 anos e fechamento com dívida
s = pd.read_csv(RES / "q1_oficial_secao.csv"); s = s[(s.grupo == 'ME') & (s.empresas_2016_2020 >= 5000)].sort_values('sobrevive_5a')
NOME = {'A': 'Agropecuária', 'B': 'Extração', 'C': 'Indústria', 'DE': 'Energia e água', 'F': 'Construção', 'G': 'Comércio', 'H': 'Transporte',
        'I': 'Alojamento e alimentação', 'I1': 'Hotéis e pousadas', 'I2': 'Alimentação (restaurantes, bares, entrega)', 'J': 'Informação e comunicação', 'K': 'Financeiro', 'L': 'Imobiliário', 'M': 'Profissionais e técnicas',
        'N': 'Administrativas', 'P': 'Educação', 'Q': 'Saúde', 'R': 'Artes e lazer', 'S': 'Outros serviços'}
fig, ax = plt.subplots(figsize=(7.6, 4.6))
cores = [COR['vermelho'] if v < 67 else COR['petroleo'] for v in s.sobrevive_5a]
ax.barh([NOME[k] for k in s.secao], s.sobrevive_5a, color=cores)
for i, (v, d) in enumerate(zip(s.sobrevive_5a, s.fechou_com_divida_5a)): ax.text(v + 0.5, i, f"{br(v)}%  (com dívida: {br(d)}%)", va='center', fontsize=7.5)
ax.set_xlim(0, 118); ax.set_xticks([0, 20, 40, 60, 80, 100]); ax.set_xlabel('% de MEs abertas que seguem abertas após 5 anos')
ax.set_title('ME: sobrevivência em 5 anos por setor')
salvar(fig, 'g3_setores_me.png', 'Fonte: Receita Federal e PGFN. MEs abertas em 2016-2020 (setores com 5 mil ou mais).\nEntre parênteses: % que fechou deixando dívida ativa.')

# 4. Sinais de risco (P2, retrato de mai/2023)
f = pd.read_csv(RES / "p2b_fatores_2023.csv")
sel = [('dívida ativa da União em mar/2023 (PGFN 2023 T1)', '1 dívida até R$ 10 mil', 'Dívida ativa até R$ 10 mil'),
       ('dívida ativa da União em mar/2023 (PGFN 2023 T1)', '3 dívida acima de R$ 100 mil', 'Dívida ativa acima de R$ 100 mil'),
       ('no Simples Nacional', 'False', 'Saiu do Simples Nacional'), ('histórico dos sócios (C1)', '4 sócio já fechou empresa com dívida ativa', 'Sócio já fechou empresa deixando dívida'),
       ('histórico dos sócios (C1)', '3 sócio tem outra empresa ativa com dívida', 'Sócio tem outra empresa com dívida'),
       ('setor (seção CNAE)', 'I2 Alimentação', 'Alimentação (restaurantes, bares, entrega)'), ('setor (seção CNAE)', 'I1 Alojamento', 'Hotéis e pousadas'),
       ('histórico dos sócios (C1)', '1 sócio tem outra empresa ativa', 'Sócio tem outra empresa sem dívida'),
       ('número de sócios PF', '3 três ou mais', 'Três ou mais sócios'), ('filiais', '2 3 ou mais', 'Três ou mais filiais'),
       ('setor (seção CNAE)', 'Q Saúde', 'Saúde'), ('setor (seção CNAE)', 'L Imobiliário', 'Imobiliário')]
f['valor'] = f.valor.astype(str).str.replace('^false$', 'False', regex=True).str.replace('^true$', 'True', regex=True)
rows = []
for c, v, lab in sel:
    x = f[(f.caracteristica == c) & (f.valor == v)].iloc[0]; rows.append((lab, x.razao, x.razao_nova_divida))
d = pd.DataFrame(rows, columns=['lab', 'fecha', 'divida'])
# leitura direta (pedido do Fabian): quanto % a mais ou a menos essas empresas fecham e recebem nova dívida, contra empresas parecidas
d['fecha_pct'] = 100 * (d.fecha - 1); d['divida_pct'] = 100 * (d.divida - 1); d = d.sort_values('fecha_pct').reset_index(drop=True)
fig, axs = plt.subplots(1, 2, figsize=(8.4, 4.8), sharey=True, gridspec_kw={'width_ratios': [1, 1.35]}); yy = np.arange(len(d))
for ax, col, tit in [(axs[0], 'fecha_pct', 'Fecham'), (axs[1], 'divida_pct', 'Recebem nova dívida ativa')]:
    v = d[col].values; ax.barh(yy, v, color=[COR['vermelho'] if x > 0 else COR['verde'] for x in v], height=0.62)
    ax.axvline(0, color=COR['petroleo'], lw=0.8)
    lim = max(abs(v).max() * 1.35, 60)
    for i, x in enumerate(v): ax.text(x + (lim * 0.02 if x >= 0 else -lim * 0.02), i, ('+' if x > 0 else '−') + f"{abs(x):.0f}%", va='center', ha='left' if x >= 0 else 'right', fontsize=8, color=COR['petroleo'])
    ax.set_xlim(-lim * 0.75 if v.min() < 0 else -lim * 0.25, lim); ax.set_title(tit, fontsize=10.5); ax.set_xticks([])
    ax.spines['bottom'].set_visible(False); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
axs[0].set_yticks(yy, d.lab)
fig.suptitle('Quanto essas empresas fecham e se endividam a mais (vermelho) ou a menos (verde)\nque empresas parecidas, do mesmo porte e da mesma idade', x=0.01, ha='left', fontsize=11, fontweight='bold', color=COR['petroleo'])
salvar(fig, 'g4_fatores.png', 'Exemplo: em dois grupos do mesmo tamanho, se 100 empresas sem dívida fecharam, fecharam 167 das que tinham dívida ativa até R$ 10 mil (+67%).\nFonte: Receita Federal (mai/2023 e out/2026) e PGFN (mar/2023 e jun/2026). Empresas ativas em mai/2023, acompanhadas até out/2026.')

# 5. Faixas A-E: nova dívida prevista x real, e fechamento
fx = pd.read_csv(RES / "p4_faixas.csv").sort_values('faixa')
fig, ax = plt.subplots(figsize=(7.2, 3.6)); x = np.arange(5)
ax.bar(x - 0.2, fx.alvo_real_pct, 0.38, color=[FAIXA[k] for k in fx.faixa], label='nova dívida ativa (real)')
ax.bar(x + 0.2, fx.fechou_pct, 0.38, color='white', edgecolor=COR['petroleo'], hatch='///', label='fechou (real)')
ax.scatter(x - 0.2, fx.alvo_previsto_pct, color=COR['petroleo'], marker='_', s=300, lw=2.5, label='nova dívida prevista', zorder=3)
for i, r_ in fx.reset_index().iterrows(): ax.text(i - 0.2, r_.alvo_real_pct + 1, br(r_.alvo_real_pct), ha='center', fontsize=8); ax.text(i + 0.2, r_.fechou_pct + 1, br(r_.fechou_pct), ha='center', fontsize=8)
ax.set_xticks(x, [f'Faixa {k}' for k in fx.faixa]); ax.set_ylabel('% das empresas da faixa'); ax.set_ylim(0, 55)
ax.set_title('Nota de dívida: o que aconteceu com cada faixa'); ax.legend(frameon=False, fontsize=8, loc='upper left')
salvar(fig, 'g5_faixas.png', 'Fonte: teste com 616.603 empresas que o modelo não viu (ativas em mai/2023). Nova dívida: aberta em jun/2026; fechou: até out/2026.')

# 6. Curva de aprovação (um eixo só; maus deixados de fora como rótulo)
cv = pd.read_csv(RES / "p4_curva_aprovacao.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.4))
ax.plot(cv.aprovacao_pct, cv.alvo_aprovados_pct, marker='o', color=COR['petroleo'], lw=2.2)
for a_, y_, m_ in zip(cv.aprovacao_pct, cv.alvo_aprovados_pct, cv.maus_evitados_pct):
    ax.text(a_, y_ + 0.9, br(y_), ha='center', fontsize=8, color=COR['petroleo'])
    if a_ in (50, 80): ax.annotate(f"{br(m_)}% dos maus\nficam de fora", (a_, y_), xytext=(0, -34), textcoords='offset points', ha='center', fontsize=7.5, color=COR['verde'],
                                   arrowprops=dict(arrowstyle='-', color=COR['verde'], lw=0.8))
ax.set_xlabel('% de propostas aprovadas (as de melhor nota)'); ax.set_ylabel('nova dívida entre aprovados (%)'); ax.set_ylim(0, 22)
ax.set_title('Quanto o risco cai com a nota, conforme o nível de aprovação')
salvar(fig, 'g6_curva_aprovacao.png', 'Fonte: teste do modelo (616.603 empresas). Aprovar 100% = sem filtro (18,5% de nova dívida).')

# 7. Pouco atendidos: índice de atendimento x participação de bons
sg = pd.read_csv(RES / "p3_segmentos.csv"); sg = sg[(sg.empresas >= 2000) & (sg.secao != 'K') & sg.comparavel]
fig, ax = plt.subplots(figsize=(7.2, 4.2))
sg['rel'] = sg.bons / sg.bons_esperados
ax.scatter(sg.indice_atendimento, sg.rel, s=np.clip(sg.empresas / 4000, 6, 160), color=COR['claro'], edgecolor=COR['cinza'], lw=0.5)
pa = sg[sg.pouco_atendido]
ax.scatter(pa.indice_atendimento, pa.rel, s=np.clip(pa.empresas / 4000, 10, 160), color=COR['ambar'], edgecolor=COR['petroleo'], lw=0.6, label='pouco atendido, inadimplência maior')
pa = pa[pa.inadimplencia_ate_nacional]
ax.scatter(pa.indice_atendimento, pa.rel, s=np.clip(pa.empresas / 4000, 10, 160), color=COR['verde'], edgecolor=COR['petroleo'], lw=0.6, label='prioritário')
top = pa.sort_values('lacuna_credito_bons_rs', ascending=False).head(6).reset_index(drop=True)
legenda = []
for i, r_ in top.iterrows():
    ax.annotate(str(i + 1), (r_.indice_atendimento, r_.rel), fontsize=8, fontweight='bold', xytext=(-14 + 6 * (i % 2), 6 + 9 * (i % 3)), textcoords='offset points',
                color=COR['petroleo'], arrowprops=dict(arrowstyle='-', color=COR['petroleo'], lw=0.6))
    legenda.append(f"{i + 1}. {r_.uf} · {NOME.get(r_.secao, r_.secao)} · {'EPP' if r_.porte_scr == 'Pequeno' else 'Micro'}")
ax.text(0.015, 0.03, '\n'.join(legenda), transform=ax.transAxes, fontsize=7.5, color=COR['petroleo'], va='bottom',
        bbox=dict(facecolor='white', edgecolor=COR['claro'], boxstyle='round,pad=0.4'))
ax.axvline(0.8, color=COR['ambar'], ls='--', lw=1); ax.axhline(1, color=COR['ambar'], ls='--', lw=1)
ax.set_xscale('log'); ax.set_xlim(0.25, 4); ax.set_xticks([0.3, 0.5, 0.8, 1, 1.5, 2, 3], ['0,3', '0,5', '0,8', '1', '1,5', '2', '3']); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_xlabel('Crédito do segmento ÷ esperado no padrão nacional do setor e porte'); ax.set_ylabel('Bons clientes ÷ esperados')
ax.set_title('Onde há bons clientes com pouco crédito (UF × setor × porte)'); ax.legend(frameon=False, loc='upper right')
salvar(fig, 'g7_pouco_atendidos.png', 'Fonte: SCR.data/Banco Central (12 meses até ago/2026) e notas aplicadas às empresas ativas em out/2026. Fora atividades financeiras\ne segmentos Micro com mistura MEI/ME diferente da nacional. Numerados: os 6 prioritários com mais crédito em falta.')

# 8. Época da abertura (C3) — um eixo só; Selic dos 12 meses seguintes escrita sob cada barra
c3 = pd.read_csv(RES / "c3_semestres.csv")
fig, ax = plt.subplots(figsize=(7.2, 3.6)); x = np.arange(len(c3))
ax.bar(x, c3.razao_vol_3a, color=[COR['ambar'] if e != 'antes' else COR['petroleo'] for e in c3.epoca])
for i, v in enumerate(c3.razao_vol_3a): ax.text(i, v + 0.01, br(v, 2), ha='center', fontsize=7)
ax.axhline(1, color=COR['cinza'], ls='--', lw=1); ax.set_ylim(0.7, 1.25); ax.set_ylabel('encerramento em 3 anos\n(1 = esperado)')
ax.set_xticks(x, [f"{s_.replace('-S', '/')}\nSelic {br(sl)}" for s_, sl in zip(c3.semestre, c3.selic_12m_seguintes)], fontsize=7)
ax.set_title('Encerramento voluntário em 3 anos por semestre de abertura')
salvar(fig, 'g8_epoca_abertura.png', 'Fonte: Receita Federal e Banco Central (SGS 4189). Âmbar: abertas durante a pandemia. Ajustado pela mistura de porte e setor.\nSelic: média dos 12 meses seguintes à abertura (% a.a.).')

# 9. Destino dos MEIs (C4)
de = pd.read_csv(RES / "c4_mei_destino.csv"); de = de[~de.destino.str.startswith('5')]
lab = {'1': 'Continua MEI', '2': 'Cresceu (saiu do MEI,\nsegue no Simples)', '3': 'Saiu do MEI\ne do Simples', '4': 'Fechou'}
cores = {'1': COR['cinza'], '2': COR['verde'], '3': COR['vermelho'], '4': COR['petroleo']}
fig, ax = plt.subplots(figsize=(7.2, 3.2))
k = [d_[0] for d_ in de.destino]; ax.barh([lab[i] for i in k], de.pct, color=[cores[i] for i in k])
for i, (p_, nd) in enumerate(zip(de.pct, de.nova_divida_pct)): ax.text(p_ + 0.6, i, f"{br(p_)}% dos MEIs · nova dívida: {br(nd)}%", va='center', fontsize=8)
ax.set_xlim(0, 80); ax.invert_yaxis(); ax.set_xlabel('% dos MEIs ativos em mai/2023')
ax.set_title('O que aconteceu com os MEIs de mai/2023 até out/2026')
salvar(fig, 'g9_mei_destino.png', 'Fonte: Receita Federal (mai/2023 e out/2026) e PGFN. 12,2 milhões de MEIs ativos em mai/2023.')
# 10. Alojamento e alimentação por atividade (pedido do Fabian)
ab = pd.read_csv(RES / "q1e_aberturas.csv"); pt = pd.read_csv(RES / "q1e_pandemia_turmas.csv"); q = ab.merge(pt, on='atividade')
q['nome'] = q.atividade.str[2:].str.replace(' (marmitas, entrega)', '\n(marmitas, entrega)', regex=False).str.replace(' (bufê, cantinas)', '\n(bufê, cantinas)', regex=False).str.replace(', casas de chá e de sucos', '', regex=False)
q = q.iloc[::-1].reset_index(drop=True); yy = np.arange(len(q))
fig, axs = plt.subplots(1, 2, figsize=(8.4, 4.2), sharey=True)
v1 = q['cresc_2021_vs_2019_pct']; axs[0].barh(yy, v1, color=COR['ambar'], height=0.6)
for i, x in enumerate(v1): axs[0].text(max(x, 0) + 1, i, (('+' + br(x, 0)) if x >= 0.5 else ('−' + br(-x, 0)) if x <= -0.5 else '0') + '%', va='center', fontsize=8)
axs[0].set_title('Aberturas: 2021\ncontra 2019', fontsize=10); axs[0].set_xlim(-5, 70); axs[0].set_xticks([])
v2 = 100 * (q.razao_pandemia_vs_antes - 1); axs[1].barh(yy, v2, color=COR['vermelho'], height=0.6)
for i, x in enumerate(v2): axs[1].text(x + 0.6, i, '+' + br(x, 0) + '%', va='center', fontsize=8)
axs[1].set_title('Abertas na pandemia: quanto\nmais encerraram em 3 anos', fontsize=10); axs[1].set_xlim(0, 42); axs[1].set_xticks([])
for ax in axs: ax.spines['bottom'].set_visible(False); ax.spines['left'].set_visible(False); ax.tick_params(axis='y', length=0)
axs[0].set_yticks(yy, q.nome, fontsize=8.5)
fig.suptitle('Hotéis e pousadas × alimentação: na pandemia abriram muito mais restaurantes\ne empresas de comida para entrega, que depois fecharam mais', x=0.01, ha='left', fontsize=11, fontweight='bold', color=COR['petroleo'])
salvar(fig, 'g10_alojamento_alimentacao.png', 'Fonte: Receita Federal (out/2026). MEI, ME e EPP. Pandemia: abertas de jul/2020 a dez/2021. Encerramento voluntário, comparado\nao das turmas de 2016-2019 da mesma atividade e do mesmo porte.')

# 11. Fluxograma da decisão de crédito proposta (pedido do Fabian)
from matplotlib.patches import FancyBboxPatch
fl = pd.read_csv(RES / "p4_fluxo_decisao.csv"); fe = lambda k: fl[fl.etapa.str.startswith(k)].iloc[0]
n_rec, n_man, n_apr = [round(10 * fe(k).participacao_pct) for k in ('recusa', 'análise manual', 'aprovação')]
fig, ax = plt.subplots(figsize=(8.0, 6.0)); ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
def caixa(x, y, w, h, txt, cor, fc='white', tc=None, fs=8.6, bold=False):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle='round,pad=0.4,rounding_size=1.6', fc=fc, ec=cor, lw=1.6))
    ax.text(x, y, txt, ha='center', va='center', fontsize=fs, color=tc or COR['petroleo'], fontweight='bold' if bold else 'normal', wrap=True)
def seta(x1, y1, x2, y2, rot=None, lado='right'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle='-|>', color=COR['cinza'], lw=1.3))
    horiz = y1 == y2
    if rot: ax.text((x1 + x2) / 2 + (0 if horiz else 1.2), (y1 + y2) / 2 + (1.8 if horiz else 0), rot, fontsize=8, color=COR['cinza'], ha='center' if horiz else 'left', va='center', fontweight='bold')
XL, X0, XR = 12.5, 50, 87.5   # análise manual à esquerda, perguntas no centro, recusa à direita: nenhuma seta cruza caixa
caixa(X0, 94, 44, 7, 'Proposta de crédito de MEI, microempresa\nou empresa de pequeno porte', COR['petroleo'], fc=COR['claro'], bold=True, fs=9.4)
caixa(X0, 78, 40, 9, '1. A nota e o modelo de referência\ndiscordam muito (2 faixas ou mais)?', COR['petroleo'], fs=9.6)
caixa(X0, 60, 40, 9, '2. A nota de dívida está na faixa E\n(os 20% de maior risco)?', COR['petroleo'], fs=9.6)
caixa(X0, 41, 40, 13, '3. Cai em alguma regra de cautela?\n• aberta há menos de 1 ano\n• saiu do Simples Nacional\n• tem dívida ativa em cobrança', COR['petroleo'], fs=9.6)
caixa(X0, 21, 40, 9, f'APROVAÇÃO PELA NOTA\n{n_apr} de cada 1.000 propostas', COR['verde'], fc='#E3F1E9', tc=COR['verde'], bold=True, fs=9.6)
caixa(X0, 6, 40, 7, 'Se a nota de fechamento estiver na faixa E:\nprazo curto', COR['verde'], fs=9.4)
caixa(XR, 60, 23, 9, f'RECUSA\n{n_rec} de cada 1.000', COR['vermelho'], fc='#F6E3E1', tc=COR['vermelho'], bold=True, fs=9.6)
caixa(XL, 41, 23, 13, f'ANÁLISE MANUAL\n(um analista decide)\n{n_man} de cada 1.000', COR['ambar'], fc='#FBF0DC', tc='#8A5E0E', bold=True, fs=9.6)
seta(X0, 90.3, X0, 82.7); seta(X0, 73.4, X0, 64.6, 'não'); seta(X0, 55.4, X0, 47.2, 'não'); seta(X0, 34.8, X0, 25.6, 'não'); seta(X0, 16.4, X0, 9.6)
seta(X0 + 20.6, 60, XR - 12.4, 60, 'sim'); seta(X0 - 20.6, 41, XL + 12.4, 41, 'sim')
ax.annotate('', xy=(XL, 47.2), xytext=(X0 - 20.6, 78), arrowprops=dict(arrowstyle='-|>', color=COR['cinza'], lw=1.3, connectionstyle='angle,angleA=180,angleB=90,rad=4'))
ax.text(X0 - 25, 79.8, 'sim', fontsize=8, color=COR['cinza'], fontweight='bold', ha='center')
ax.set_title('Como a nota entra na decisão de crédito (fluxo proposto)', pad=2)
salvar(fig, 'g11_fluxo_decisao.png', 'Proporções medidas no teste (616.603 empresas ativas em mai/2023 que o modelo não viu). As regras de cautela impedem a aprovação automática.')
print(sorted(p.name for p in G.glob('*.png')))
