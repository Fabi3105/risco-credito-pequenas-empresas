# -*- coding: utf-8 -*-
"""Converte os .zip do CNPJ (Receita, out/2026) em Parquet enxuto, sem nomes, endereços nem contatos.
Uso: python etl_cnpj.py <tabela> <n> [inicio fim]   (tabela: estab|empresas|socios|simples|aux; n = número do arquivo)
Lê o CSV direto do zip (unzip -p) e grava em dados/processados/<tabela>/<tabela>_<n>[_parte].parquet.
Estabelecimentos0 é grande demais para uma chamada: passe as linhas inicio e fim para dividir."""
import sys, subprocess, duckdb, pathlib, shutil
RAIZ = pathlib.Path(__file__).resolve().parents[1]
import os
EXTRACAO = os.environ.get("EXTRACAO", "2026-10")   # 2026-10 (principal) ou 2023-05 (retrato do passado)
BR = RAIZ / f"dados/brutos/{EXTRACAO}"
OUT = RAIZ / ("dados/processados" if EXTRACAO == "2026-10" else f"dados/processados_{EXTRACAO}")

COLS = {
 "estab": ["cnpj_basico","cnpj_ordem","cnpj_dv","matriz_filial","nome_fantasia","situacao","data_situacao","motivo_situacao",
           "cidade_exterior","pais","data_inicio","cnae_principal","cnae_secundaria","tipo_logradouro","logradouro","numero",
           "complemento","bairro","cep","uf","municipio","ddd1","telefone1","ddd2","telefone2","ddd_fax","fax","email",
           "situacao_especial","data_situacao_especial"],
 "empresas": ["cnpj_basico","razao_social","natureza_juridica","qualificacao_responsavel","capital_social","porte","ente_federativo"],
 "socios": ["cnpj_basico","identificador_socio","nome_socio","cpf_cnpj_socio","qualificacao_socio","data_entrada","pais",
            "representante_legal","nome_representante","qualificacao_representante","faixa_etaria"],
 "simples": ["cnpj_basico","opcao_simples","data_opcao_simples","data_exclusao_simples","opcao_mei","data_opcao_mei","data_exclusao_mei"],
}
SELECT = {
 "estab": """cnpj_basico, cnpj_ordem, matriz_filial::TINYINT matriz_filial, situacao::TINYINT situacao,
   TRY_STRPTIME(NULLIF(data_situacao,'0'),'%Y%m%d')::DATE data_situacao, TRY_CAST(motivo_situacao AS SMALLINT) motivo_situacao,
   TRY_STRPTIME(data_inicio,'%Y%m%d')::DATE data_inicio, cnae_principal,
   CASE WHEN cnae_secundaria IS NULL OR cnae_secundaria='' THEN 0 ELSE len(string_split(cnae_secundaria,',')) END::SMALLINT n_cnae_sec,
   uf, TRY_CAST(municipio AS INTEGER) municipio_rf, (email IS NOT NULL AND email<>'')::BOOLEAN tem_email,
   (telefone1 IS NOT NULL AND telefone1<>'')::BOOLEAN tem_telefone, (nome_fantasia IS NOT NULL AND nome_fantasia<>'')::BOOLEAN tem_fantasia,
   (situacao_especial IS NOT NULL AND situacao_especial<>'')::BOOLEAN tem_situacao_especial""",
 "empresas": """cnpj_basico, TRY_CAST(natureza_juridica AS SMALLINT) natureza_juridica, TRY_CAST(qualificacao_responsavel AS SMALLINT) qualificacao_responsavel,
   TRY_CAST(replace(capital_social,',','.') AS DOUBLE) capital_social, TRY_CAST(porte AS TINYINT) porte""",
 # sócio: sem nome; CPF mascarado mantido só como parte da chave de pessoa (cálculos agregados, nunca publicado)
 "socios": """cnpj_basico, TRY_CAST(identificador_socio AS TINYINT) tipo_socio, md5(coalesce(nome_socio,'')||'|'||coalesce(cpf_cnpj_socio,'')) pessoa,
   TRY_CAST(qualificacao_socio AS SMALLINT) qualificacao_socio, TRY_STRPTIME(NULLIF(data_entrada,'0'),'%Y%m%d')::DATE data_entrada,
   TRY_CAST(faixa_etaria AS TINYINT) faixa_etaria""",
 "simples": """cnpj_basico, opcao_simples, TRY_STRPTIME(NULLIF(data_opcao_simples,'00000000'),'%Y%m%d')::DATE data_opcao_simples,
   TRY_STRPTIME(NULLIF(data_exclusao_simples,'00000000'),'%Y%m%d')::DATE data_exclusao_simples, opcao_mei,
   TRY_STRPTIME(NULLIF(data_opcao_mei,'00000000'),'%Y%m%d')::DATE data_opcao_mei,
   TRY_STRPTIME(NULLIF(data_exclusao_mei,'00000000'),'%Y%m%d')::DATE data_exclusao_mei""",
}
ZIP = {"estab": "Estabelecimentos{}.zip", "empresas": "Empresas{}.zip", "socios": "Socios{}.zip", "simples": "Simples.zip"}

def converte(tab, n, ini=None, fim=None):
    z = BR / ZIP[tab].format(n)
    if not z.exists():
        z = BR / (f"{EXTRACAO}_" + ZIP[tab].format(n))
    (OUT / tab).mkdir(parents=True, exist_ok=True)
    sufixo = f"_{ini}" if ini is not None else ""
    destino = OUT / tab / f"{tab}_{n}{sufixo}.parquet"
    cmd = f"unzip -p '{z}'"
    if ini is not None:
        cmd += f" | tail -n +{int(ini) + 1} | head -n {int(fim) - int(ini)}"
    tmp = pathlib.Path.home() / f"tmp_{tab}_{n}{sufixo}.csv"
    subprocess.run(f"{cmd} | iconv -f latin1 -t utf-8 > '{tmp}'", shell=True, check=True)
    tmp_pq = tmp.with_suffix('.parquet')
    con = duckdb.connect()
    con.execute("SET memory_limit='1200MB'; SET threads=2; SET preserve_insertion_order=false;")
    cols = ", ".join(f"'{c}': 'VARCHAR'" for c in COLS[tab])
    con.execute(f"""COPY (SELECT {SELECT[tab]} FROM read_csv('{tmp}', delim=';', quote='"', header=false,
        columns={{{cols}}}, ignore_errors=false, auto_detect=false, parallel=true)) TO '{tmp_pq}' (FORMAT parquet, COMPRESSION zstd)""")
    n_linhas = con.execute(f"SELECT count(*) FROM '{tmp_pq}'").fetchone()[0]
    tmp.unlink()
    shutil.move(str(tmp_pq), str(destino))   # grava fora da pasta sincronizada e só depois move
    print(destino.name, n_linhas)

if __name__ == "__main__":
    a = sys.argv[1:]
    converte(a[0], a[1], *(a[2:4] if len(a) > 2 else []))
