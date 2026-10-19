# Fontes de dados

## CNPJ — Receita Federal (dados abertos, extração de out/2026)

- Catálogo: https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj (licença Creative Commons Attribution)
- Arquivos: compartilhamento público SERPRO+ https://arquivos.receitafederal.gov.br/index.php/s/YggdBLfdninEJX9 , pasta `2026-10`
- Dicionário de campos: https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf
- Colocar os .zip em `dados/brutos/2026-10/`:
  - Estabelecimentos0.zip a Estabelecimentos9.zip (~5,4 GB)
  - Empresas0.zip a Empresas9.zip (~1,4 GB)
  - Socios0.zip a Socios9.zip (~0,7 GB)
  - Simples.zip (~0,3 GB)
  - Cnaes, Municipios, Motivos, Naturezas, Qualificacoes, Paises (tabelas de tradução)
- Os brutos não vão para o repositório.

## Dívida ativa da União — PGFN (dados abertos, 2º trimestre de 2026)

- Página: https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/dados-abertos
- Arquivos (colocar em `dados/brutos/pgfn/`):
  - https://dadosabertos.pgfn.gov.br/2026_trimestre_02/Dados_abertos_Nao_Previdenciario.zip (~1,3 GB)
  - https://dadosabertos.pgfn.gov.br/2026_trimestre_02/Dados_abertos_Previdenciario.zip (~83 MB)
  - https://dadosabertos.pgfn.gov.br/2026_trimestre_02/Dados_abertos_FGTS.zip (~18 MB)
- Dicionário: https://www.gov.br/pgfn/pt-br/assuntos/divida-ativa-da-uniao/transparencia-fiscal-1/arquivos-dados-abertos/dicionario_de_campos.xlsx

## SCR.data — Banco Central (operações de crédito, 2024 a 2026)

- Painel e metodologia: https://www.bcb.gov.br/estabilidadefinanceira/scrdata
- Arquivos (colocar em `dados/brutos/scr/`): https://www.bcb.gov.br/pda/desig/planilha_2024.zip (~414 MB), planilha_2025.zip (~410 MB), planilha_2026.zip (~263 MB, até o mês mais recente publicado)
- Licença: Open Data Commons ODbL.

## CNPJ — extração antiga de mai/2023 (retrato do passado para o modelo da P4)

- Mesmo compartilhamento SERPRO+, pasta `2023-05` (primeira extração disponível).
- Baixados com o prefixo `2023-05_` no nome; colocar em `dados/brutos/2023-05/` (pode tirar o prefixo ou não; o script aceita os dois).
- Estabelecimentos0-9 (~4,1 GB), Empresas0-9 (~1,1 GB), Socios0-9 (~0,5 GB), Simples (~0,2 GB). As tabelas de tradução são as mesmas de out/2026.

## Dívida ativa da União — PGFN, 1º trimestre de 2023 (posição antes do corte de mai/2023, para a P4)
- Arquivos (colocar em `dados/brutos/pgfn_2023T1/`), baixados pelo Chrome em 16/10/2026:
  - https://dadosabertos.pgfn.gov.br/2023_trimestre_01/Dados_abertos_Nao_Previdenciario.zip
  - https://dadosabertos.pgfn.gov.br/2023_trimestre_01/Dados_abertos_Previdenciario.zip
  - https://dadosabertos.pgfn.gov.br/2023_trimestre_01/Dados_abertos_FGTS.zip
- Uso: dívida ativa como estava antes do corte (evita usar quem quitou entre 2023 e 2026 como "sem dívida").

## Taxa Selic — Banco Central, SGS série 4189 (Selic acumulada no mês, anualizada, % a.a.)
- Fonte: https://api.bcb.gov.br/dados/serie/bcdata.sgs.4189/dados?formato=json&dataInicial=01/01/2011&dataFinal=31/10/2026 (lida no Chrome em 16/10/2026; sem download de arquivo).
- Gravada em `dados/externos/bcb_selic_sgs4189.csv` (jan/2011 a out/2026). Uso: C3 (juros na época da abertura).
