# Sobrevivência de pequenas empresas e risco de crédito PJ (dados abertos do CNPJ, PGFN e SCR, 2012-2026)

Estudo independente, do ponto de vista de um banco ou fintech que empresta a pequenas empresas, para a gerência e a diretoria. Responde a quatro perguntas: quanto tempo as empresas sobrevivem, que características indicam mais risco, como transformar isso numa nota de crédito e onde estão os bons clientes pouco atendidos.

- **Relatório:** [RELATORIO.pdf](RELATORIO.pdf) (versão em texto: [RELATORIO.md](RELATORIO.md))
- **Painel interativo com calculadora de nota:** https://fabi3105.github.io/risco-credito-pequenas-empresas/ (arquivo: [index.html](index.html))
- **Como a nota é calculada e como refazer a conta:** [metodo/P4_nota_de_risco.md](metodo/P4_nota_de_risco.md) · **Empresas esperadas por cidade:** [metodo/C2_empresas_esperadas.md](metodo/C2_empresas_esperadas.md)
- **Decisões e revisões, com data:** [DIARIO_DECISOES.md](DIARIO_DECISOES.md) · **Perspectiva:** [BRIEFING_NEGOCIO.md](BRIEFING_NEGOCIO.md) · **Dados e validação:** [RESUMO_DADOS.md](RESUMO_DADOS.md)

## Principais conclusões

1. **Metade dos MEIs fecha em cinco anos, e o risco não desaparece com a idade.** Seguem abertos após 5 anos 47,8% dos MEIs, 69,9% das MEs e 75,7% das EPPs; o encerramento voluntário do MEI é de 13,9% no 1º ano e fica perto de 7% ao ano depois.
2. **Entre os dados públicos analisados, os sinais mais fortes são** a dívida ativa da União, a saída do Simples Nacional (regime simplificado de impostos) e o histórico dos sócios (a saída do Simples vale como regra de análise manual, fora da nota). Concorrência local, ajustada por população e renda, não acompanha diferença no fechamento.
3. **Uma nota única, com 15 variáveis e o setor dentro, separa bem os riscos:** a nova dívida ativa vai de 6,5% na faixa A a 41,1% na E. No modelo de referência, um modelo por setor não foi melhor em nenhum dos 15 setores testados. Empresa com menos de 1 ano, excluída do Simples ou com dívida em cobrança vai para análise manual; no teste, cerca de 1 em cada 4 propostas não recusadas iria para um analista, três quartos delas de empresas com menos de 1 ano.
4. **Há 4,8 milhões de bons clientes e 34 segmentos com pouco crédito;** em 13 deles a inadimplência também é igual ou menor que a nacional: a maioria EPPs de São Paulo em serviços, transporte e indústria, mas mais da metade dos bons clientes prioritários está em MEIs e MEs de transporte em SP e da construção em MG. 5,0% dos MEIs cresceram em três anos.
5. **A época da abertura e o setor pesam:** empresas abertas na pandemia encerraram 5% a 17% mais que o esperado em três anos. A alimentação (restaurantes, lanchonetes, bares e comida para entrega) fecha 19% mais que empresas parecidas; hotéis e pousadas, 21% menos.

O relatório termina com seis soluções, dois pilotos com sorteio dimensionados em dois cenários e metas com dono.

## Dados

| Base | Fonte | Período |
|---|---|---|
| CNPJ (empresas, estabelecimentos, Simples/MEI, sócios) | Receita Federal, dados abertos | extrações de mai/2023 e out/2026 |
| Dívida ativa da União | PGFN, dados abertos | posições de mar/2023 e jun/2026 |
| SCR.data (crédito por segmento) | Banco Central | jan/2024 a ago/2026 |
| Municípios, população, PIB | IBGE | população 2011 a 2025; PIB 2010 a 2023 |
| Selic (série 4189) | Banco Central | 2011 a 2026 |

Os arquivos de dados não estão no repositório. O endereço de cada um, a pasta onde colocá-lo e os filtros estão em [dados/FONTES.md](dados/FONTES.md). Dados de sócios são usados só em contagens; nenhum nome, CPF, endereço ou contato é guardado.

## Como reproduzir

```
pip install -r requirements.txt
cd scripts
python rodar_tudo.py --completo   # conversão dos dados brutos, bases, análises, nota, painel e conferências (horas)
python rodar_tudo.py              # a partir das bases já montadas
python rodar_tudo.py 6 7          # só a nota de risco (passo 6)
python conferir_relatorio.py      # confere os números do relatório contra os resultados
```

Feito com uma máquina de 2 núcleos e 2,9 GB de memória: as bases são processadas em partes (por dígito do CNPJ) com DuckDB.

## Autoria

Fabian Aliatti Mayer. Perguntas, critérios e decisões de método são dele; consultas, programas e textos foram executados com apoio de IA (Claude). Licença MIT.

---

## Summary (English)

Independent study of small-business survival and SME credit risk in Brazil, written from the perspective of a bank or fintech lending to small companies, using only open data: the full Federal Revenue company registry (CNPJ, 70.5 million records, snapshots of May/2023 and Oct/2026), federal tax debt (PGFN), Central Bank segment-level credit data (SCR.data) and IBGE. Half of micro-entrepreneurs (MEI) close within five years; federal tax debt, exclusion from the simplified tax regime and partners' history are the strongest public risk signals, while local competition adjusted for population and income is not. A point-in-time 15-variable scorecard with monotonic risk bands (features as of May/2023, outcome measured in 2026) separates new tax-debt rates from 6.5% (band A) to 41.1% (band E), and, in the reference model (LightGBM), a single model with sector as a variable matched or beat sector-specific models in all 15 sectors. Firms under one year old, excluded from the simplified regime or with tax debt in collection go to manual review regardless of score. The dashboard includes a calculator that reproduces the scorecard exactly in the browser, data for every municipality, and a segment explorer of under-served good clients.
