# -*- coding: utf-8 -*-
"""Gera metodo/P4_nota_de_risco.md (tabela de pontos v2) a partir dos resultados; nenhum número é digitado à mão."""
import json, pandas as pd, numpy as np, duckdb
from scipy.stats import spearmanr
from base import RAIZ
from p4_tabela import NUM, VARIAVEIS, ORDENADAS, REGRAS
R = RAIZ / "resultados"; P23 = RAIZ / "dados/processados_2023-05"
NOME = {'porte_natureza': 'Porte e natureza jurídica', 'setor': 'Setor (divisão CNAE, 2 dígitos)', 'uf': 'UF', 'simples': 'Simples Nacional', 'idade': 'Idade da empresa',
 'populacao_municipio': 'População do município', 'pib_per_capita_municipio': 'PIB per capita do município', 'capital_social': 'Capital social',
 'atividades_secundarias': 'Atividades secundárias', 'filiais': 'Filiais', 'socios_pf': 'Sócios pessoa física', 'socio_pj': 'Tem sócio pessoa jurídica',
 'historico_socios': 'Histórico dos sócios', 'divida_ativa': 'Dívida ativa da União (perfil)', 'divida_previdenciaria': 'Tem dívida ativa previdenciária'}
br = lambda x, c=2: f"{x:,.{c}f}".replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−')
def K(suf): return pd.read_csv(R / f"p4_scorecard_constantes{suf}.csv").iloc[0]
k, kf = K(''), K('_fechou')
pts = pd.read_csv(R / "p4_scorecard_pontos.csv"); ex = pd.read_csv(R / "p4_exemplo_conta.csv"); junta = json.load(open(R / "p4_scorecard_juncoes.json", encoding='utf-8'))
cortes = pd.read_csv(R / "p4_cortes_faixas.csv").nota.values; fx = pd.read_csv(R / "p4_faixas.csv"); fxf = pd.read_csv(R / "p4_faixas_fechou.csv")
cv = pd.read_csv(R / "p4_curva_aprovacao.csv"); al = pd.read_csv(R / "p4_alerta_discordancia.csv")
junta_f = json.load(open(R / "p4_scorecard_juncoes_fechou.json", encoding='utf-8')); bc = pd.read_csv(R / "p4_bons_clientes.csv")
cal = {n: pd.read_csv(R / f"p4_calibragem_scr_{n}.csv") for n in ['secao', 'uf', 'secao_porte']}
rho = {n: spearmanr(cal[n].nova_divida_prevista_pct, cal[n].inad_scr_pct)[0] for n in ['secao', 'uf']}
fat = cal['secao_porte'].groupby('porte').fator_scr_sobre_nota.median()
nota_ex = k.offset - k.fator * (k.constante_regressao + ex.coeficiente.sum()); chance = k.ODDS_BASE * 2 ** ((nota_ex - k.BASE) / k.PDO); prob = 1 / (1 + chance)
L = ["# P4 — Como foi calculada a nota de risco de crédito e como refazer a conta", "",
"Objetivo: dar a cada empresa ativa uma nota que indique a chance de ela virar mau pagador, usando só o que um banco consegue ver em dados públicos no dia do pedido de crédito. Pedido do Fabian: o cálculo precisa ser verificável, como no anexo das empresas esperadas por cidade (`C2_empresas_esperadas.md`). Este anexo é gerado por `scripts/gerar_anexo_p4.py`; nenhum número foi digitado à mão.", "",
"**Versão 2 (16/10/2026).** Na primeira revisão, algumas faixas tinham sinal invertido quando lidas sozinhas (por exemplo, \"dívida ajuizada\" dava mais pontos), porque variáveis parecidas dividiam o peso entre si. Por decisão do Fabian, a tabela foi refeita: 15 variáveis em faixas fixas, as parecidas reunidas num bloco só, e saíram e-mail, telefone, nome fantasia, dívida ajuizada, anos desde a 1ª dívida, saturação do setor e a faixa etária dos sócios (atributo de pessoa, risco de compliance).", "",
"## O que a nota prevê", "",
"- **Nota oficial (dívida):** chance de a empresa receber **nova inscrição em dívida ativa da União depois de 15/05/2023 que ainda estava ativa na posição de jun/2026** (arquivo PGFN do 2º trimestre de 2026). A janela efetiva é de cerca de 3,1 anos. Inscrições quitadas antes de jun/2026 não aparecem, então a taxa é um piso.",
"- **Segunda nota (fechamento):** chance de a empresa ser baixada (menos reorganização societária) ou ficar inapta até out/2026 (cerca de 3,4 anos).",
"- **Ponto no tempo:** as características são as de mai/2023 (extração da Receita de mai/2023; dívida na posição de mar/2023). População e PIB per capita do município são do IBGE para 2023, publicados depois (efeito desprezível, porque entram em faixas largas).", "",
"## Passo 1 — As 15 variáveis e as suas faixas", "",
"| Variável | Faixas |", "|---|---|"]
for v in VARIAVEIS:
    if v in NUM: fx_txt = ' · '.join(NUM[v][2])
    elif v in ORDENADAS: fx_txt = ' · '.join(ORDENADAS[v]) + (' · sem sócio pessoa física' if v == 'historico_socios' else '')
    elif v == 'porte_natureza': fx_txt = 'MEI · ou porte (ME, EPP, demais) combinado com a natureza (empresário individual, sociedade limitada, sociedade simples, S.A. fechada, EIRELI, outra)'
    elif v == 'setor': fx_txt = 'divisão CNAE de 2 dígitos (as com menos de 200 empresas no treino vão para "outras (raras)")'
    elif v == 'uf': fx_txt = '27 UFs'
    elif v == 'simples': fx_txt = 'optante · excluída do Simples · nunca optou'
    else: fx_txt = 'sim · não'
    L.append(f"| {NOME[v]} | {fx_txt} |")
L += ["", "Regras: o limite inferior pertence à faixa (ex.: capital de exatamente R$ 1.000 fica em \"até R$ 1 mil\"; idade de exatamente 2 anos fica em \"2 a 3 anos\"). Faixa com menos de 200 empresas no treino vai para \"outras (raras)\". As faixas são definidas uma vez em `scripts/p4_tabela.py`, que gera tanto o modelo quanto a calculadora do painel.", "",
"## Passo 2 — Um peso por faixa, com ordem garantida", "",
"Regressão logística com uma coluna 0/1 por faixa (máxima verossimilhança, penalização leve C = 1), treinada com " + br(k.empresas_treino, 0) + " empresas:", "",
"    log-chance de mau = constante + soma dos coeficientes das 15 faixas da empresa", "",
"Nas variáveis ordenadas (perfil de dívida, histórico dos sócios, Simples e dívida previdenciária), se duas faixas vizinhas saem fora de ordem (a de mais risco com peso menor), elas são juntadas e o modelo é refeito. Junções feitas na nota de dívida:", ""]
for v, m in junta.items():
    for novo in sorted(set(m.values())): L.append(f"- {NOME[v]}: \"{novo}\"")
L += ["", "**Por que \"excluída do Simples\" foi juntada a \"optante\".** Sozinha, a exclusão acompanha muito mais nova dívida (cerca de 40% contra 18%). Mas cerca de 2 em cada 3 empresas excluídas já tinham dívida ativa em mai/2023, e essa dívida está na nota pelo perfil de dívida. Com o perfil de dívida na conta, a exclusão não acrescentou risco na média, e a regra de ordem juntou as duas faixas. Para não perder o sinal, a exclusão virou uma **regra de política fora da nota** (abaixo)."]
L += ["", f"Constante: {br(k.constante_regressao, 6)}. Coeficientes: `resultados/p4_scorecard_coeficientes.csv`; junções: `resultados/p4_scorecard_juncoes.json`.", "",
"## Passo 3 — De pesos para pontos", "",
"- **600 pontos** = chance de 20 bons para 1 mau; **a cada 20 pontos a mais, a chance de ser bom dobra**.", "",
f"    fator = 20 ÷ ln 2 = {br(k.fator, 6)}", f"    offset = 600 − fator × ln 20 = {br(k.offset, 6)}",
f"    base por variável = (offset − fator × constante) ÷ 15 = {br(k.base_por_variavel, 6)}", "    pontos da faixa = base por variável − fator × coeficiente", "",
"**Nota = soma dos pontos das 15 faixas da empresa.** Menos pontos = mais risco.", "",
"## Passo 4 — Da nota para a probabilidade e para a faixa", "",
"    chance de bom = 20 × 2 ^ ((nota − 600) ÷ 20)", "    probabilidade de nova dívida ativa = 1 ÷ (1 + chance de bom)", "",
"| Faixa | Nota |", "|---|---|", f"| A | {br(cortes[3], 1)} ou mais |", f"| B | de {br(cortes[2], 1)} até {br(cortes[3], 1)} |", f"| C | de {br(cortes[1], 1)} até {br(cortes[2], 1)} |", f"| D | de {br(cortes[0], 1)} até {br(cortes[1], 1)} |", f"| E | abaixo de {br(cortes[0], 1)} |", "",
"## Tabela de pontos (nota de dívida)", "", "Setor: 87 divisões; ver `resultados/p4_scorecard_pontos.csv` (de " + br(pts[pts.variavel == 'setor'].pontos.min(), 1) + " a " + br(pts[pts.variavel == 'setor'].pontos.max(), 1) + " pontos). UF: de " + br(pts[(pts.variavel == 'uf') & (pts.faixa != 'outras (raras)')].pontos.min(), 1) + " a " + br(pts[(pts.variavel == 'uf') & (pts.faixa != 'outras (raras)')].pontos.max(), 1) + " pontos.", "",
"| Variável | Faixa | Pontos |", "|---|---|---|"]
for v in VARIAVEIS:
    if v in ('setor', 'uf'): continue
    g = pts[(pts.variavel == v) & (pts.faixa != 'outras (raras)')]
    ordem = NUM[v][2] if v in NUM else None
    if ordem: g = g.assign(o=g.faixa.map({c: i for i, c in enumerate(ordem)})).sort_values('o')
    else: g = g.sort_values('pontos', ascending=False)
    for _, r in g.iterrows(): L.append(f"| {NOME[v]} | {r.faixa} | {br(r.pontos, 2)} |")
L += ["", "Leitura (associações observadas, não causas): a idade não é uma linha reta. Empresas com menos de 1 ano recebem muitos pontos; em pouco tempo, poucas chegam a ter tributo inscrito em dívida ativa. O risco delas aparece na nota de fechamento e na regra de política de idade. O risco de nova dívida é maior entre 2 e 5 anos e menor depois dos 10. Mais filiais e sócio único dão menos pontos; uma explicação compatível, não testada, é que essas empresas têm mais tributos a pagar. O capital social é declarado pela própria empresa e a Receita não o confere; o capital zero foi juntado a \"até R$ 1 mil\". Na nota de dívida, a faixa mais baixa tem a maior pontuação e capital acima de R$ 200 mil a menor: empresas maiores têm mais tributo a pagar e, com isso, mais chance de inscrição (hipótese compatível, não testada). Na nota de fechamento a ordem se inverte (capital baixo fecha mais), e um bom cliente precisa de A ou B nas duas notas. A ordem não é imposta no capital porque o risco não anda num só sentido nas duas notas.", "",
"## Regras de política (fora da nota, valem acima dela)", "",
"A nota mede o risco médio. Três situações vão sempre para **análise manual** e nunca contam como \"bom cliente\", qualquer que seja a faixa: " + "; ".join(r for _, r in REGRAS) + ". \"Excluída do Simples\" é a empresa que já optou e hoje não é optante (`opcao_simples = 'N'`); o cadastro não informa o motivo. A regra de idade se apoia no fechamento: essas empresas recebem menos nova dívida que a média, mas fecham mais. No teste (empresas de mai/2023):", "",
"| Grupo | Empresas | % do teste | Nova dívida real | Fechou (real) |", "|---|---|---|---|---|"] + [f"| {r.grupo} | {br(r.empresas, 0)} | {br(r.participacao_pct, 1)}% | {br(r.nova_divida_pct, 1)}% | {br(r.fechou_pct, 1)}% |" for _, r in bc.iterrows()] + ["",
"As empresas A ou B nas duas notas que caem numa regra têm mais nova dívida e mais fechamento que as demais A/B. Fluxo de decisão proposto, nesta ordem: (1) divergência forte com o modelo de referência = análise manual; (2) senão, faixa E da nota de dívida = recusa (abaixo do corte dos 80%); (3) senão, regra de política = análise manual; (4) senão, aprovação pela nota, com prazo curto se a faixa de fechamento for E. Como a recusa vem antes das regras, quase toda empresa com dívida em cobrança sai na faixa E. Proporções no teste, com a fila aberta por motivo: `resultados/p4_fluxo_decisao.csv`. As regras estão em `scripts/p4_tabela.py` (REGRAS) e também na calculadora do painel.", "",
"## Exemplo verificável (empresa real do teste, sem identificação)", "",
"Empresa do teste com nota mais próxima da mediana da faixa C (`resultados/p4_exemplo_conta.csv`).", "",
"| Variável | Faixa da empresa | Coeficiente | Pontos |", "|---|---|---|---|"]
for _, r in ex.iterrows(): L.append(f"| {NOME[r.variavel]} | {r.faixa} | {br(r.coeficiente, 6)} | {br(r.pontos, 2)} |")
s = ex.coeficiente.sum()
L += [f"| **Total** | | {br(s, 6)} | **{br(ex.pontos.sum(), 2)}** |", "",
f"- Pela fórmula: nota = {br(k.offset, 4)} − {br(k.fator, 4)} × ({br(k.constante_regressao, 6)} {'+' if s >= 0 else '−'} {br(abs(s), 6)}) = **{br(nota_ex, 2)}**.",
f"- Chance de bom = 20 × 2^(({br(nota_ex, 2)} − 600) ÷ 20) = {br(chance, 3)}; probabilidade de nova dívida = 1 ÷ (1 + {br(chance, 3)}) = **{br(100 * prob, 1)}%**. Faixa **C**.", "",
"## Segunda nota: fechamento", "",
f"Mesmas variáveis, faixas e escala, com o alvo \"fechou até out/2026\" (constante {br(kf.constante_regressao, 6)}; base por variável {br(kf.base_por_variavel, 6)}). Arquivos com sufixo `_fechou`. As mesmas regras de ordem valem. Junções feitas na nota de fechamento:", ""] + [f"- {NOME[v]}: \"{novo}\"" for v, m in junta_f.items() for novo in sorted(set(m.values()))] + ["",
"Na nota de fechamento, ter dívida previdenciária não muda os pontos (as duas faixas foram juntadas): sem a regra de ordem, ela daria menos risco de fechar (uma explicação compatível, não testada, é que a dívida previdenciária indica empresas com empregados). Juntar as duas faixas é uma escolha conservadora: a política de crédito não premia dívida.", "",
"## Resultado no teste (616.603 empresas que o modelo não viu)", "",
"| Faixa | Nova dívida prevista | Nova dívida real | Fechou (real) | Fechamento real (2ª nota) |", "|---|---|---|---|---|"]
for (_, r), (_, r2) in zip(fx.iterrows(), fxf.iterrows()): L.append(f"| {r.faixa} | {br(r.alvo_previsto_pct, 1)}% | {br(r.alvo_real_pct, 1)}% | {br(r.fechou_pct, 1)}% | {br(r2.alvo_real_pct, 1)}% |")
cmp_ = pd.concat([pd.read_csv(R / f"p4_comparacao_{a}_{e}.csv") for a in ['y_nova_divida', 'y_fechou'] for e in ['geral', 'scorecard']])
L += ["", "| Alvo | Modelo | AUC |", "|---|---|---|"] + [f"| {'nova dívida' if r.alvo == 'y_nova_divida' else 'fechamento'} | {r.modelo} | {br(r.auc, 3)} |" for _, r in cmp_.iterrows()]
L += ["", "A tabela v2 perde um pouco de poder de separação contra o modelo de referência (LightGBM, com todas as variáveis da versão 1), em troca de pesos que respeitam a ordem nas variáveis ordenadas e de uma calculadora simples. Divergências fortes entre os dois (2 faixas ou mais):"]
for _, r in al.iterrows(): L.append(f"- {r.caso}: {br(r.participacao_pct, 1)}% das empresas; nova dívida real {br(r.nova_divida_real_pct, 1)}% (tabela previa {br(r.prevista_scorecard_pct, 1)}%, LightGBM {br(r.prevista_lgbm_pct, 1)}%).")
L += ["", "## Calibragem com a inadimplência bancária (SCR)", "",
f"O SCR do Banco Central não identifica empresas; a comparação é por segmento. A nota prevista média ordena os segmentos como a inadimplência bancária: correlação de postos (Spearman) de {br(rho['secao'], 2)} entre {len(cal['secao'])} setores e de {br(rho['uf'], 2)} entre {len(cal['uf'])} UFs. Fator para converter a chance de nova dívida em inadimplência bancária aproximada (mediana dos setores): MEIs e MEs (porte “Micro” do SCR) {br(fat['Micro'], 2)}; EPPs (porte “Pequena”) {br(fat['Pequeno'], 2)}. Arquivos: `resultados/p4_calibragem_scr_*.csv`.", "",
"## Como refazer do zero", "",
"1. `etl_cnpj.py` com `EXTRACAO=2023-05`; `PGFN_PERIODO=2023T1 etl_pgfn.py`; `montar_base_2023.py`, `pgfn_devedores_2023.py`, `c1_socios_2023.py`, `p4_montar.py`.",
"2. `p4_amostra.py`, `p4_tabela.py` (variáveis v2), `p4_scorecard.py y_nova_divida` e `y_fechou`.",
"3. Conferência: `p4_pontuar.py` (refaz a nota só com as tabelas), `teste_calculadora.py` (a conta do painel), `conferir_p4.py`.",
"4. Para uma empresa nova: achar a faixa de cada variável, aplicar as junções, somar os pontos e converter pela fórmula do passo 4 — ou usar a calculadora do painel."]
(RAIZ / "metodo/P4_nota_de_risco.md").write_text("\n".join(L) + "\n", encoding="utf-8"); print("ok", len(L), round(nota_ex, 2), round(prob, 4))
