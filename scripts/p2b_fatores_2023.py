# -*- coding: utf-8 -*-
"""P2 (segunda rodada, ponto no tempo): características como estavam em mai/2023 e o que aconteceu até out/2026,
para as empresas ATIVAS em mai/2023 (fora incorporação imobiliária e reorganizações societárias). Sem contaminação de campos atuais.
Razão observado/esperado dentro do mesmo porte (MEI, ME, EPP, demais) e da mesma faixa de idade.
Saída: resultados/p2b_fatores_2023.csv"""
import pandas as pd
from base import salvar, RAIZ
import duckdb, pathlib
P4 = RAIZ / "dados/processados_2023-05/p4"
con = duckdb.connect(); con.execute(f"SET threads=2; SET memory_limit='2200MB'; SET enable_progress_bar=false; SET temp_directory='{pathlib.Path.home()/'duck_tmp'}'")
D = "substr(cnae_principal,1,2)"
con.execute(f"""CREATE TABLE q AS SELECT y_fechou::INT f, y_fechou_div::INT fd, y_nova_divida::INT nd, grupo_23 grupo,
  CASE WHEN idade_anos < 1 THEN '0 menos de 1 ano' WHEN idade_anos < 3 THEN '1 1 a 3 anos' WHEN idade_anos < 5 THEN '2 3 a 5 anos'
       WHEN idade_anos < 10 THEN '3 5 a 10 anos' WHEN idade_anos < 20 THEN '4 10 a 20 anos' ELSE '5 20 anos ou mais' END idade,
  CASE WHEN {D} BETWEEN '01' AND '03' THEN 'A Agropecuária' WHEN {D} BETWEEN '05' AND '09' THEN 'B Extração'
   WHEN {D} BETWEEN '10' AND '33' THEN 'C Indústria' WHEN {D} BETWEEN '35' AND '39' THEN 'D/E Energia, água e resíduos'
   WHEN {D} BETWEEN '41' AND '43' THEN 'F Construção' WHEN {D} BETWEEN '45' AND '47' THEN 'G Comércio'
   WHEN {D} BETWEEN '49' AND '53' THEN 'H Transporte' WHEN {D} = '55' THEN 'I1 Alojamento' WHEN {D} = '56' THEN 'I2 Alimentação'
   WHEN {D} BETWEEN '58' AND '63' THEN 'J Informação e comunicação' WHEN {D} BETWEEN '64' AND '66' THEN 'K Financeiro'
   WHEN {D} = '68' THEN 'L Imobiliário' WHEN {D} BETWEEN '69' AND '75' THEN 'M Profissionais e técnicas'
   WHEN {D} BETWEEN '77' AND '82' THEN 'N Administrativas' WHEN {D} = '85' THEN 'P Educação'
   WHEN {D} BETWEEN '86' AND '88' THEN 'Q Saúde' WHEN {D} BETWEEN '90' AND '93' THEN 'R Artes e lazer' ELSE 'S Outros serviços' END secao,
  CASE natureza_juridica WHEN 2135 THEN 'Empresário individual' WHEN 2062 THEN 'Sociedade limitada' WHEN 2305 THEN 'EIRELI'
   WHEN 2054 THEN 'S.A. fechada' WHEN 2240 THEN 'Sociedade simples limitada' ELSE 'Outras' END natureza,
  CASE WHEN populacao IS NULL THEN '9 sem dado' WHEN populacao < 20000 THEN '1 até 20 mil' WHEN populacao < 100000 THEN '2 20 a 100 mil' WHEN populacao < 500000 THEN '3 100 a 500 mil' ELSE '4 mais de 500 mil' END cidade,
  CASE WHEN capital_social IS NULL OR capital_social = 0 THEN '0 zero' WHEN capital_social <= 1000 THEN '1 até R$ 1 mil'
   WHEN capital_social <= 10000 THEN '2 R$ 1 a 10 mil' WHEN capital_social <= 50000 THEN '3 R$ 10 a 50 mil'
   WHEN capital_social <= 200000 THEN '4 R$ 50 a 200 mil' ELSE '5 mais de R$ 200 mil' END capital,
  CASE WHEN n_cnae_sec = 0 THEN '0 nenhuma' WHEN n_cnae_sec <= 2 THEN '1 1 a 2' WHEN n_cnae_sec <= 5 THEN '2 3 a 5' ELSE '3 6 ou mais' END atividades_sec,
  tem_email, tem_telefone, tem_fantasia, simples_23,
  CASE WHEN n_filiais = 0 THEN '0 nenhuma' WHEN n_filiais <= 2 THEN '1 1 a 2' ELSE '2 3 ou mais' END filiais,
  CASE WHEN c1_socios_pf IS NULL THEN '0 sem sócio PF no quadro' WHEN c1_socios_pf = 1 THEN '1 um sócio' WHEN c1_socios_pf = 2 THEN '2 dois sócios' ELSE '3 três ou mais' END socios,
  CASE WHEN c1_socios_pf IS NULL THEN 'sem sócio PF no quadro' WHEN n_outras_fechadas_divida > 0 THEN '4 sócio já fechou empresa com dívida ativa'
   WHEN n_outras_ativas_divida > 0 THEN '3 sócio tem outra empresa ativa com dívida' WHEN n_outras_fechadas > 0 THEN '2 sócio já fechou empresa (sem dívida)'
   WHEN n_outras_ativas > 0 THEN '1 sócio tem outra empresa ativa' ELSE '0 única empresa dos sócios' END historico_socios,
  CASE WHEN c1_socios_pf IS NULL THEN 'sem sócio PF' ELSE coalesce(mudou_socio_12m, false)::VARCHAR END mudou_socio_12m,
  CASE WHEN t1_inscricoes = 0 THEN '0 sem dívida ativa' WHEN t1_valor < 10000 THEN '1 dívida até R$ 10 mil'
   WHEN t1_valor < 100000 THEN '2 dívida R$ 10 a 100 mil' ELSE '3 dívida acima de R$ 100 mil' END divida_23,
  tem_situacao_especial, uf
FROM read_parquet('{P4}/p4_*.parquet') WHERE cnae_principal <> '4110700' AND NOT reorganizada""")
con.execute("CREATE TABLE e AS SELECT grupo, idade, avg(f) ef, avg(fd) efd, avg(nd) end_ FROM q GROUP BY ALL")
CARAC = {"porte em mai/2023": "grupo", "idade da empresa": "idade", "setor (seção CNAE)": "secao", "natureza jurídica": "natureza",
         "tamanho da cidade": "cidade", "capital social": "capital", "atividades secundárias": "atividades_sec", "tem e-mail": "tem_email",
         "tem telefone": "tem_telefone", "tem nome fantasia": "tem_fantasia", "no Simples Nacional": "simples_23", "filiais": "filiais",
         "número de sócios PF": "socios", "histórico dos sócios (C1)": "historico_socios", "entrou sócio nos últimos 12 meses": "mudou_socio_12m",
         "dívida ativa da União em mar/2023 (PGFN 2023 T1)": "divida_23", "situação especial": "tem_situacao_especial", "UF": "uf"}
out = []
for nome, col in CARAC.items():
    df = con.execute(f"""SELECT {col}::VARCHAR valor, count(*) empresas, 100*avg(f) fechou_pct, sum(f)/sum(ef) razao,
        100*avg(fd) fechou_divida_pct, sum(fd)/sum(efd) razao_divida, 100*avg(nd) nova_divida_pct, sum(nd)/sum(end_) razao_nova_divida
        FROM q JOIN e USING (grupo, idade) GROUP BY 1 ORDER BY 1""").df()
    out.append(df.assign(caracteristica=nome))
r = pd.concat(out)[["caracteristica", "valor", "empresas", "fechou_pct", "razao", "fechou_divida_pct", "razao_divida", "nova_divida_pct", "razao_nova_divida"]]
r = r[r.empresas >= 1000].round(3)
salvar(r, "p2b_fatores_2023.csv"); pd.set_option("display.width", 250); print(r.to_string())
