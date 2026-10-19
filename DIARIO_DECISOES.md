# Diário de decisões — Sobrevivência de pequenas empresas (dados abertos do CNPJ)

## 14/10/2026 — Escolha do projeto e definições iniciais

- Projeto escolhido por Fabian entre três sugestões, para cobrir a lacuna de modelo preditivo no portfólio.
- Perspectiva: banco ou fintech de crédito para pequenas empresas (decisão do Fabian).
- Abrangência: Brasil, com recorte e destaque para o RS (decisão do Fabian).
- Público-alvo: gerência e diretoria (decisão do Fabian).
- Fonte principal: dados abertos do CNPJ da Receita Federal (empresas, estabelecimentos, Simples/MEI, com data de abertura e de situação cadastral). Referência externa para validação: estudo de sobrevivência do Sebrae, também baseado em dados da Receita (MEI 29%, ME 21,6% e EPP 17% de fechamento em até cinco anos, publicado em 2021).
- Próximo passo: Fabian envia as perguntas principais; a IA sugere melhorias e perguntas complementares.

## 15/10/2026 — Perguntas aprovadas

**Perguntas do Fabian:**
- P1. Quanto tempo as empresas sobrevivem, por setor, porte e cidade? Há setores mais frágeis? Com quantos anos de empresa o risco tende a cair?
- P2. Que características na abertura apontam maior risco de fechar? Que pontos as empresas de maior risco têm em comum? Que fatores reduzem o risco?
- P3. Onde há bons clientes pouco atendidos? Quais os melhores setores?
- P4. Como transformar isso numa nota de risco para concessão de crédito? Um método geral com vários fatores ou métodos por setor?

**Melhorias aprovadas (M1 a M4):**
- M1. Sobrevivência por turma de abertura, risco por ano de vida, MEI, ME e EPP separados e base mínima por cidade. Definição de fechamento: baixada ou inapta, com teste de sensibilidade só com baixada (decisão do Fabian).
- M2. Só informação conhecida na abertura (cuidado com porte e capital social, que a base guarda com o valor atual); perfis de risco; linguagem de associação.
- M3. Bom cliente = segmento com alta sobrevivência e crescimento de aberturas; pouco atendido = pouco crédito por empresa (Banco Central: SCR.data por UF, setor e porte; ESTBAN, agências por município).
- M4. Modelo geral × modelos por setor, comparados por setor; scorecard × gradient boosting; validação em turmas posteriores; faixas A a E com taxa esperada e curva de aprovação × fechamento.

**Complementares aprovadas (C1 a C5):** sócio com histórico (dados de sócio só agregados, nunca nominais); concorrência local; momento da abertura (pandemia, juros); MEI que vira microempresa; validação com Sebrae e IBGE (Demografia das Empresas).

**Ajuste do Fabian na C2:** a concorrência local tem de considerar o tamanho da cidade e, se possível, a renda. Medida: empresas ativas do mesmo setor por 10 mil habitantes no município, na data de abertura, comparada com a densidade esperada para cidades de mesma população e PIB per capita (IBGE: estimativas de população/Censo 2022 e PIB dos Municípios). O indicador final é a "saturação": densidade observada ÷ esperada.

## 15/10/2026 — Briefing e download

- `BRIEFING_NEGOCIO.md` escrito (perspectiva de crédito PJ; fechamento como sinal próximo de risco, não inadimplência; cuidados com campos que guardam o valor atual).
- Fonte oficial mudou: o antigo endereço da Receita não existe mais; os arquivos estão no compartilhamento público SERPRO+ (link no catálogo dados.gov.br). Extração mais recente: out/2026 (42 meses disponíveis, de mai/2023 a out/2026).
- Fabian autorizou o download de tudo que o estudo usa (~7,8 GB, 37 arquivos) pelo Chrome dele.
- Ambiente: o shell da pasta do Fabian tem pandas e SQLite, mas não tem scikit-learn nem DuckDB e não tem rede para instalar. Plano: preparação dos dados (pesada) na pasta do Fabian com pandas e SQLite, em partes curtas; o modelo preditivo roda no ambiente da nuvem a partir de uma tabela de modelagem enxuta.

## 15/10/2026 — Download refeito e bibliotecas

- Os 37 arquivos da primeira tentativa vieram vazios (0 bytes): o link de download do compartilhamento devolvia arquivo vazio. Movidos para `dados/_lixo/zip_vazios/`. Download refeito pelo endereço WebDAV público (`/public.php/dav/files/<token>/2026-10/<arquivo>`), conferido com um arquivo pequeno antes.
- Bibliotecas: o PyPI está bloqueado pela configuração de rede desta sessão, tanto na pasta do Fabian quanto na nuvem. Disponíveis: pandas e SQLite (pasta do Fabian); pandas, scikit-learn e SciPy (nuvem). Plano mantido sem DuckDB, LightGBM e lifelines: gradient boosting do scikit-learn (HistGradientBoosting), regressão logística para o scorecard e curva de sobrevivência calculada no próprio código, com testes.

## 15/10/2026 — Bibliotecas instaladas

- Fabian liberou o acesso à rede nas configurações. Instalados no ambiente da pasta do Fabian: DuckDB, PyArrow, scikit-learn, LightGBM, lifelines, statsmodels, SciPy e SHAP (versões em `requirements.txt`). Com isso, todo o estudo (preparação e modelo) roda no mesmo ambiente, sem levar dados para a nuvem. O plano alternativo sem essas bibliotecas fica descartado.

## 15/10/2026 — C6 aprovada e dados de inadimplência

- Fabian aprovou a C6 (dívida ativa da PGFN como segundo alvo: quais empresas acabam devendo ao fisco, e se a nota de fechamento também acerta esse risco) e o uso do SCR.data do Banco Central para calibrar a nota com a inadimplência bancária real por segmento.
- Download autorizado: PGFN do 2º tri/2026 (não previdenciário, previdenciário e FGTS, ~1,44 GB) e SCR.data de 2024 a 2026 (~1,09 GB). Opção do Fabian entre três (só PGFN; PGFN + SCR 2024-2026; PGFN + SCR 2019-2026).
- Limite já anotado: a lista da PGFN é um retrato do trimestre; dívidas pagas ou extintas antes dele não aparecem.

## 15/10/2026 — Conferência dos arquivos e conversão para Parquet

- Conferência: 40 de 43 arquivos íntegros. Faltavam Empresas8.zip (0 byte) e o SCR.data de 2025 e 2026 (não chegaram à pasta). Os três foram baixados de novo pelo Chrome; aguardando o Fabian mover.
- `scripts/etl_cnpj.py`: lê cada .zip direto (unzip | iconv latin-1→UTF-8), grava Parquet enxuto em `dados/processados/` só com os campos usados. Nomes, endereços e contatos não são gravados; ficam só indicadores (tem e-mail, tem telefone, tem nome fantasia). Sócio vira um código de pessoa (hash de nome + CPF mascarado), sem nome.
- Arquivos grandes (Estabelecimentos0, Simples) divididos por faixas de linhas por causa do limite de tempo de cada chamada. Contagem conferida: Estabelecimentos0 tem 31.028.468 linhas e 31.028.464 registros (4 registros com quebra de linha dentro do texto).
- Resultado: 73,8 milhões de estabelecimentos, 61,5 milhões de empresas (falta Empresas8, ~4,5 milhões), 50,8 milhões de registros do Simples/MEI, 30,5 milhões de vínculos de sócio.
- Primeiro sinal para a validação: a proporção de baixadas tem picos nas turmas e anos de 2016 e 2020 e a de inaptas é quase zero nas turmas recentes (a inaptidão leva tempo para ser declarada). Antes de medir sobrevivência, separar baixas a pedido de baixas de ofício (motivo da situação) e tratar o atraso da inaptidão.

## 15/10/2026 — Validação da base (etapa 1)

- Todos os arquivos conferidos (Empresas8 e SCR 2025/2026 refeitos). PGFN e SCR.data convertidos para Parquet (`etl_pgfn.py`, `etl_scr.py`), sem nomes.
- Tabela montada por empresa (`montar_base.py`, por dígito do CNPJ por causa do limite de memória): 70,5 milhões de linhas.
- `validar_dados.py`: sem duplicidade de estabelecimento; 1 CNPJ básico com duas matrizes (mantido); 4 aberturas antes de 1900; 33 baixas/inaptas com data anterior à abertura (descartar); 299 mil baixadas no mesmo dia da abertura; 172 mil no exterior (excluir); 4.112 sem porte; todos os CNAEs e municípios traduzidos; 468 devedores da PGFN sem CNPJ.
- Achados que exigem decisão: CNPJs de candidatos (natureza 4090) em massa nos anos de eleição; baixas de ofício em massa em 2015 (motivo 73) e 2018 (motivo 67); atraso de cerca de dois anos na inaptidão.
- Validação externa (Sebrae, Sobrevivência de Empresas 2020: fechamento em 5 anos de 29% no MEI, 21,6% na ME e 17% na EPP): na nossa base, a baixa voluntária em 5 anos das turmas 2015-2019 é de 33% a 35% no MEI, 22% na ME e 16% a 18% na EPP; com as inaptas, o MEI vai a 35%-53%. A ordem de grandeza bate com o Sebrae na baixa voluntária.
- `RESUMO_DADOS.md` escrito.

## 15/10/2026 — Decisões de método após a validação

- Universo (decisão do Fabian): só natureza jurídica empresarial (grupo 2), fora do exterior e sem datas incoerentes. Exclui candidatos, associações, órgãos públicos e produtores rurais pessoa física.
- Fechamento (decisão do Fabian): baixada (menos incorporação, fusão e cisão) ou inapta. Medidas principais nas turmas de 2012 a 2021 (pelo menos 5 anos de acompanhamento). Sensibilidade sem as baixas de ofício em massa e só com baixa voluntária.
- MEI (decisão do Fabian): opção pelo MEI em até 180 dias da abertura. ME e EPP pelo porte atual, com aviso.
- Regras gravadas em `scripts/metodos.py`, com 7 testes em `scripts/testes.py` (todos passam).

## 15/10/2026 — P1 (primeira parte): sobrevivência por porte e setor

- `q1_sobrevivencia.py`: tábua de vida anual (método atuarial, com as empresas ainda abertas tratadas como censura) sobre 24,4 milhões de empresas das turmas 2012-2021, universo empresarial.
- Sobrevivência em 5 anos: MEI 49,1%, ME 72,4%, EPP 77,1%, demais 81,2%. Em 10 anos: 23,4%, 43,8%, 54,9% e 63,6%.
- Risco por ano de vida: a baixa voluntária é mais alta no 1º ano (MEI 13,3%, ME 4,4%) e cai para um patamar estável a partir do 3º (MEI ~7,5%, ME ~4,8%, EPP ~3%). As inaptas e baixas de ofício só aparecem a partir do 3º ano (atraso administrativo), o que cria o salto do MEI no 3º ano da curva total. O risco não chega perto de zero com a idade.
- Setor: alojamento e alimentação (I) e comércio (G) são os mais frágeis na ME e EPP; no MEI, atividades profissionais (M), agropecuária (A) e alimentação (I) sobrevivem menos (40%-44% em 5 anos); construção (F), serviços pessoais (S) e artes (R) mais (54%-56%).
- Sensibilidade: só com baixa voluntária, o MEI sobrevive 62,9% em 5 anos (bate com o Sebrae, 71% em outra janela); excluindo as empresas das baixas de ofício em massa, o resultado quase não muda (MEI 49,7%).
- Pendente: recorte por cidade (aguarda tradução dos municípios para o código do IBGE). Dados do IBGE baixados pelo Chrome do Fabian (lista de municípios, população 2011-2025 e Censo 2022, PIB 2010-2023).

## 15/10/2026 — P1: revisão pedida pelo Fabian (horizonte de 10 anos; agro e construção)

**Ponto 1 (10 anos com turmas de 2012 a 2021).** A tábua de vida juntava turmas: o 10º ano vinha só das turmas que já tinham 10 anos, mas o leitor não via isso. Refeito com medida direta por turma (`q1b_horizonte_setores.py`, `q1b_base_horizontes.csv`): cada horizonte só usa turmas em que todas as empresas completaram o prazo.
- Achado novo: o resultado depende da época da fiscalização. A turma de 2012 do MEI "sobrevive" 75% em 5 anos porque as inativas dela só foram baixadas em massa em 2018, depois da janela; a partir de 2016 a inaptidão passou a ser contínua. A baixa voluntária é estável entre turmas (MEI 66%-70% em 5 anos de 2013 a 2019).
- Proposta: 1, 3 e 5 anos nas turmas de 2016 a 2020 (todas com 5 anos completos e no mesmo regime de fiscalização): MEI 86,0% / 66,1% / 47,8%; ME 95,2% / 82,0% / 70,0%; EPP 96,0% / 85,2% / 75,7%. 10 anos nas turmas de 2012 a 2015 (5 milhões de MEIs), com aviso: MEI 28,8% (59,8% contando só baixa voluntária), ME 46,5%, EPP 60,2%. O risco por ano de vida passa a ser mostrado com a baixa voluntária, comparável entre épocas.

**Ponto 2 (agro e construção, hipóteses do Fabian).** Novo sinal: se a empresa fechada deixou dívida ativa (fechamento com problema) ou não (encerramento limpo).
- Agropecuária MEI: fecha 55,6% em 5 anos (contra 49,1% nos demais setores), mais rápido (mediana de 2,7 anos contra 3,3) e com menos dívida ativa entre as fechadas (12,7% contra 15,7%). Padrão de quem desiste da formalização sem deixar dívida, compatível com a volta à informalidade (a base não mostra a informalidade em si).
- Incorporação imobiliária (41.10-7, em geral empresas criadas para uma obra): fecha pouco em 5 anos (15%-20%), em 4,5 a 4,8 anos de mediana, e as fechadas têm menos dívida ativa que as abertas (5,1% contra 9,7% nas "demais"; 10,6% contra 14,9% na ME). Compatível com o fechamento planejado ao fim da obra.
- Construção de edifícios e serviços de construção (ME e EPP): fechamentos com mais abandono (47%-53% inaptas) e mais dívida (24%-34%): esses sim são fechamentos com problema. MEI de serviços de construção fecha um pouco menos que a média (44,7%).
- Proposta: separar em todo o estudo "fechamento com dívida ativa" de "fechamento limpo", e tratar incorporação imobiliária como encerramento planejado (fora do ranking de risco).

## 15/10/2026 — C2: concorrência local ajustada por população e renda

- Municípios da Receita traduzidos para o código do IBGE por UF + nome (10 casos manuais por grafia ou mudança de nome; sobraram 2 empresas sem correspondência). `municipios_ibge.py`.
- Empresas esperadas por setor e município: regressão de Poisson por setor com ln(população), ln(PIB per capita) e efeito de ano; saturação = observadas ÷ esperadas. Pedido do Fabian: o cálculo precisa ser verificável. Resposta: coeficientes por setor publicados (`q2_coeficientes_setor.csv`), exemplo de conta para Garibaldi (`q2_exemplo_garibaldi.csv`, refeito à mão: 944,3 esperadas no varejo) e método alternativo sem regressão (tabela de taxas por faixa de população × quintil de renda). Documentado em `metodo/C2_empresas_esperadas.md`. A equação explica 88,8% da variação no setor mediano.
- Resultado (turmas 2016-2020, comparação dentro do mesmo setor e porte): a saturação não muda o fechamento em 5 anos (razão observado/esperado entre 0,99 e 1,02 nas faixas). EPP e empresas maiores em setores com mais do dobro do esperado fecham cerca de 10% menos (polos). Mesma conclusão por faixa de tamanho de cidade, pelo método da tabela e com setor por grupo CNAE (3 dígitos).
- Conclusão provisória: concorrência local ajustada não é sinal de risco; polo setorial é sinal favorável para empresas maiores.
- 15/10/2026: Fabian aprovou C2 e os dois métodos (equação e tabela) e pediu que o anexo explique a formação da constante e dos números de cada setor. Acrescentado em `metodo/C2_empresas_esperadas.md`: estimação por máxima verossimilhança; constante = ln(soma observada) − ln(soma de exp(b·ln pop + c·ln PIBpc + ano)), conferida no varejo (−6,05782 estimada; −6,05783 pela fórmula).

## 15/10/2026 — P2 (primeira rodada): características na abertura

- `c1_socios.py`: histórico dos sócios PF na data de abertura (outras empresas do mesmo sócio abertas antes; fechadas antes; fechadas com dívida ativa; ativas na abertura), por partição do código de pessoa. Só agregados.
- `p2_montar.py`: tabela de características das turmas 2012-2020 (`dados/processados/p2/`), com população e PIB per capita do ano de abertura e saturação do setor (2016-2020).
- `p2_fatores.py` (turmas 2016-2020, fora incorporação): fechamento em 5 anos e fechamento com dívida ativa por característica, comparados dentro do mesmo porte.
- **Problema encontrado: campos com o valor de hoje contaminam a comparação.** Exemplo claro: a EIRELI foi extinta em 2021 e as que estavam ativas viraram sociedade limitada; na base só sobram 3 EIRELIs ativas e 98,5 mil baixadas, o que daria "EIRELI fecha 94%". O mesmo risco vale para capital social, número de atividades secundárias, e-mail, nome fantasia e número de sócios (quem sobrevive atualiza o cadastro; quem fecha fica congelado).
- Campos confiáveis na data de abertura: data de abertura, MEI e Simples na abertura (datas de opção), setor principal, município (população e renda do ano), histórico dos sócios (datas das outras empresas).
- Resultados confiáveis: alojamento e alimentação fecham 14% mais que o esperado para o porte e 32% mais com dívida; imobiliário, financeiro e extração bem menos. Empresa fora do Simples na abertura fecha 40% menos. Cidades grandes fecham um pouco mais que as pequenas (+2% contra −5%). Estados do Norte e o DF fecham 10%-14% mais; com dívida, 20%-40% mais.
- C1 (só empresas com quadro de sócios): o fechamento total quase não muda com o histórico, mas o fechamento com dívida ativa dobra quando um sócio já fechou outra empresa deixando dívida (6,1% contra 3,4% na primeira empresa; razão 2,0) e cai quando o sócio fechou outra sem dívida (0,81).
- Decisão a pedir ao Fabian: para o modelo da P4, usar uma extração antiga da Receita (mai/2023, primeira disponível no compartilhamento) como "retrato do passado" e medir o que aconteceu até out/2026, eliminando o problema dos campos atuais.
- 15/10/2026: Fabian autorizou baixar a extração de mai/2023 (~6,1 GB, 31 arquivos) para o modelo da P4: características como estavam em mai/2023 e resultado (fechou; fechou com dívida ativa) até out/2026.
- 15/10/2026: da extração de mai/2023, só 9 dos 31 arquivos chegaram (Empresas0-2, Estabelecimentos0 e 2, Simples, Socios0-2). Os 22 que faltaram foram disparados de novo pelo Chrome, com 12 segundos entre um e outro. Os 9 presentes já foram convertidos para `dados/processados_2023-05/` (conferido que são de fato de 2023: capital social total diferente do de 2026). A Receita divide os arquivos com o mesmo número de linhas por arquivo, por isso várias contagens se repetem entre extrações.
- 16/10/2026: os 31 arquivos de mai/2023 conferidos (todos íntegros) e convertidos para `dados/processados_2023-05/` (empresas, estabelecimentos, Simples, sócios).

## 16/10/2026 — P2 (segunda rodada): retrato de mai/2023, sem campos atuais

- `montar_base_2023.py`: base de mai/2023 (53,7 milhões de CNPJs). Dívida ativa "em mai/2023" = inscrições do arquivo PGFN 2026 com data anterior a 15/05/2023 (é um piso: dívida quitada antes de 2026 não aparece).
- `c1_socios_2023.py`: histórico dos sócios PF como estava em mai/2023 (outras empresas fechadas, fechadas com dívida, ativas, ativas com dívida). Só agregados.
- `p4_montar.py`: 20,6 milhões de empresas empresariais ativas em mai/2023, com características daquela data e resultados até out/2026: fechou (MEI 44,8%, ME 27,9%, EPP 20,0%, demais 15,4% em 3,4 anos), fechou com dívida ativa (12,6% / 10,7% / 8,3% / 4,1%) e nova inscrição em dívida ativa (17,2% / 20,8% / 22,7% / 14,4%).
- Atenção: parte dos fechamentos é inaptidão por omissão de declarações logo depois do corte (MEI 6,5% inaptas ainda em 2023), ou seja, empresas que já estavam paradas em mai/2023. Baixa voluntária no período: MEI 26,7%, ME 13,1%, EPP 9,6%.
- `p2b_fatores_2023.py` (comparação dentro do mesmo porte e da mesma faixa de idade): sinais mais fortes são dívida ativa da União já existente (fechamento 1,3x a 1,9x; nova dívida 2,4x a 3,4x), exclusão do Simples (1,75x; com dívida 2,65x), sócio que já fechou empresa com dívida (1,33x; com dívida 2,0x, confirma C1) ou que tem outra empresa ativa com dívida (com dívida 1,42x). Protegem: sócio com outra empresa ativa sem dívida (0,77), três ou mais sócios (0,60), três ou mais filiais (0,60), setores imobiliário (0,60), saúde e financeiro (0,80). Alojamento e alimentação seguem 18% acima; Norte, Nordeste e DF acima, Sul e MG abaixo. E-mail, telefone e nome fantasia têm efeito fraco e instável.
- Divergência com a 1ª rodada: "nunca optou pelo Simples" aparecia como proteção (−40%) nas turmas 2016-2020; no estoque de 2023 fecha 26% mais. O sinal robusto é a exclusão do Simples (quem optou e saiu).
- 16/10/2026: Fabian aprovou a P2 (2ª rodada) e decidiu fazer a P4 antes da P3 (a P3 vai usar a nota para definir "bom cliente").

## 16/10/2026 — P4 (primeira rodada): amostra e primeiros modelos

- `p4_amostra.py`: 10% das empresas ativas em mai/2023 (2,05 milhões, sorteio fixo pelo hash do CNPJ), treino 70% e teste 30% por empresa; fora incorporação imobiliária e reorganizações. `p4_features.py`: variáveis de mai/2023. `p4_modelo.py`: LightGBM geral (memória da VM exige ler só as colunas usadas).
- Fechou (37%): AUC 0,716 com a dívida de mai/2023, 0,686 sem ela. Problema (fechou com dívida ou nova dívida, 21%): AUC 0,791 com dívida, 0,704 sem.
- **Problema encontrado: vazamento na variável de dívida.** A dívida "de mai/2023" vem do arquivo PGFN de 2026; quem quitou a dívida entre 2023 e 2026 aparece como "sem dívida", e quem não quitou fica marcado. Isso usa o futuro e infla o poder da variável. Além disso, "fechou com dívida" inclui dívidas antigas, o que repete a variável no alvo.
- Proposta ao Fabian: baixar o arquivo PGFN do 1º trimestre de 2023 (posição de março/2023, antes do corte) para medir a dívida como ela estava; e usar como "mau pagador" a nova inscrição em dívida ativa depois do corte (fechando ou não), mais próxima de inadimplência e sem repetir a variável.
- 16/10/2026: Fabian autorizou baixar a PGFN do 1º trimestre de 2023 e escolheu como "mau cliente" a nova inscrição em dívida ativa da União depois de mai/2023 (fechando ou não); o fechamento vira a segunda nota.

## 16/10/2026 — P4 (segunda rodada): dívida medida na posição de mar/2023

- PGFN 2023 T1 (arquivos com posição de mar/2023, gerados em 10/05/2023) convertida com `PGFN_PERIODO=2023T1 python etl_pgfn.py` para `dados/processados_2023-05/pgfn_2023T1/` (19 arquivos; 5,18 milhões de CNPJs devedores principais).
- Vazamento confirmado: das empresas ativas com dívida em mar/2023, 28% não aparecem como devedoras antes do corte no arquivo de 2026 (quitaram ou parcelaram e saíram). Essas recebem nova dívida 20% das vezes, contra 56% das que continuaram devendo. A variável antiga misturava "deve" com "continuou devendo".
- Refeitos com a posição de mar/2023: `p4_montar.py` (colunas t1_*: inscrições, valor, ajuizada, em cobrança, benefício fiscal, previdenciária, data da primeira), `c1_socios_2023.py` (sócio com dívida = devedor em mar/2023), `p2b_fatores_2023.py`, amostra e modelos.
- `p4_features.py` passou a calcular as variáveis no DuckDB (`p4_X.parquet`): a leitura em pandas estourava a memória da VM. O scorecard monta a matriz 0/1 à mão pelo mesmo motivo.
- Resultados no teste (616 mil empresas, nova dívida em 18,5%):
  - LightGBM geral: AUC 0,740 (Gini 0,48, KS 0,34); sem as variáveis de dívida: 0,679.
  - Scorecard (logística com variáveis em faixas): AUC 0,726 (Gini 0,45), só 0,014 abaixo, e cada faixa tem peso explicável.
  - Fechamento como alvo: LightGBM 0,717; scorecard 0,703.
  - Modelo por setor: em todas as 15 seções com volume suficiente, o modelo geral (com setor como variável) empata ou ganha do modelo próprio da seção (ex.: comércio 0,737 x 0,737; alojamento e alimentação 0,710 x 0,707; artes 0,722 x 0,683). Conclusão: método geral, com o setor dentro dele.
  - Variáveis mais importantes: tempo desde a primeira dívida ativa, valor da dívida, idade da empresa, setor, UF.
- P2 com a dívida de mar/2023: dívida até R$ 10 mil 1,67x de fechamento e 1,93x de nova dívida; acima de R$ 100 mil 1,38x e 3,07x. Sócio que já fechou empresa com dívida: 1,23x fechamento e 1,60x nova dívida (antes 1,33x e 1,82x: parte vinha do vazamento).
- Limite: só há um par de retratos (mai/2023 -> out/2026), então a validação é entre empresas diferentes, não entre períodos. Uma validação fora do tempo exigiria outro retrato antigo da Receita.
- 16/10/2026: Fabian escolheu scorecard como nota oficial e LightGBM como referência e alerta de discordância; validação fora do tempo não será feita (aviso no relatório).

## 16/10/2026 — P4 (terceira rodada): nota oficial, faixas A-E e calibragem pelo SCR

- `p4_scorecard.py`: logística em faixas convertida em pontos (600 pontos = 20 bons para 1 mau; +20 pontos dobram a chance de ser bom). Tabela de pontos em `p4_scorecard_pontos.csv`; cortes em `p4_cortes_faixas.csv`; notas do teste em `p4_notas_teste.parquet`.
- Faixas (quintis do treino), nova dívida ativa real no teste: A 6,1%, B 10,6%, C 14,8%, D 19,6%, E 41,4%; previsto e real batem em todas (diferença máxima de 0,6 ponto). A faixa E concentra 45% dos maus.
- Curva de aprovação: aprovando os 50% melhores, a nova dívida cai de 18,5% para 9,4% e 75% dos maus ficam de fora; aprovando 80%, 12,8% e 45% evitados.
- A nota de dívida não substitui a de fechamento: a faixa A ainda fecha 26% em 3,4 anos (a E, 46%). Daí a segunda nota.
- `p4_calibra_scr.py` (SCR jan/2024 a ago/2026, Micro e Pequeno): a nota ordena os segmentos como a inadimplência bancária real (Spearman 0,70 por seção, 0,62 por UF, 0,58 por seção × porte). Fator mediano: inadimplência bancária ≈ 0,4 × chance prevista de nova dívida ativa (o SCR mede em valor e só entre empresas com crédito).
- Divergência: no SCR, Pequeno (EPP) e Micro têm inadimplência parecida, mas a nota prevê mais nova dívida para a EPP (paga mais tributos, logo tem mais chance de inscrição). Na calibragem, o fator deve ser por porte (Micro 0,41; Pequeno 0,34 na mediana das seções).
- 16/10/2026: Fabian aprovou a P4 até aqui e pediu um anexo que explique como a nota foi feita e como refazer a conta, no mesmo padrão do anexo do C2.

## 16/10/2026 — P4 (quarta rodada): segunda nota, alerta, anexo verificável

- Faixas do scorecard revistas: variáveis com mais da metade em zero (filiais, dívidas parceladas, ajuizadas, previdenciárias) agora têm o zero como faixa própria e decis só entre os positivos; antes o zero e os positivos caíam na mesma faixa. AUC do scorecard de dívida 0,726 → 0,730; de fechamento 0,703 → 0,706. Função `limites_faixas` em `p4_features.py`, usada pelos dois scripts.
- Segunda nota (fechamento): A 14,0%, B 26,4%, C 36,7%, D 47,1%, E 60,8% de fechamento real, previsto e real até 1 ponto de distância.
- Cruzamento das duas notas (`p4_matriz_divida_fechamento.csv`): são quase independentes. A/A = 8,9% das empresas, com 5,4% de nova dívida e 12,4% de fechamento; E/E = 8,3%, 43,9% e 64,9%.
- Alerta de discordância (`p4_alerta_lgbm.py`): 69% das empresas ficam na mesma faixa nos dois modelos. Em 2,3% a diferença é de 2 ou mais faixas, e nesses casos o LightGBM acerta melhor (ex.: scorecard previa 10,8%, LightGBM 19,7%, real 19,1%). Regra proposta: 2+ faixas de diferença = análise manual.
- Anexo `metodo/P4_nota_de_risco.md`, gerado por `gerar_anexo_p4.py` (nenhum número digitado): faixas, regressão, fórmula dos pontos (fator 28,8539; offset 513,5614; base por variável), conversão nota → probabilidade, cortes A–E, exemplo real anônimo conta a conta (MEI de SP, 564,87 pontos, 14,5%, faixa C), leitura por bloco (dívida e sócios), segunda nota, validação, SCR, limites e roteiro para refazer.
- Novos arquivos para refazer à mão: `p4_scorecard_coeficientes*.csv`, `p4_scorecard_limites*.csv`, `p4_scorecard_constantes*.csv`, `p4_exemplo_conta*.csv`.
- `conferir_p4.py`: 20 conferências automáticas (fórmulas da escala, pontos = base − fator × coeficiente em todas as 314 faixas, exemplo, faixas crescentes, previsto × real, anexo atualizado), todas OK.
- Observação de memória: `p4_scorecard.py` fica no limite da VM (2,9 GB) e às vezes precisa rodar de novo.
- 16/10/2026: Fabian aprovou e pediu, se viável, uma calculadora no painel final: o usuário preenche só os dados da empresa e recebe a nota. Avaliação: viável. A nota é uma tabela de pontos (314 faixas por nota) que cabe no próprio painel. Município: lista com população e PIB per capita. Saturação do setor: fixada na faixa mediana, porque mexe no máximo 1 ponto e a tabela por cidade e setor seria pesada demais. Histórico dos sócios: perguntas simples.

## 16/10/2026 — Conferência da tabela de pontos e P3 (bons clientes pouco atendidos)

- `p4_pontuar.py`: aplica só as tabelas publicadas (limites + pontos), a mesma conta da calculadora. Primeira conferência: diferença de até 3,7 pontos contra o modelo. Causas: (1) pontos gravados com 1 casa decimal (passou a 4); (2) limites das faixas perdiam precisão no CSV, e um valor igual ao limite caía na faixa vizinha (limites gravados com 17 dígitos e lidos com `float_precision="round_trip"`). Depois da correção, nas 200 mil empresas do teste: diferença máxima de 0,001 ponto e faixa igual em 100% (dívida) e 99,998% (fechamento).
- `p4_scorecard.py` monta a matriz de treino em separado (antes, uma cópia dupla estourava a memória da VM).
- `p3_base_2026.py`: amostra de 10% das empresas ativas em out/2026 (2,5 milhões), com as variáveis montadas igual às de 2023, com os dados de hoje (PGFN de jun/2026, sócios e cadastro de out/2026, população de 2025). `p3_notas_2026.py`: aplica as duas notas.
- Empresas novas (CNPJs abertos em 2024-2026) recebem nota boa de dívida e nota ruim de fechamento, como esperado. Por isso "bom cliente" = A ou B nas duas notas: 26,3% dos MEIs, MEs e EPPs ativos (6,3 milhões).
- `p3_oportunidades.py`: SCR médio dos 12 meses até ago/2026 por UF × setor × porte. Índice de atendimento = crédito por empresa do segmento ÷ crédito por empresa do mesmo setor e porte no Brasil (mesma lógica do observado ÷ esperado do C2). Pouco atendido = índice < 0,8 e participação de bons ≥ a nacional; fora atividades financeiras (crédito entre empresas do próprio setor distorce o SCR, com crédito por empresa 10 vezes o dos demais) e segmentos com menos de 2 mil empresas.
- Resultado: 32 segmentos pouco atendidos. O maior grupo são as EPPs de serviços em SP (transporte, administrativas, informação, indústria, profissionais, saúde, educação, artes): índice entre 0,69 e 0,78, mais bons clientes que a média e inadimplência abaixo da nacional. Também imobiliário Micro em MG, PR, RS, SC e ES, e construção Micro em MG (inadimplência abaixo da nacional).
- UFs com menos crédito por empresa (AM, RJ, AL, PE, PA) também têm menos bons clientes e mais inadimplência: pouco crédito ali reflete risco, não oportunidade.
- `p3_rs.py`: o RS é bem atendido no total (índice 1,13). Exceções: construção Micro (0,69, mas inadimplência de 8,4% contra 4,4% nacional, ou seja, risco) e imobiliário Micro (0,70, inadimplência abaixo da nacional, oportunidade). Concentração de bons clientes por município (por mil habitantes): Serra e Litoral Norte lideram (Xangri-lá 94, Gramado 91, Garibaldi 80, Veranópolis 80, Flores da Cunha 79). SCR não existe por município.
- `c4_mei_cresce.py`: dos 12,2 milhões de MEIs ativos em mai/2023, até out/2026: 43,6% continuam MEI, 5,0% cresceram (saíram do MEI e seguem no Simples; 21,6 mil viraram EPP), 6,4% saíram do MEI e do Simples, 44,9% fecharam. Nova dívida ativa: cresceram 7,2% (perto da faixa A); saíram do MEI e do Simples 78,5% (sinal de alerta). Crescem mais: informação (16% dos ativos), profissionais (14%), administrativas (13%), educação (13%); por UF, Norte e Centro-Oeste (PA, AP, AM 14%) e SC (11%).

## 16/10/2026 — C3 (época da abertura) e P1 por cidade

- Selic mensal (BCB SGS 4189) lida no Chrome e gravada em `dados/externos/bcb_selic_sgs4189.csv`.
- `c3_epoca_abertura.py`: empresas abertas de 2016 a 2021 por semestre, comparadas com o esperado para a sua mistura de porte e setor.
  - Baixa voluntária em 3 anos: estável antes da pandemia (razão 0,88 a 1,01). Sobe nas empresas abertas durante a pandemia: 2020-S2 1,05; 2021-S1 1,11; 2021-S2 1,17. São as que viveram os primeiros anos com a alta de juros de 2021-2023.
  - Juros: a Selic na abertura não explica sozinha. As turmas de 2016 abriram com 14% e fecharam no esperado. A correlação com a Selic dos 12 meses seguintes é fraca (0,50; p = 0,10; 12 semestres). Conclusão: efeito da época da pandemia claro; efeito dos juros sugerido, não comprovado.
  - Fechamento em 1 ano mais baixo nas abertas em 2019-S2 e 2020-S1 (razão 0,84): o primeiro ano caiu no auge da pandemia, com auxílio e adiamento de obrigações.
  - Fechamento com dívida e fechamento total não servem para comparar épocas: a dívida vem do arquivo PGFN atual (turmas antigas já quitaram ou tiveram baixa de inscrições) e o total depende do calendário de inaptidões.
- `q1c_cidades.py`: sobrevivência em 5 anos (turmas 2016-2020) por UF e por município (2.256 municípios com 500+ empresas), com razão observado/esperado pela mistura de porte × divisão CNAE.
  - UFs: PI (0,92), MS (0,96), SC (0,97) fecham menos que o esperado; AC (1,11), AP (1,10), DF (1,09) mais. RS 1,02.
  - RS: cidades pequenas do interior fecham menos (Constantina 0,78, Sananduva 0,84). Região Metropolitana fecha mais (Alvorada 1,08, Viamão 1,08, Canoas 1,07, Porto Alegre 1,05). Bento Gonçalves 0,97; Garibaldi 0,99 (baixa voluntária 1,22, compensada por menos inaptidões).
- `q1d_rs_enchente.py`: teste da hipótese de que as enchentes de mai/2024 explicariam o fechamento alto em Lajeado, Venâncio Aires e Eldorado do Sul. Baixas voluntárias de jun/2024 a mai/2025 contra jun/2022 a mai/2023, relativas ao Brasil: Lajeado 1,02; Venâncio Aires 1,05; Eldorado do Sul 1,06; Canoas 1,06. Não há salto. Hipótese não confirmada nas baixas voluntárias. O maior aumento foi no Litoral Norte e na Serra turística (Gramado 1,22; Xangri-lá 1,19; Tramandaí 1,17).
- 16/10/2026: Fabian aprovou C3 e P1 por cidade e decidiu que o painel terá todos os municípios (2.256 com 500+ empresas nas turmas e todos os municípios na calculadora), para aumentar a relevância e a utilidade.

## 16/10/2026 — Relatório, painel e conferências (antes da revisão em duas camadas)

- Fabian escolheu o visual "Mesa de crédito" para o painel (azul-petróleo, verde, âmbar; faixas A–E como selos).
- `q1_oficial.py`: números oficiais da P1 gravados (turmas 2016-2020; 10 anos em 2012-2015; fora incorporação imobiliária). Pequenas diferenças contra o texto aprovado em 15/10 (ME 5 anos 69,9% contra 70,0%; EPP 10 anos 60,1% contra 60,2%) vêm da retirada da incorporação imobiliária, como aprovado.
- P3: além dos 32 segmentos pouco atendidos, 13 "prioritários" (também com inadimplência do SCR igual ou menor que a nacional; 280 mil bons clientes). Nos outros 19, o pouco crédito acompanha inadimplência maior (exemplo: energia e água micro no RS e no PR).
- `p3_municipios.py`: todos os municípios no painel (decisão do Fabian); base pequena (menos de 300 empresas ativas) aparece como "—".
- `p5_pilotos_metas.py`: dimensionamento (7,84 × [p0(1−p0)+p1(1−p1)]/efeito²) com a inadimplência do SCR (micro 5,85%, pequenas 7,94%, 12 meses até ago/2026) e a redução proporcional da curva de aprovação (−31% com 80% aprovados): 2.176 propostas por grupo (micro) e 1.571 (pequenas); oferta ativa: 3.818 por grupo para conversão de 2% para 3%. Meta de inadimplência em termos relativos (−15% em 12 meses; −31% final), porque o "hoje" é a inadimplência interna do banco.
- Gráficos (`graficos.py`): paleta de porte validada com `validate_palette.js` (MEI #B07A12, ME #2F6FA0, EPP #2E8B57); faixas A–E em escala divergente com cinza no meio e letra sempre escrita; sem gráficos de eixo duplo (Selic escrita sob as barras).
- Relatório (`RELATORIO.md`, PDF de 18 páginas via `relatorio_html.py` + Chromium) na estrutura de gestão; `conferir_relatorio.py` com 84 conferências no contexto da frase e lista de valores antigos proibidos: todas OK.
- Painel (`painel_modelo.html` + `painel_dados.py` + `painel.py` → `index.html`, 0,93 MB): seções 1.1 a 5 com o que mostram / por que importa / o que fazer, filtros, "Ver dados", municípios de todo o Brasil, explorador de segmentos e calculadora (ficha de proposta). `teste_calculadora.py` roda a função do painel (Node) em 3.000 empresas do teste: diferença máxima de 0,0008 ponto e mesma faixa em 100%. Conferido em captura a 1366 px e 390 px sem rolagem lateral.
- Correção encontrada ao montar a calculadora: a variável `mei_excluido` não é "já foi MEI e saiu", e sim "tem registro no Simples e não é MEI hoje" (o campo de opção pelo MEI vem "N" para quem nunca foi MEI). O modelo não muda; o rótulo no anexo e a calculadora seguem a definição correta.
- README (com resumo em inglês), LICENSE, .gitignore, `rodar_tudo.py` (testes → análises → nota → oportunidades → gráficos → painel → conferências; `--completo` inclui a conversão dos brutos).

## 16/10/2026 — Revisão em duas camadas, rodada 1 (relatório 7,0; painel 6,5; projeto 8,0) e correções

- Camada 2 recalculou direto nos dados os principais números (sobrevivência, faixas, curva, bons clientes, fatores da P2, C4, índice de um segmento, treino e teste disjuntos): todos bateram. Nenhum erro de conta.
- Problemas apontados e decisões:
  - Tabela de pontos com faixas de sinal invertido quando lidas sozinhas (ex.: "dívida ajuizada" dava mais pontos; tirar e-mail melhorava a nota). **Decisão do Fabian: refazer a tabela.** Versão 2 (`p4_tabela.py`, `p4_scorecard.py`): 15 variáveis em faixas fixas, blocos reunidos (perfil de dívida, histórico dos sócios, porte com natureza), saíram e-mail, telefone, nome fantasia, ajuizada, anos desde a 1ª dívida, saturação e faixa etária dos sócios. Faixas vizinhas fora de ordem nas variáveis ordenadas (dívida, histórico, Simples) são juntadas e o modelo refeito. AUC da nota de dívida 0,730 → 0,722; fechamento 0,706 → 0,698. Faixas A–E: nova dívida 6,5%, 10,8%, 14,6%, 19,6%, 41,1%.
  - Compliance: **decisão do Fabian: tirar a faixa etária dos sócios e manter a UF**, com parecer do jurídico antes do piloto.
  - Alvo descrito com mais alcance que os dados: o arquivo PGFN é a posição de jun/2026 (janela de cerca de 3,1 anos) e só mostra inscrições ainda ativas (quitadas somem): texto corrigido para "nova dívida ainda aberta em jun/2026", taxa como piso.
  - Piloto 1 com efeito otimista: agora dois cenários (−30% otimista, da curva de aprovação; −15% conservador, porque a política atual já filtra), tamanho em concessões (2.322 a 10.086 micro; 1.676 a 7.273 pequenas), concessões de fev a jul/2027 e leitura em ago/2028. Meta de inadimplência em 12 meses trocada por meta de processo; inadimplência só na leitura do piloto. Piloto 2: conversão entre grupos; inadimplência dos que contratam comparada com clientes atuais da mesma faixa.
  - Acompanhamento "mensal" da PGFN: os dados abertos são trimestrais; solução 4 reescrita (consulta por CNPJ ou bureau, custo médio, TI).
  - P3 sem ajuste da mistura MEI/ME no porte Micro do SCR: tentou-se estimar crédito por MEI e por ME entre UFs (mínimos quadrados não negativos), mas os coeficientes saíram instáveis (crédito por MEI zero em 12 de 17 setores). Regra adotada: Micro só entra no ranking com proporção de MEIs a até 10 pontos da nacional do setor; bons esperados pela mistura. Resultado: 29 pouco atendidos e 12 prioritários (247 mil bons clientes), 8 em São Paulo.
  - C4: viés de seleção (seguir no Simples exige estar em dia) declarado; 7,2% não é usado como risco esperado.
  - Margem de 95% na razão de fechamento por município e UF (`q1c_cidades.py`); municípios do RS citados com critério (3 mil empresas ou mais).
  - Linguagem causal retirada ("protege", "porque pagam", "não explicam"); "pagam melhor que a média" trocado por "inadimplência igual ou menor que a nacional"; indústria não é chamada de serviço.
  - Calculadora: validação de entradas (datas, negativos, cobrança ≤ inscrições, MEI = empresário individual), avisos (menos de 1 ano, exclusão do Simples, faixa E), barra fixa do celular só na calculadora, colunas-chave primeiro na tabela de segmentos, gráfico de UFs a partir de 0,85. `teste_calculadora.py` agora parte dos dados brutos: mesmas faixas nas 15 variáveis e mesma nota em 100% de 3.000 empresas.
  - Reprodução: `pgfn_devedores_2023.py` criado; `rodar_tudo.py` com `p4_tabela.py`, `--contar` do C2 e nota sobre etl_pgfn/etl_scr; `p2_base.parquet` corrompido (sobra antiga) movido para `dados/_lixo`; requirements sem lifelines/shap; P2 sem reorganizadas.
- Apontamentos não acatados: o `.gitignore` não exclui `dados/FONTES.md` (a linha citada pelo revisor não existe); o rótulo do equivalente bancário da calculadora já muda com o porte.

## 16/10/2026 — Revisão em duas camadas, rodada 2 (relatório 8,0; painel 7,5; projeto 9,0) e correções

- Camada 2: todos os recálculos bateram e não houve vazamento. Problemas apontados e decisões:
  - "Excluída do Simples" foi juntada a "optante" pela regra de ordem: com o perfil de dívida na nota, a exclusão não acrescenta risco médio. **Decisão do Fabian: regras de política fora da nota.** `p4_tabela.REGRAS`: menos de 1 ano, excluída do Simples ou dívida ativa em cobrança → análise manual e nunca "bom cliente". Aplicadas na P3 (`p3_notas_2026.py` guarda `regra_politica`), na matriz (`p4_bons_clientes.csv`), nos pilotos e na calculadora (função `regras()`, conferida por `teste_calculadora.py`: mesma decisão em 100%). No teste, A/B nas duas notas mas barradas: nova dívida 9,9% e fechamento 24%, contra 7,5% e 19% das demais A/B.
  - Capital social zero dava a melhor pontuação. **Decisão do Fabian: juntar zero com "até R$ 1 mil"** (dado declarado e não conferido).
  - Dívida previdenciária reduzia o fechamento: entrou nas variáveis ordenadas; na nota de fechamento, "não" e "sim" foram juntadas.
  - `p4_scorecard.py` passou a guardar as variáveis como categorias (a VM estourava a memória) e a gravar faixas e curva com 4 casas (evita arredondamento duplo: 41,05 → 41,0).
  - Nota de dívida: AUC 0,7215; faixas 6,5 / 10,8 / 14,7 / 19,6 / 41,1; E reúne 44,5% dos maus; curva a 50% 9,6% e 74,1% dos maus fora. Fechamento AUC 0,6964 (A 15,1%, E 59,8%). Divergência forte com o LightGBM: 4,7%. SCR: Spearman 0,67 (setor) e 0,63 (UF); fator 0,40 micro e 0,35 pequenas (agora lido do CSV pelo painel). AUC no texto com 2 casas.
  - P3 refeita: 4,8 milhões de bons clientes (20,0%); 34 pouco atendidos, 13 prioritários (205 mil bons, 9 em SP). Transporte micro em SP e construção micro em MG somam 53% dos bons prioritários (dito no relatório e no painel). Sensibilidade da tolerância MEI (`p3_sensibilidade_mei.csv`): 5 pontos → 12 prioritários; 15 → os mesmos 13. Tabela de segmentos do painel ganhou a coluna de bons clientes.
  - Pilotos: 2.324 a 10.095 (micro) e 1.678 a 7.279 (pequenas). Nova tabela de viabilidade (`p5_viabilidade.csv`): com 1.000 concessões por mês, o cenário conservador de micro leva 20 meses; para caber em seis meses, cerca de 3.400 por mês. Corte dos 80% deve ser recalculado sobre as propostas do banco.
  - Textos: "modelo por setor não foi melhor" qualificado como teste do modelo de referência (relatório, README, inglês, painel); "por isso há duas notas" e "sempre no sentido esperado" retirados; anexo P4 sem explicações causais, com seção de regras de política, junções das duas notas e calibragem SCR; painel sem "pilotos de 12 meses", "atualizados todo mês" e "monitoramento mensal"; indicador "ainda aberta em jun/2026"; aviso de viés no 7,2% do C4; nota de comparações múltiplas nos municípios; AUC da v1 (não reproduzível) retirada do Anexo A, com referência a `_lixo/v1_scorecard`.
  - Conferências: `conferir_p4.py` 28/28; `conferir_relatorio.py` 107/107 (novas: regras, fator SCR, sensibilidade, peso dos segmentos, viabilidade; lista de valores proibidos ampliada); calculadora 100%.

## 16/10/2026 — Revisão em duas camadas, rodada 3 (relatório 8,5; painel 8,0; projeto 9,2) e correções

- Camada 2: todos os recálculos bateram, sem vazamento e sem arredondamento duplo. Erro de conta: a viabilidade do piloto supunha que o grupo com nota recebe metade das concessões; ele recebe metade das propostas e concede só às que passam no corte. Corrigido: meses = tamanho ÷ (0,5 × 0,8 × propostas aprováveis por mês). Micro conservador com 1.000 por mês: 25 meses (antes 20); para caber em seis meses, cerca de 4.200 por mês (antes 3.400).
- Camada 1: o volume de análise manual não estava medido. `p4_alerta_lgbm.py` grava a divergência por empresa e `p4_matriz_duas_notas.py` gera `p4_fluxo_decisao.csv`: no teste, recusa 20,1% (faixa E da nota de dívida), análise manual 20,4% (regras ou divergência; cerca de 1 em 4 das que passam no corte) e aprovação pela nota 59,5%. Custo humano da solução 1 passou a "médio a alto"; sumário, painel e README dizem isso.
- Faixa E com uma só política: abaixo do corte dos 80% = recusa no fluxo proposto (calculadora alinhada; faixa E de fechamento = prazo curto).
- Pilotos: o piloto 1 aplica o fluxo completo (corte, regras e divergência), e o efeito foi estimado só com o corte (dito no texto). O piloto 2 sorteia bons clientes pela definição oficial, e os MEIs que cresceram também precisam estar fora das regras.
- Textos:
  - "excluída do Simples": o cadastro não informa o motivo;
  - a regra de idade se apoia no fechamento (nova dívida 10,9% contra 18,5%; fechamento 41,8% contra 37,0%);
  - capital: a faixa baixa tem mais pontos na nota de dívida e menos na de fechamento; o anexo explica por que a ordem não é imposta;
  - previdenciária: "escolha conservadora";
  - o transporte em SP passa o critério de bons clientes por pouco;
  - o índice de atendimento aparece com 3 casas no painel;
  - o Anexo A não cita mais notas internas nem o nome da pasta da v1.
- Calculadora: a regra de menos de 1 ano é aplicada pelo calendário (antes, uma empresa com exatamente 1 ano ainda caía na regra).
- `p5_pilotos_metas.py`: código sem uso retirado.
- Conferências:
  - `conferir_relatorio.py`: 115/115, com novas conferências de fluxo, viabilidade e regra de idade;
  - `conferir_p4.py`: 28/28;
  - calculadora: 100%.

## 16/10/2026 — Revisão em duas camadas, rodada 4 (relatório 9,0; painel 7,0; projeto 9,4) e correções

- Regressão grave no painel (camada 1): o comentário "// regra pelo calendário" entrou no meio da linha que lia população e PIB do município, e a calculadora passou a tratar todo município como "sem dado". Corrigido (comentário de bloco). `teste_calculadora.py` passou a conferir o código de `dadosForm` (nenhum campo dentro de comentário; campos obrigatórios presentes), já que essa função lê o formulário e não roda no Node.
- Contradição do fluxo (camada 2): a recusa da faixa E vinha antes da divergência, e 0,7% do teste com divergência forte era recusado. Decisão: a divergência forte prevalece sobre a recusa (na faixa E, ela só ocorre quando o modelo de referência vê risco menor). Fluxo novo: recusa 19,4%, análise manual 21,1%, aprovação 59,5%.
- Fila aberta por motivo (`p4_fluxo_decisao.csv`): menos de 1 ano 16,3% das propostas (nova dívida 10,8%, fechamento 41,9%), saída do Simples 1,9%, cobrança 0,4%, só divergência 2,5%. Alternativa posta para decisão no sumário: regra automática para empresas novas (limite baixo e prazo curto), o que deixa a fila em 4,8%.
- "Faixa E de fechamento: prazo curto" escrito na solução 1 (relatório e painel) e no anexo. A viabilidade avisa que os meses são um piso (supõem que a análise manual aprova tudo). "Quase toda empresa excluída tem dívida" virou "cerca de 2 em cada 3" (63% em mai/2023, contra 15% no total).
- Conferências: `conferir_relatorio.py` 121/121; `conferir_p4.py` 28/28; calculadora 100%, com a nova conferência de `dadosForm`.

## 16/10/2026 — Revisão em duas camadas, rodada 5 (relatório 9,0; painel 8,5; projeto 9,6) e correções

- A ordem do fluxo agora está escrita no relatório, no anexo e no painel: divergência forte → análise manual; senão faixa E de dívida → recusa; senão regra de política → análise manual; senão aprovação (prazo curto se a faixa de fechamento for E).
- A calculadora mostra uma decisão única. Na faixa E, a mensagem é "recusa, salvo divergência forte verificada no sistema" (a calculadora não tem o modelo de referência).
- A alternativa da regra automática para empresas novas passou a trazer o custo em risco (o grupo fecha 41,9%) e quem decide (diretoria de crédito).
- `p5_viabilidade.csv`: colunas renomeadas para meses_minimos_*, e o script avisa que os meses são um piso.
- Conferências: 121/121 no relatório, 28/28 no P4 e 100% na calculadora.

## 16/10/2026 — Revisão em duas camadas, rodada 6 (relatório 9,5; painel 9,0; projeto 9,7) e ajustes

- Calculadora: a aprovação agora também diz "salvo divergência forte, verificada no sistema".
- "A fila é quase toda de empresas novas" virou "cerca de três quartos" (16,3 de 21,1 pontos), no relatório, no painel e no README. A frase de empregados no anexo virou hipótese não testada.
- Painel: barra empilhada do fluxo (recusa, análise manual e aprovação) dentro do quadro "Decisão pedida".
- Conferências: 122/122 no relatório, 28/28 no P4 e 100% na calculadora.

## 16/10/2026 — Revisão em duas camadas, rodada 7 (relatório 9,5; painel 9,5; projeto 9,8)

- Primeira rodada com as três notas acima de 9. Nenhum problema de conta, coerência ou redação; ficam os limites declarados (validação num só período, alvo fiscal, SCR por segmento, UF sujeita a parecer do jurídico). Nada foi alterado depois desta rodada; a rodada 8 serve de confirmação.

## 16/10/2026 — Revisão em duas camadas, rodada 8 (relatório 9,0; painel 9,0; projeto 9,8) e ajustes

- A leitura "de diretor" (camada 1) trouxe pontos novos:
  - **Custo da recusa:** o sumário agora traz o fluxo em tópicos e a conta por 1.000 propostas: 194 recusadas (82 com nova dívida, 112 sem), 211 para analistas e 595 aprovadas. Recusar compensa se a perda com um inadimplente passar de cerca de 1,4 vez a margem de um bom cliente. Com a alternativa, a fila cai para 48 a cada 1.000.
  - **Arredondamento do painel:** usa agora a mesma regra do Python (toFixed sobre o valor binário, no lugar de toLocaleString), e faixas, curva e fluxo entram no painel com 4 casas, arredondados uma vez só.
  - **Gráficos do painel:** época da abertura com eixo até 1,2 e linha tracejada no esperado; faixas com eixo até 60 ou 80 e legenda do traço previsto.
  - **Metas:** a meta de bons clientes passa a ser "definida após a leitura do piloto 2 (mai/2027)", e a leitura de ago/2028 fica condicionada ao volume.
- Camada 2: o MEI da agropecuária (55,6%) usava as turmas de 2012 a 2020. O texto agora diz isso e traz também os 59,0% das turmas de 2016 a 2020.
- Conferências: 130/130 no relatório, 28/28 no P4 e 100% na calculadora.

## 16/10/2026 — Revisão em duas camadas, rodada 9 (relatório 9,5; painel 9,5; projeto 9,6) e ajustes

- O ponto de equilíbrio "1,4 vez" contava casos de nova dívida como se fossem inadimplentes. Com o fator do SCR (mediana por porte), entre as 194 recusas a cada 1.000 propostas haveria cerca de 32 inadimplentes e 162 bons pagadores no micro. Recusar compensa se a perda passar de 5 a 6 vezes a margem (5,1 no micro e 5,9 nas pequenas). O texto também diz que a comparação é contra aprovar todos. O "por mês" saiu da conta.
- Painel: a conta por 1.000 entrou sob a barra do fluxo; os rótulos das colunas ganharam contorno branco, para a linha tracejada não riscá-los.
- br() do painel: empates exatos agora vão para o par mais próximo, como no Python. Comparado com o Python em 16.044 valores: 0 diferenças (teste com Playwright no ambiente de nuvem).
- `teste_calculadora.py` passou a rodar `node --check` no script inteiro do painel, depois que um segundo comentário // engoliu código. O defeito foi pego no teste de navegador antes de publicar.
- Conferências: 133/133 no relatório, 28/28 no P4 e 100% na calculadora.

## 16/10/2026 — Revisão em duas camadas, rodada 10 (relatório 9,5; painel 9,5; projeto 9,8): critério atingido

- Rodadas 9 e 10 seguidas com as três notas acima de 9: a revisão em duas camadas termina aqui.
- Retoques finais, sem mudar número:
  - razão do ponto de equilíbrio calculada com os valores sem arredondar (5,0 no micro e 5,8 nas pequenas);
  - avisos de que o fator do SCR é uma média por segmento e de que margem e perda devem estar no mesmo horizonte;
  - ressalva "contra aprovar todas" na linha do painel;
  - "se o volume permitir" na ordem de execução do painel.
  O br() do painel foi conferido pela camada 2 contra o Python em 200 mil valores, sem nenhuma diferença.
- Pendente: aprovação final do Fabian; publicação no GitHub só com autorização.

## 16/10/2026 — Observações do Fabian na leitura do relatório (itens 1 a 5)

1. **"Impacto na operação" confuso:** virou um fluxograma (`g11_fluxo_decisao.png`, no relatório e no painel) com quatro tópicos curtos. Entrou no sumário um quadro de termos: MEI, ME, EPP; "Micro" e "Pequena" do Banco Central; Simples Nacional; nova dívida ativa. O texto usa "MEIs e MEs" e "EPPs" no lugar de "micro" e "pequenas".
2. **Alojamento e alimentação:** a seção foi aberta por atividade (`q1e_alojamento_alimentacao.py`, gráfico `g10`, tabela no painel).
   - Hotéis e pousadas fecham 17% menos que o esperado para o porte (60,1% abertos após 5 anos). O risco está na alimentação: de 41% a 45% abertos após 5 anos.
   - De 2019 para 2021, as aberturas cresceram 49% em restaurantes e 51% em comida para entrega (hotéis, 8%). Essas turmas encerraram 25% e 31% mais em três anos.
   - Empresas que já existiam: em 2020, hotéis e pousadas encerraram como o resto da economia (antes, cerca de 10% menos); comida para entrega encerrou menos em 2020 e 2021 e mais a partir de 2022 (+32% em 2024).
   - A nota já separava alojamento (divisão 55) de alimentação (56), porque usa a divisão CNAE de 2 dígitos.
3. **Gráfico de sinais de risco:** refeito como barras de "% a mais ou a menos que empresas parecidas", com um exemplo de leitura. No painel, o gráfico mostra "para cada 100 empresas parecidas", com uma linha de referência em 100.
4. **"Simples":** explicado como Simples Nacional, regime simplificado de impostos, no quadro de termos, na seção 1.2 e no "O que fazer".
5. **Parágrafo da curva:** reescrito com "a cada 100 empresas".
- Conferências: 140/140 no relatório (com as novas de alojamento e alimentação) e calculadora 100%. O PDF passou a ter 17 páginas.

## 17/10/2026 — Segunda leva de observações do Fabian

1. **Fluxograma:** a caixa "Análise manual" foi para a esquerda, e nenhuma seta cruza caixa.
2. **Alojamento separado da alimentação em todo o estudo** (pedido do Fabian: não julgar hotéis e pousadas pelos números da alimentação).
   - `q1_oficial.py` e `p2b_fatores_2023.py` agora separam I1 (divisão 55, hotéis e pousadas) de I2 (divisão 56, alimentação).
   - Resultados: ME abertas após 5 anos, alimentação 58,2% (6,9% fecham com dívida) e hotéis e pousadas 72,5%; fechamento contra empresas parecidas, alimentação +19% e hotéis e pousadas −21% (nova dívida +23% e −16%).
   - Atualizados o relatório (achado 5, 1.1, 1.2), os gráficos g3 e g4 e o painel.
   - O SCR do Banco Central não separa as duas atividades: na P3, a seção continua junta, com o aviso "o SCR não separa".
3. **"Como ler" do gráfico de sinais:** reescrito com dois grupos do mesmo tamanho (100 contra 167). O rótulo do gráfico passou a ser "Saiu do Simples Nacional".
- **Painel:**
  - gráfico de sinais com rótulos inclinados e rolagem dentro do cartão no celular, eixo com marcas redondas e "Hotéis e pousadas" no lugar de "Alojamento";
  - setor "Alimentação" com nome curto;
  - "Como ler" igual ao do relatório.
- **Conferências:** 144/144 no relatório e 100% na calculadora.
- Tabelas do painel (pedido do Fabian): cabeçalho escuro com texto branco e linha verde embaixo, separadores entre colunas, números centralizados sob o título da coluna, linhas alternadas e destaque ao passar o mouse. Porte "Micro" virou "MEI e ME" nos filtros e na tabela de segmentos.

## 17/10/2026 — Revisão em duas camadas, rodada 11 (relatório 9,0; painel 9,0; projeto 9,5) e correções

- **Erro de conta (camada 2):** em `q1e`, o fechamento esperado por porte incluía as divisões 55 e 56 inteiras junto com só 10% das outras atividades, o que puxava a razão para 1. Agora o esperado vem só das outras atividades.
  - Hotéis e pousadas: 9% menos fechamento (antes 17%).
  - Alimentação: 13% a 21% mais (antes 4% a 10%).
  - O texto explica por que esses números diferem do sumário (outra comparação: turmas de 2016 a 2020 contra empresas ativas em 2023 com a mesma idade).
- **"Micro" e "pequenas" trocados por "MEIs e MEs" e "EPPs"** em todo o relatório (corpo, anexos) e no painel (calculadora, metas, segmentos).
- **Seção 1.2:** os números estão no mesmo formato do gráfico ("93% mais nova dívida" em vez de "1,93 vez").
- **Quadro de termos:** ganhou "modelo de referência".
- **Fluxograma:** a caixa 4 virou afirmação ("se a nota de fechamento estiver na faixa E: prazo curto"); o rodapé diz que as regras impedem a aprovação automática; o "Impacto na operação" foi para depois da "Ordem de execução" (o espaço em branco da página 2 diminuiu).
- **Alojamento e alimentação:**
  - entrega em 2020 e 2021, "no mesmo ritmo do resto";
  - frase de que todas as turmas da pandemia encerraram mais;
  - hotéis 60,1%, de todos os portes (dois terços MEIs).
- **Painel:**
  - título do gráfico de sinais reescrito e eixo em 0 / 100 / 200 / 300 / 400;
  - "(o SCR não separa)" ficou só na legenda dos segmentos;
  - tabela por atividade com "× outras atividades".
- **Conferências:** 146/146 no relatório e 100% na calculadora.

## 17/10/2026 — Revisão em duas camadas, rodada 12 (relatório 9,5; painel 9,5; projeto 9,8) e acabamento

- Primeira rodada da nova série com as três notas acima de 9. Acabamento:
  - "três perguntas e um ajuste de prazo";
  - fonte maior nas caixas do fluxograma;
  - no celular, rótulos de dívida encurtados ("> R$ 100 mil") e anos com dois dígitos no gráfico da época;
  - legenda da tabela por atividade com "outras atividades do mesmo porte";
  - anexo P4 com "MEIs e MEs" e "EPPs" no fator do SCR.
- Conferências: 146/146 no relatório, 28/28 no P4 e 100% na calculadora.

## 17/10/2026 — Revisão em duas camadas, rodada 13 (relatório 9,5; painel 9,5; projeto 9,8): critério atingido de novo

- Rodadas 12 e 13 seguidas com as três notas acima de 9: a revisão termina para esta versão.
- Ajuste final: as margens dos estados ficam abaixo de ±1 ponto na maioria; AC, AP e RR têm de ±1,3 a ±1,4.
- Pendente: o Fabian avaliar o painel e aprovar a versão final; publicação no GitHub só com autorização.

## 19/10/2026 — Aprovação final e preparação da publicação

- O Fabian aprovou o relatório e o painel e autorizou a publicação. Repositório escolhido: Fabi3105/risco-credito-pequenas-empresas (público), com o painel no GitHub Pages.
- Antes de publicar:
  - `.gitignore` passou a excluir `scripts/.tmp/` (arquivos temporários do DuckDB, cerca de 500 MB);
  - o número de um CNPJ citado na validação foi retirado (`validar_dados.py` e `validacao_dados.csv`);
  - o README ganhou o endereço do painel e as últimas mudanças de texto (saída do Simples, MEIs e MEs, alimentação contra hotéis e pousadas).
- Criados `_publicar_github.bat` (primeira publicação) e `_atualizar_github.bat` (envios seguintes). O repositório vai com cerca de 14 MB, sem os dados brutos nem os processados.
