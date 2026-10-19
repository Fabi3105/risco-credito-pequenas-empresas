# -*- coding: utf-8 -*-
"""P2 — Características na abertura associadas a mais ou menos fechamento em 5 anos (turmas 2016-2020).
Para cada característica: fechamento em 5 anos e fechamento com dívida ativa, e a razão observado/esperado dentro do
mesmo porte (MEI, ME, EPP, demais), para não confundir a característica com o porte.
Saída: resultados/p2_fatores.csv"""
import pandas as pd
from base import conectar, salvar, PROC
con = conectar()
con.execute(f"""CREATE VIEW p AS SELECT *,
  (evento AND dur < 5) f5, (evento AND dur < 5 AND tem_pgfn) f5d,
  CASE WHEN substr(cnae_principal,1,2) BETWEEN '01' AND '03' THEN 'A Agropecuária' WHEN substr(cnae_principal,1,2) BETWEEN '05' AND '09' THEN 'B Extração'
   WHEN substr(cnae_principal,1,2) BETWEEN '10' AND '33' THEN 'C Indústria' WHEN substr(cnae_principal,1,2) BETWEEN '35' AND '39' THEN 'D/E Energia, água e resíduos'
   WHEN substr(cnae_principal,1,2) BETWEEN '41' AND '43' THEN 'F Construção' WHEN substr(cnae_principal,1,2) BETWEEN '45' AND '47' THEN 'G Comércio'
   WHEN substr(cnae_principal,1,2) BETWEEN '49' AND '53' THEN 'H Transporte' WHEN substr(cnae_principal,1,2) IN ('55','56') THEN 'I Alojamento e alimentação'
   WHEN substr(cnae_principal,1,2) BETWEEN '58' AND '63' THEN 'J Informação e comunicação' WHEN substr(cnae_principal,1,2) BETWEEN '64' AND '66' THEN 'K Financeiro'
   WHEN substr(cnae_principal,1,2) = '68' THEN 'L Imobiliário' WHEN substr(cnae_principal,1,2) BETWEEN '69' AND '75' THEN 'M Profissionais e técnicas'
   WHEN substr(cnae_principal,1,2) BETWEEN '77' AND '82' THEN 'N Administrativas' WHEN substr(cnae_principal,1,2) = '85' THEN 'P Educação'
   WHEN substr(cnae_principal,1,2) BETWEEN '86' AND '88' THEN 'Q Saúde' WHEN substr(cnae_principal,1,2) BETWEEN '90' AND '93' THEN 'R Artes e lazer'
   ELSE 'S Outros serviços' END secao,
  CASE natureza_juridica WHEN 2135 THEN 'Empresário individual' WHEN 2062 THEN 'Sociedade limitada' WHEN 2305 THEN 'EIRELI'
   WHEN 2054 THEN 'S.A. fechada' WHEN 2240 THEN 'Sociedade simples limitada' ELSE 'Outras' END natureza,
  CASE WHEN populacao < 20000 THEN '1 até 20 mil' WHEN populacao < 100000 THEN '2 20 a 100 mil' WHEN populacao < 500000 THEN '3 100 a 500 mil' ELSE '4 mais de 500 mil' END cidade,
  CASE WHEN capital_social IS NULL OR capital_social = 0 THEN '0 zero' WHEN capital_social <= 1000 THEN '1 até R$ 1 mil'
   WHEN capital_social <= 10000 THEN '2 R$ 1 a 10 mil' WHEN capital_social <= 50000 THEN '3 R$ 10 a 50 mil'
   WHEN capital_social <= 200000 THEN '4 R$ 50 a 200 mil' ELSE '5 mais de R$ 200 mil' END capital,
  CASE WHEN n_cnae_sec = 0 THEN '0 nenhuma' WHEN n_cnae_sec <= 2 THEN '1 1 a 2' WHEN n_cnae_sec <= 5 THEN '2 3 a 5' ELSE '3 6 ou mais' END atividades_sec,
  CASE WHEN n_socios_pf IS NULL THEN '0 sem quadro de sócios (MEI/individual)' WHEN n_socios_pf = 1 THEN '1 um sócio' WHEN n_socios_pf = 2 THEN '2 dois sócios' ELSE '3 três ou mais' END socios,
  CASE WHEN n_socios_pf IS NULL THEN 'sem quadro de sócios' WHEN n_fech_div_ant > 0 THEN '3 sócio já fechou empresa com dívida ativa'
   WHEN n_fech_ant > 0 THEN '2 sócio já fechou empresa (sem dívida)' WHEN n_ativas_ab > 0 THEN '1 sócio já tem outra empresa ativa'
   ELSE '0 primeira empresa dos sócios' END historico_socios
FROM read_parquet('{PROC}/p2/p2_2016_2020.parquet') WHERE cnae_principal <> '4110700'""")
con.execute("CREATE TEMP TABLE q AS SELECT *, avg(f5::INT) OVER (PARTITION BY grupo) e5, avg(f5d::INT) OVER (PARTITION BY grupo) e5d FROM p")
CARAC = {"porte na abertura": "grupo", "setor (seção CNAE)": "secao", "natureza jurídica": "natureza", "tamanho da cidade": "cidade",
         "capital social (valor atual)": "capital", "atividades secundárias": "atividades_sec", "tem e-mail": "tem_email",
         "tem telefone": "tem_telefone", "tem nome fantasia": "tem_fantasia", "Simples Nacional na abertura": "simples_na_abertura",
         "número de sócios PF": "socios", "histórico dos sócios (C1)": "historico_socios", "região (UF)": "uf"}
out = []
for nome, col in CARAC.items():
    df = con.execute(f"""SELECT {col}::VARCHAR valor, count(*) empresas, 100*avg(f5::INT) fecha5_pct, sum(f5::INT)/sum(e5) razao_mesmo_porte,
        100*avg(f5d::INT) fecha5_divida_pct, sum(f5d::INT)/sum(e5d) razao_divida_mesmo_porte FROM q GROUP BY 1 ORDER BY 1""").df()
    out.append(df.assign(caracteristica=nome))
r = pd.concat(out)[["caracteristica", "valor", "empresas", "fecha5_pct", "razao_mesmo_porte", "fecha5_divida_pct", "razao_divida_mesmo_porte"]]
r = r[r.empresas >= 1000].round(3)
salvar(r, "p2_fatores.csv"); print(r.to_string())
