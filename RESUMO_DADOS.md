# Resumo dos dados

Extração da Receita de out/2026 (última data na base: 11/10/2026), dívida ativa da PGFN de jun/2026 e SCR.data de jan/2024 a ago/2026.

## Tabelas processadas (`dados/processados/`)

| Tabela | Linha = | Registros | Campos usados |
|---|---|---|---|
| estab | estabelecimento (matriz ou filial) | 73.809.379 | situação, data e motivo da situação, data de abertura, CNAE principal, nº de CNAEs secundários, UF, município (código da Receita), indicadores de e-mail, telefone, nome fantasia |
| empresas | empresa (CNPJ básico) | 70.517.438 | natureza jurídica, qualificação do responsável, capital social, porte |
| simples | empresa optante (atual ou passada) | 50.806.102 | datas de opção e exclusão do Simples e do MEI |
| socios | vínculo de sócio | 28.495.961 | tipo (PF/PJ), código de pessoa (sem nome), qualificação, data de entrada, faixa etária |
| pgfn | inscrição em dívida ativa de PJ | 32.339.322 | sistema (não previdenciária, previdenciária, FGTS), tipo de devedor, situação, data de inscrição, ajuizada, valor |
| scr | célula do SCR.data (PJ) por mês | ~25 milhões | UF, seção e subclasse CNAE, porte, modalidade, carteira ativa, inadimplida, ativo problemático |
| base | empresa (CNPJ básico), tabela montada | 70.517.438 | matriz + empresa + Simples/MEI + contagem de sócios e filiais + resumo da dívida ativa (só devedor principal) |

## Números de referência

- 91,4% das empresas têm natureza jurídica empresarial (grupo 2); 5,4% são pessoas físicas com CNPJ (grupo 4, sobretudo candidatos a cargo eletivo e produtores rurais) e 3,1% entidades sem fins lucrativos (grupo 3).
- 37,4 milhões de empresas já foram MEI alguma vez.
- 6,77 milhões de empresas têm dívida ativa da União como devedor principal; só 468 devedores principais não aparecem no CNPJ.
- Inadimplência bancária PJ (SCR.data, ago/2026): 3,4% da carteira; micro 7,9%, pequeno 7,6%, médio 4,9%, grande 0,7%.

## Armadilhas

- **Retrato de um mês:** porte, capital social e endereço vêm com o valor atual; a situação tem só a última mudança.
- **Candidatos e produtores rurais:** CNPJs de campanha eleitoral (natureza 4090) aparecem em massa nos anos de eleição (497 mil abertos em 2016) e fecham logo; distorcem qualquer taxa se não forem excluídos.
- **Baixas de ofício em massa:** a Receita baixou de uma vez empresas inativas (motivo 73, omissão contumaz, 934 mil em 2015; motivo 67, registro cancelado, 1,37 milhão em 2018). A empresa já estava parada, mas a data da baixa é administrativa.
- **Atraso da inaptidão:** a empresa vira inapta (motivo 63, omissão de declarações) só depois de cerca de dois anos sem declarar. Turmas recentes parecem mais saudáveis do que são.
- **Código de município da Receita** não é o do IBGE: precisa de tabela de tradução para juntar população e PIB.
- **Porte atual:** uma empresa que cresceu aparece como EPP hoje, mesmo tendo aberto como ME; o porte não pode ser usado como característica da abertura sem cuidado.
- **Dívida ativa:** retrato de jun/2026; dívidas já pagas ou extintas não aparecem. Datas de inscrição inválidas (01/01/1000) viraram nulo.
