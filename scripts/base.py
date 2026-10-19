# -*- coding: utf-8 -*-
"""Caminhos e conexão DuckDB comuns. As tabelas Parquet viram views com os mesmos nomes."""
import duckdb, pathlib
RAIZ = pathlib.Path(__file__).resolve().parents[1]
PROC, RES = RAIZ / "dados/processados", RAIZ / "resultados"
DATA_BASE = "2026-10-11"   # data da extração da Receita (última data de situação na base)

def conectar():
    con = duckdb.connect()
    tmp = pathlib.Path.home() / "duck_tmp"; tmp.mkdir(exist_ok=True)
    con.execute(f"SET memory_limit='1500MB'; SET threads=2; SET enable_progress_bar=false; SET temp_directory='{tmp}'; SET preserve_insertion_order=false")
    for t in ["estab", "empresas", "simples", "socios", "pgfn", "scr", "base"]:
        con.execute(f"CREATE VIEW {t} AS SELECT * FROM read_parquet('{PROC / t}/*.parquet')")
    for t in ["Cnaes", "Municipios", "Motivos", "Naturezas", "Qualificacoes"]:
        con.execute(f"CREATE VIEW aux_{t.lower()} AS SELECT column0 codigo, column1 descricao FROM read_csv('{PROC}/aux/{t}.csv', delim=';', header=false, all_varchar=true)")
    return con

def salvar(df, nome):
    RES.mkdir(exist_ok=True)
    df.to_csv(RES / nome, index=False, encoding="utf-8-sig")
    return df
