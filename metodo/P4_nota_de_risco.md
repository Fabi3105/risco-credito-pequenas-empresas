# P4 — Como foi calculada a nota de risco de crédito e como refazer a conta

Objetivo: dar a cada empresa ativa uma nota que indique a chance de ela virar mau pagador, usando só o que um banco consegue ver em dados públicos no dia do pedido de crédito. Pedido do Fabian: o cálculo precisa ser verificável, como no anexo das empresas esperadas por cidade (`C2_empresas_esperadas.md`). Este anexo é gerado por `scripts/gerar_anexo_p4.py`; nenhum número foi digitado à mão.

**Versão 2 (16/10/2026).** Na primeira revisão, algumas faixas tinham sinal invertido quando lidas sozinhas (por exemplo, "dívida ajuizada" dava mais pontos), porque variáveis parecidas dividiam o peso entre si. Por decisão do Fabian, a tabela foi refeita: 15 variáveis em faixas fixas, as parecidas reunidas num bloco só, e saíram e-mail, telefone, nome fantasia, dívida ajuizada, anos desde a 1ª dívida, saturação do setor e a faixa etária dos sócios (atributo de pessoa, risco de compliance).

## O que a nota prevê

- **Nota oficial (dívida):** chance de a empresa receber **nova inscrição em dívida ativa da União depois de 15/05/2023 que ainda estava ativa na posição de jun/2026** (arquivo PGFN do 2º trimestre de 2026). A janela efetiva é de cerca de 3,1 anos. Inscrições quitadas antes de jun/2026 não aparecem, então a taxa é um piso.
- **Segunda nota (fechamento):** chance de a empresa ser baixada (menos reorganização societária) ou ficar inapta até out/2026 (cerca de 3,4 anos).
- **Ponto no tempo:** as características são as de mai/2023 (extração da Receita de mai/2023; dívida na posição de mar/2023). População e PIB per capita do município são do IBGE para 2023, publicados depois (efeito desprezível, porque entram em faixas largas).

## Passo 1 — As 15 variáveis e as suas faixas

| Variável | Faixas |
|---|---|
| Porte e natureza jurídica | MEI · ou porte (ME, EPP, demais) combinado com a natureza (empresário individual, sociedade limitada, sociedade simples, S.A. fechada, EIRELI, outra) |
| Setor (divisão CNAE, 2 dígitos) | divisão CNAE de 2 dígitos (as com menos de 200 empresas no treino vão para "outras (raras)") |
| UF | 27 UFs |
| Simples Nacional | nunca optou · optante · excluída do Simples |
| Idade da empresa | menos de 1 ano · 1 a 2 anos · 2 a 3 anos · 3 a 5 anos · 5 a 10 anos · 10 a 20 anos · 20 anos ou mais |
| População do município | até 20 mil hab. · 20 a 100 mil hab. · 100 a 500 mil hab. · 500 mil a 1 milhão hab. · mais de 1 milhão hab. |
| PIB per capita do município | até R$ 20 mil · R$ 20 a 30 mil · R$ 30 a 45 mil · R$ 45 a 65 mil · mais de R$ 65 mil |
| Capital social | até R$ 1 mil (inclui zero) · R$ 1 a 10 mil · R$ 10 a 50 mil · R$ 50 a 200 mil · mais de R$ 200 mil |
| Atividades secundárias | nenhuma · 1 a 2 · 3 a 5 · 6 ou mais |
| Filiais | nenhuma · 1 a 2 · 3 ou mais |
| Sócios pessoa física | nenhum · 1 · 2 · 3 ou mais |
| Tem sócio pessoa jurídica | sim · não |
| Histórico dos sócios | sócio tem outra empresa ativa sem dívida · sócio já fechou empresa sem dívida · única empresa dos sócios · sócio tem outra empresa ativa com dívida · sócio já fechou empresa deixando dívida · sem sócio pessoa física |
| Dívida ativa da União (perfil) | sem dívida · só parcelada ou garantida · em cobrança até R$ 10 mil · em cobrança de R$ 10 a 100 mil · em cobrança acima de R$ 100 mil |
| Tem dívida ativa previdenciária | não · sim |

Regras: o limite inferior pertence à faixa (ex.: capital de exatamente R$ 1.000 fica em "até R$ 1 mil"; idade de exatamente 2 anos fica em "2 a 3 anos"). Faixa com menos de 200 empresas no treino vai para "outras (raras)". As faixas são definidas uma vez em `scripts/p4_tabela.py`, que gera tanto o modelo quanto a calculadora do painel.

## Passo 2 — Um peso por faixa, com ordem garantida

Regressão logística com uma coluna 0/1 por faixa (máxima verossimilhança, penalização leve C = 1), treinada com 1.435.792 empresas:

    log-chance de mau = constante + soma dos coeficientes das 15 faixas da empresa

Nas variáveis ordenadas (perfil de dívida, histórico dos sócios, Simples e dívida previdenciária), se duas faixas vizinhas saem fora de ordem (a de mais risco com peso menor), elas são juntadas e o modelo é refeito. Junções feitas na nota de dívida:

- Simples Nacional: "optante / excluída do Simples"
- Histórico dos sócios: "sócio tem outra empresa ativa sem dívida / sócio já fechou empresa sem dívida"
- Dívida ativa da União (perfil): "só parcelada ou garantida / em cobrança até R$ 10 mil"

**Por que "excluída do Simples" foi juntada a "optante".** Sozinha, a exclusão acompanha muito mais nova dívida (cerca de 40% contra 18%). Mas cerca de 2 em cada 3 empresas excluídas já tinham dívida ativa em mai/2023, e essa dívida está na nota pelo perfil de dívida. Com o perfil de dívida na conta, a exclusão não acrescentou risco na média, e a regra de ordem juntou as duas faixas. Para não perder o sinal, a exclusão virou uma **regra de política fora da nota** (abaixo).

Constante: −0,049004. Coeficientes: `resultados/p4_scorecard_coeficientes.csv`; junções: `resultados/p4_scorecard_juncoes.json`.

## Passo 3 — De pesos para pontos

- **600 pontos** = chance de 20 bons para 1 mau; **a cada 20 pontos a mais, a chance de ser bom dobra**.

    fator = 20 ÷ ln 2 = 28,853901
    offset = 600 − fator × ln 20 = 513,561438
    base por variável = (offset − fator × constante) ÷ 15 = 34,331692
    pontos da faixa = base por variável − fator × coeficiente

**Nota = soma dos pontos das 15 faixas da empresa.** Menos pontos = mais risco.

## Passo 4 — Da nota para a probabilidade e para a faixa

    chance de bom = 20 × 2 ^ ((nota − 600) ÷ 20)
    probabilidade de nova dívida ativa = 1 ÷ (1 + chance de bom)

| Faixa | Nota |
|---|---|
| A | 578,0 ou mais |
| B | de 568,9 até 578,0 |
| C | de 560,7 até 568,9 |
| D | de 550,3 até 560,7 |
| E | abaixo de 550,3 |

## Tabela de pontos (nota de dívida)

Setor: 87 divisões; ver `resultados/p4_scorecard_pontos.csv` (de 22,6 a 65,5 pontos). UF: de 30,3 a 38,9 pontos.

| Variável | Faixa | Pontos |
|---|---|---|
| Porte e natureza jurídica | Demais · outra natureza | 54,85 |
| Porte e natureza jurídica | ME · outra natureza | 37,78 |
| Porte e natureza jurídica | EPP · sociedade limitada | 36,94 |
| Porte e natureza jurídica | ME · sociedade limitada | 36,26 |
| Porte e natureza jurídica | Demais · sociedade limitada | 35,69 |
| Porte e natureza jurídica | EPP · outra natureza | 35,31 |
| Porte e natureza jurídica | Demais · S.A. fechada | 34,25 |
| Porte e natureza jurídica | ME · sociedade simples | 33,88 |
| Porte e natureza jurídica | Demais · sociedade simples | 32,69 |
| Porte e natureza jurídica | EPP · sociedade simples | 31,13 |
| Porte e natureza jurídica | Demais · empresário individual | 29,36 |
| Porte e natureza jurídica | EPP · empresário individual | 29,07 |
| Porte e natureza jurídica | MEI | 27,85 |
| Porte e natureza jurídica | ME · empresário individual | 27,02 |
| Simples Nacional | nunca optou | 39,38 |
| Simples Nacional | optante / excluída do Simples | 30,70 |
| Idade da empresa | menos de 1 ano | 39,15 |
| Idade da empresa | 1 a 2 anos | 27,99 |
| Idade da empresa | 2 a 3 anos | 20,54 |
| Idade da empresa | 3 a 5 anos | 23,19 |
| Idade da empresa | 5 a 10 anos | 34,14 |
| Idade da empresa | 10 a 20 anos | 43,98 |
| Idade da empresa | 20 anos ou mais | 52,74 |
| População do município | até 20 mil hab. | 40,94 |
| População do município | 20 a 100 mil hab. | 36,14 |
| População do município | 100 a 500 mil hab. | 32,31 |
| População do município | 500 mil a 1 milhão hab. | 31,44 |
| População do município | mais de 1 milhão hab. | 32,22 |
| PIB per capita do município | até R$ 20 mil | 35,26 |
| PIB per capita do município | R$ 20 a 30 mil | 34,41 |
| PIB per capita do município | R$ 30 a 45 mil | 33,67 |
| PIB per capita do município | R$ 45 a 65 mil | 34,48 |
| PIB per capita do município | mais de R$ 65 mil | 35,23 |
| Capital social | até R$ 1 mil (inclui zero) | 39,68 |
| Capital social | R$ 1 a 10 mil | 37,24 |
| Capital social | R$ 10 a 50 mil | 34,12 |
| Capital social | R$ 50 a 200 mil | 33,09 |
| Capital social | mais de R$ 200 mil | 28,94 |
| Atividades secundárias | nenhuma | 37,92 |
| Atividades secundárias | 1 a 2 | 35,25 |
| Atividades secundárias | 3 a 5 | 33,25 |
| Atividades secundárias | 6 ou mais | 32,32 |
| Filiais | nenhuma | 41,72 |
| Filiais | 1 a 2 | 35,18 |
| Filiais | 3 ou mais | 27,50 |
| Sócios pessoa física | nenhum | 38,77 |
| Sócios pessoa física | 1 | 23,95 |
| Sócios pessoa física | 2 | 34,46 |
| Sócios pessoa física | 3 ou mais | 41,55 |
| Tem sócio pessoa jurídica | sim | 40,77 |
| Tem sócio pessoa jurídica | não | 29,30 |
| Histórico dos sócios | sócio tem outra empresa ativa sem dívida / sócio já fechou empresa sem dívida | 41,49 |
| Histórico dos sócios | sem sócio pessoa física | 38,77 |
| Histórico dos sócios | única empresa dos sócios | 37,46 |
| Histórico dos sócios | sócio tem outra empresa ativa com dívida | 28,32 |
| Histórico dos sócios | sócio já fechou empresa deixando dívida | 27,03 |
| Dívida ativa da União (perfil) | sem dívida | 79,92 |
| Dívida ativa da União (perfil) | só parcelada ou garantida / em cobrança até R$ 10 mil | 36,08 |
| Dívida ativa da União (perfil) | em cobrança de R$ 10 a 100 mil | 18,45 |
| Dívida ativa da União (perfil) | em cobrança acima de R$ 100 mil | 4,29 |
| Tem dívida ativa previdenciária | não | 39,55 |
| Tem dívida ativa previdenciária | sim | 30,52 |

Leitura (associações observadas, não causas): a idade não é uma linha reta. Empresas com menos de 1 ano recebem muitos pontos; em pouco tempo, poucas chegam a ter tributo inscrito em dívida ativa. O risco delas aparece na nota de fechamento e na regra de política de idade. O risco de nova dívida é maior entre 2 e 5 anos e menor depois dos 10. Mais filiais e sócio único dão menos pontos; uma explicação compatível, não testada, é que essas empresas têm mais tributos a pagar. O capital social é declarado pela própria empresa e a Receita não o confere; o capital zero foi juntado a "até R$ 1 mil". Na nota de dívida, a faixa mais baixa tem a maior pontuação e capital acima de R$ 200 mil a menor: empresas maiores têm mais tributo a pagar e, com isso, mais chance de inscrição (hipótese compatível, não testada). Na nota de fechamento a ordem se inverte (capital baixo fecha mais), e um bom cliente precisa de A ou B nas duas notas. A ordem não é imposta no capital porque o risco não anda num só sentido nas duas notas.

## Regras de política (fora da nota, valem acima dela)

A nota mede o risco médio. Três situações vão sempre para **análise manual** e nunca contam como "bom cliente", qualquer que seja a faixa: aberta há menos de 1 ano; excluída do Simples; dívida ativa em cobrança. "Excluída do Simples" é a empresa que já optou e hoje não é optante (`opcao_simples = 'N'`); o cadastro não informa o motivo. A regra de idade se apoia no fechamento: essas empresas recebem menos nova dívida que a média, mas fecham mais. No teste (empresas de mai/2023):

| Grupo | Empresas | % do teste | Nova dívida real | Fechou (real) |
|---|---|---|---|---|
| A/B nas duas notas | 142.464 | 23,1% | 7,8% | 19,7% |
| A/B nas duas notas e fora das regras de política (definição oficial) | 123.952 | 20,1% | 7,5% | 19,1% |
| A/B nas duas notas, mas barrada por regra de política | 18.512 | 3,0% | 9,9% | 24,1% |
| todas as empresas do teste | 616.603 | 100,0% | 18,5% | 37,0% |
| regra: aberta há menos de 1 ano | 100.650 | 16,3% | 10,9% | 41,8% |
| regra: dívida ativa em cobrança | 52.235 | 8,5% | 45,1% | 56,4% |
| regra: excluída do Simples | 31.586 | 5,1% | 40,7% | 42,4% |

As empresas A ou B nas duas notas que caem numa regra têm mais nova dívida e mais fechamento que as demais A/B. Fluxo de decisão proposto, nesta ordem: (1) divergência forte com o modelo de referência = análise manual; (2) senão, faixa E da nota de dívida = recusa (abaixo do corte dos 80%); (3) senão, regra de política = análise manual; (4) senão, aprovação pela nota, com prazo curto se a faixa de fechamento for E. Como a recusa vem antes das regras, quase toda empresa com dívida em cobrança sai na faixa E. Proporções no teste, com a fila aberta por motivo: `resultados/p4_fluxo_decisao.csv`. As regras estão em `scripts/p4_tabela.py` (REGRAS) e também na calculadora do painel.

## Exemplo verificável (empresa real do teste, sem identificação)

Empresa do teste com nota mais próxima da mediana da faixa C (`resultados/p4_exemplo_conta.csv`).

| Variável | Faixa da empresa | Coeficiente | Pontos |
|---|---|---|---|
| Porte e natureza jurídica | MEI | 0,224779 | 27,85 |
| Setor (divisão CNAE, 2 dígitos) | 47 | 0,104120 | 31,33 |
| UF | ES | −0,153591 | 38,76 |
| Simples Nacional | optante / excluída do Simples | 0,126018 | 30,70 |
| Idade da empresa | 5 a 10 anos | 0,006610 | 34,14 |
| População do município | 500 mil a 1 milhão hab. | 0,100332 | 31,44 |
| PIB per capita do município | mais de R$ 65 mil | −0,031138 | 35,23 |
| Capital social | R$ 10 a 50 mil | 0,007421 | 34,12 |
| Atividades secundárias | 3 a 5 | 0,037571 | 33,25 |
| Filiais | nenhuma | −0,256147 | 41,72 |
| Sócios pessoa física | nenhum | −0,153893 | 38,77 |
| Tem sócio pessoa jurídica | não | 0,174309 | 29,30 |
| Histórico dos sócios | sem sócio pessoa física | −0,153893 | 38,77 |
| Dívida ativa da União (perfil) | sem dívida | −1,579889 | 79,92 |
| Tem dívida ativa previdenciária | não | −0,180979 | 39,55 |
| **Total** | | −1,728370 | **564,85** |

- Pela fórmula: nota = 513,5614 − 28,8539 × (−0,049004 − 1,728370) = **564,85**.
- Chance de bom = 20 × 2^((564,85 − 600) ÷ 20) = 5,914; probabilidade de nova dívida = 1 ÷ (1 + 5,914) = **14,5%**. Faixa **C**.

## Segunda nota: fechamento

Mesmas variáveis, faixas e escala, com o alvo "fechou até out/2026" (constante −0,230336; base por variável 34,680503). Arquivos com sufixo `_fechou`. As mesmas regras de ordem valem. Junções feitas na nota de fechamento:

- Simples Nacional: "nunca optou / optante"
- Histórico dos sócios: "única empresa dos sócios / sócio tem outra empresa ativa com dívida"
- Dívida ativa da União (perfil): "em cobrança até R$ 10 mil / em cobrança de R$ 10 a 100 mil / em cobrança acima de R$ 100 mil"
- Tem dívida ativa previdenciária: "não / sim"

Na nota de fechamento, ter dívida previdenciária não muda os pontos (as duas faixas foram juntadas): sem a regra de ordem, ela daria menos risco de fechar (uma explicação compatível, não testada, é que a dívida previdenciária indica empresas com empregados). Juntar as duas faixas é uma escolha conservadora: a política de crédito não premia dívida.

## Resultado no teste (616.603 empresas que o modelo não viu)

| Faixa | Nova dívida prevista | Nova dívida real | Fechou (real) | Fechamento real (2ª nota) |
|---|---|---|---|---|
| A | 7,1% | 6,5% | 25,6% | 15,1% |
| B | 11,3% | 10,8% | 33,9% | 27,1% |
| C | 14,5% | 14,7% | 37,8% | 36,2% |
| D | 18,7% | 19,6% | 41,9% | 46,9% |
| E | 40,7% | 41,1% | 45,9% | 59,8% |

| Alvo | Modelo | AUC |
|---|---|---|
| nova dívida | LightGBM, com dívida de mar/2023 | 0,740 |
| nova dívida | LightGBM, sem dívida de mar/2023 | 0,679 |
| nova dívida | Scorecard v2 (tabela simplificada) | 0,722 |
| fechamento | LightGBM, com dívida de mar/2023 | 0,717 |
| fechamento | LightGBM, sem dívida de mar/2023 | 0,686 |
| fechamento | Scorecard v2 (tabela simplificada) | 0,696 |

A tabela v2 perde um pouco de poder de separação contra o modelo de referência (LightGBM, com todas as variáveis da versão 1), em troca de pesos que respeitam a ordem nas variáveis ordenadas e de uma calculadora simples. Divergências fortes entre os dois (2 faixas ou mais):
- LightGBM vê risco bem maior (2+ faixas): 2,1% das empresas; nova dívida real 19,3% (tabela previa 11,0%, LightGBM 19,4%).
- LightGBM vê risco bem menor (2+ faixas): 2,6% das empresas; nova dívida real 9,4% (tabela previa 20,5%, LightGBM 9,8%).
- diferença de 1 faixa: 34,4% das empresas; nova dívida real 14,6% (tabela previa 14,8%, LightGBM 14,5%).
- mesma faixa: 60,9% das empresas; nova dívida real 21,1% (tabela previa 20,7%, LightGBM 21,1%).

## Calibragem com a inadimplência bancária (SCR)

O SCR do Banco Central não identifica empresas; a comparação é por segmento. A nota prevista média ordena os segmentos como a inadimplência bancária: correlação de postos (Spearman) de 0,67 entre 15 setores e de 0,63 entre 27 UFs. Fator para converter a chance de nova dívida em inadimplência bancária aproximada (mediana dos setores): MEIs e MEs (porte “Micro” do SCR) 0,40; EPPs (porte “Pequena”) 0,35. Arquivos: `resultados/p4_calibragem_scr_*.csv`.

## Como refazer do zero

1. `etl_cnpj.py` com `EXTRACAO=2023-05`; `PGFN_PERIODO=2023T1 etl_pgfn.py`; `montar_base_2023.py`, `pgfn_devedores_2023.py`, `c1_socios_2023.py`, `p4_montar.py`.
2. `p4_amostra.py`, `p4_tabela.py` (variáveis v2), `p4_scorecard.py y_nova_divida` e `y_fechou`.
3. Conferência: `p4_pontuar.py` (refaz a nota só com as tabelas), `teste_calculadora.py` (a conta do painel), `conferir_p4.py`.
4. Para uma empresa nova: achar a faixa de cada variável, aplicar as junções, somar os pontos e converter pela fórmula do passo 4 — ou usar a calculadora do painel.
