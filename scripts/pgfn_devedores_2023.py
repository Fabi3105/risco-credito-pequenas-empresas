# -*- coding: utf-8 -*-
"""Lista de CNPJs básicos devedores principais na PGFN em mar/2023 (arquivo 2023 T1), usada por c1_socios_2023.py.
Saída: dados/processados_2023-05/pgfn_2023T1_devedores.parquet"""
import duckdb, pathlib, shutil
from base import RAIZ
P23 = RAIZ / "dados/processados_2023-05"; tmp = pathlib.Path.home() / "tmp_dev.parquet"
con = duckdb.connect(); con.execute("SET threads=2; SET memory_limit='1500MB'")
con.execute(f"COPY (SELECT DISTINCT cnpj_basico FROM read_parquet('{P23}/pgfn_2023T1/*.parquet') WHERE upper(tipo_devedor) = 'PRINCIPAL') TO '{tmp}' (FORMAT parquet)")
shutil.move(str(tmp), str(P23 / "pgfn_2023T1_devedores.parquet")); print(con.execute(f"select count(*) from '{P23}/pgfn_2023T1_devedores.parquet'").fetchone())
