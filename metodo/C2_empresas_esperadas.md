# C2 — Como foi calculado o número esperado de empresas por setor e cidade

Objetivo: saber se uma cidade tem mais ou menos empresas de um setor do que o tamanho e a renda dela comportam (pedido do Fabian: considerar população e renda).

## Dados

- Empresas ativas do setor no município em 1º de janeiro de cada ano (2016 a 2020): aberturas até o ano anterior menos fechamentos até o ano anterior, universo empresarial (`q2_ativas_mun_div_ano.parquet`).
- População: estimativas do IBGE (2022 = Censo; 2023 interpolado). PIB municipal do IBGE (preços correntes). PIB per capita = PIB ÷ população.
- Setor: divisão CNAE (2 dígitos, 84 setores com pelo menos 500 empresas ativas). Conferência com grupo CNAE (3 dígitos).

## Método principal: equação por setor

Para cada setor, uma regressão de Poisson em todos os municípios e anos (5.570 × 5 = 27.850 observações por setor):

    esperadas = exp( constante + b × ln(população) + c × ln(PIB per capita) + efeito do ano )

- b mede quanto o número de empresas cresce com a população (b = 1: dobra a população, dobra o número de empresas).
- c mede quanto cresce com a renda por habitante.
- Os coeficientes de cada setor estão em `resultados/q2_coeficientes_setor.csv`; qualquer pessoa refaz a conta numa calculadora.
- Qualidade do ajuste: a equação explica 88,8% da variação entre municípios no setor mediano (94,6% ponderando pelo tamanho do setor); correlação mediana entre observado e esperado de 0,95.
- Propriedade da regressão de Poisson com constante: a soma das esperadas de cada setor e ano é igual à soma das observadas (o esperado redistribui o total do país conforme população e renda).

**Saturação = (ativas observadas + 0,5) ÷ (esperadas + 0,5).** O 0,5 evita divisão por zero em cidades pequenas sem nenhuma empresa do setor.

## Exemplo verificável: Garibaldi-RS, 1º/01/2020 (`resultados/q2_exemplo_garibaldi.csv`)

População 35.440; PIB per capita R$ 64.890.

| Setor | Constante | b (população) | c (renda) | Efeito 2020 | Esperadas | Observadas | Saturação |
|---|---|---|---|---|---|---|---|
| 47 Comércio varejista | −6,0578 | 1,0127 | 0,2182 | −0,1186 | 944,3 | 745 | 0,79 |
| 56 Alimentação | −10,1244 | 1,0237 | 0,4680 | 0,0472 | 341,1 | 186 | 0,55 |

Conta do varejo: exp(−6,0578 + 1,0127 × ln 35.440 + 0,2182 × ln 64.890 − 0,1186) = 944,3.

## Como cada setor chega aos seus números (constante, b, c e efeitos de ano)

Cada setor tem a sua própria equação porque cada setor se distribui de um jeito pelo país: varejo acompanha quase só a população; serviços de saúde e alimentação crescem mais com a renda. Os números não são escolhidos à mão. São estimados com os dados de todos os municípios pelo método de máxima verossimilhança da regressão de Poisson: o computador procura os valores de b, c e dos efeitos de ano que deixam as esperadas o mais perto possível das observadas, município a município, nos cinco anos.

**A constante** é o fator de escala do setor. Sozinha não tem leitura prática (seria o número de empresas de uma cidade com 1 habitante e R$ 1 de PIB per capita). Ela é fixada de modo que a soma das esperadas de todos os municípios seja exatamente igual à soma das empresas que existem no país. Por isso pode ser recalculada diretamente, sem software estatístico, depois de conhecidos b, c e os efeitos de ano:

    constante = ln(soma das empresas ativas do setor em todos os municípios e anos)
              − ln( soma, em todos os municípios e anos, de exp( b × ln(população) + c × ln(PIB per capita) + efeito do ano ) )

Conferência para o varejo (setor 47): soma observada 25.882.833 empresas; soma esperada 25.882.832; constante estimada −6,05782; constante pela fórmula acima −6,05783.

**b e c** são o que muda entre setores. Leitura de b: se b = 1,01 (varejo), uma cidade com o dobro da população tem 2^1,01 ≈ 2,01 vezes mais lojas. Leitura de c: se c = 0,47 (alimentação), uma cidade com o dobro da renda por habitante tem 2^0,47 ≈ 1,39 vez mais restaurantes, a mesma população. **Efeito do ano** ajusta o crescimento ou a queda do setor no país de um ano para o outro (2016 é a referência, com efeito zero).

Para verificar uma cidade: pegar b, c, constante e efeito do ano na tabela `resultados/q2_coeficientes_setor.csv`, a população e o PIB per capita do IBGE, e aplicar a equação (exemplo de Garibaldi acima).

## Método de conferência: tabela de taxas (sem regressão)

Municípios agrupados em 6 faixas de população × 5 faixas de PIB per capita (quintis do ano). Para cada setor, faixa e ano:

    taxa da faixa = empresas ativas do setor nos municípios da faixa ÷ população desses municípios
    esperadas = taxa da faixa × população do município

Garibaldi 2020 (faixa 20 a 50 mil habitantes, quintil mais alto de renda): varejo 895,9 esperadas (saturação 0,83); alimentação 314,8 (0,59). Os dois métodos levam à mesma conclusão sobre o fechamento.

## Limites

- Mede concorrência por setor amplo; a conferência por grupo CNAE (3 dígitos, `_n3`) dá o mesmo resultado.
- PIB municipal inclui atividades que não viram renda local (ex.: grandes indústrias); a população flutuante (turismo) não entra.
- Associação, não causa.
