# -*- coding: utf-8 -*-
"""SCR.data (Banco Central) -> Parquet só com pessoas jurídicas, por mês.
Uso: python etl_scr.py <zip> [membro ...]  (sem membros: todos os CSVs do zip)
Valores com vírgula decimal convertidos para número. Grava dados/processados/scr/<membro>.parquet."""
import sys, subprocess, duckdb, pathlib, shutil
RAIZ = pathlib.Path(__file__).resolve().parents[1]
BR, OUT = RAIZ / "dados/brutos/scr", RAIZ / "dados/processados/scr"
OUT.mkdir(parents=True, exist_ok=True)
z = sys.argv[1]
membros = sys.argv[2:] or subprocess.run(f"unzip -Z1 '{BR / z}'", shell=True, capture_output=True, text=True).stdout.split()
num = lambda c: f"TRY_CAST(replace(replace({c}, '.', ''), ',', '.') AS DOUBLE) {c}"
for m in membros:
    destino = OUT / m.replace(".csv", ".parquet")
    if destino.exists():
        continue
    tmp = pathlib.Path.home() / f"tmp_{m}"
    subprocess.run(f"unzip -p '{BR / z}' '{m}' > '{tmp}'", shell=True, check=True)
    con = duckdb.connect(); con.execute("SET memory_limit='1200MB'; SET threads=2; SET enable_progress_bar=false")
    tmp_pq = tmp.with_suffix(".parquet")
    con.execute(f"""COPY (SELECT data_base::DATE data_base, uf, trim(cnae_secao) cnae_secao, trim(cnae_subclasse) cnae_subclasse,
        trim(porte) porte, trim(modalidade) modalidade, trim(origem) origem, TRY_CAST(numero_de_operacoes AS BIGINT) numero_de_operacoes,
        {num('vencido_acima_de_15_dias')}, {num('carteira_ativa')}, {num('carteira_inadimplida_arrastada')}, {num('ativo_problematico')}
      FROM read_csv('{tmp}', delim=';', header=true, all_varchar=true) WHERE cliente = 'PJ') TO '{tmp_pq}' (FORMAT parquet)""")
    n = con.execute(f"SELECT count(*) FROM '{tmp_pq}'").fetchone()[0]
    tmp.unlink(); shutil.move(str(tmp_pq), str(destino)); print(m, n, flush=True)
