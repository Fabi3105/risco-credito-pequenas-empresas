# -*- coding: utf-8 -*-
"""Dívida ativa da União (PGFN, 2º tri/2026) -> Parquet só com pessoas jurídicas, sem nomes.
Uso: [PGFN_PERIODO=2023T1] python etl_pgfn.py <zip> <membro>   (ex.: PGFN_2026T2_Previdenciario.zip arquivo_lai_PREV_1_202606.csv)
Grava dados/processados/pgfn/<membro>.parquet com: cnpj_basico, sistema, tipo_devedor, tipo_situacao, data_inscricao,
ajuizado, valor. Datas inválidas (ex.: 01/01/1000) viram nulo."""
import sys, subprocess, duckdb, pathlib, shutil
RAIZ = pathlib.Path(__file__).resolve().parents[1]
import os
PER = os.environ.get("PGFN_PERIODO", "2026T2")   # 2026T2 (padrão) ou 2023T1 (posição antes do corte da P4)
BR, OUT = (RAIZ / "dados/brutos/pgfn", RAIZ / "dados/processados/pgfn") if PER == "2026T2" else (RAIZ / f"dados/brutos/pgfn_{PER}", RAIZ / f"dados/processados_2023-05/pgfn_{PER}")
z, membro = sys.argv[1], sys.argv[2]
sistema = "FGTS" if "FGTS" in membro else ("previdenciaria" if "PREV" in membro else "nao_previdenciaria")
OUT.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path.home() / f"tmp_{membro}"
subprocess.run(f"unzip -p '{BR / z}' '{membro}' | iconv -f latin1 -t utf-8 > '{tmp}'", shell=True, check=True)
tmp_pq = tmp.with_suffix(".parquet")
con = duckdb.connect(); con.execute("SET memory_limit='1200MB'; SET threads=2; SET preserve_insertion_order=false; SET enable_progress_bar=false")
con.execute(f"""COPY (
  SELECT substr(regexp_replace(CPF_CNPJ, '[^0-9]', '', 'g'), 1, 8) cnpj_basico, '{sistema}' sistema,
         TIPO_DEVEDOR tipo_devedor, TIPO_SITUACAO_INSCRICAO tipo_situacao,
         CASE WHEN TRY_STRPTIME(DATA_INSCRICAO, '%d/%m/%Y') >= DATE '1950-01-01' THEN TRY_STRPTIME(DATA_INSCRICAO, '%d/%m/%Y')::DATE END data_inscricao,
         INDICADOR_AJUIZADO = 'SIM' ajuizado, TRY_CAST(VALOR_CONSOLIDADO AS DOUBLE) valor
  FROM read_csv('{tmp}', delim=';', header=true, all_varchar=true, quote='"', ignore_errors=false)
  WHERE TIPO_PESSOA ILIKE 'Pessoa jur%') TO '{tmp_pq}' (FORMAT parquet, COMPRESSION zstd)""")
n = con.execute(f"SELECT count(*) FROM '{tmp_pq}'").fetchone()[0]
tmp.unlink(); shutil.move(str(tmp_pq), str(OUT / (membro.replace('.csv', '') + '.parquet')))
print(membro, n)
