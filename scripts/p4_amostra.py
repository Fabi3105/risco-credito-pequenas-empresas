# -*- coding: utf-8 -*-
"""Amostra para o modelo de risco (P4): 10% das empresas ativas em mai/2023 (sorteio fixo pelo hash do CNPJ),
fora incorporação imobiliária e reorganizações societárias. Separação treino/teste também pelo hash (70/30),
para que nenhuma empresa apareça nos dois. Saída: dados/processados_2023-05/p4_amostra.parquet"""
import duckdb, pathlib
from base import RAIZ
P23 = RAIZ / "dados/processados_2023-05"
con = duckdb.connect(); con.execute(f"SET threads=2; SET memory_limit='2000MB'; SET enable_progress_bar=false; SET temp_directory='{pathlib.Path.home()/'duck_tmp'}'")
tmp = pathlib.Path.home() / "tmp_p4_amostra.parquet"
con.execute(f"""COPY (SELECT *, CASE WHEN hash(cnpj_basico || 't') % 10 < 7 THEN 'treino' ELSE 'teste' END parte
  FROM read_parquet('{P23}/p4/p4_*.parquet')
  WHERE hash(cnpj_basico) % 10 = 0 AND cnae_principal <> '4110700' AND NOT reorganizada) TO '{tmp}' (FORMAT parquet)""")
import shutil; shutil.move(str(tmp), str(P23 / "p4_amostra.parquet"))
print(con.execute(f"select parte, count(*), avg(y_fechou::int), avg(y_fechou_div::int), avg(y_nova_divida::int) from '{P23}/p4_amostra.parquet' group by 1").fetchall())
