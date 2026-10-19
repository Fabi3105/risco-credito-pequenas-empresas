# -*- coding: utf-8 -*-
"""Confere a calculadora do painel (tabela v2): roda as funções categorias(), pontuar() e regras() do index.html (Node) em 3.000 empresas
do teste, a partir dos dados BRUTOS de cada empresa, e compara faixas e notas com o modelo (Python)."""
import json, re, subprocess, pathlib, numpy as np, pandas as pd, sys
from base import RAIZ
from p4_tabela import VARIAVEIS
P23 = RAIZ / "dados/processados_2023-05"
html = (RAIZ / "index.html").read_text(encoding='utf-8')
func = "".join(re.search(rf"function {f}\(.*?\n(?=function |\$\(|const |\Z)", html, re.S).group(0) for f in ['faixaNum', 'categorias', 'pontuar', 'regras'])
# o script inteiro do painel precisa ser JavaScript válido (pega comentários // que engolem código)
scr = pathlib.Path.home() / "painel_script.js"; scr.write_text(re.findall(r"<script>(.*?)</script>", html, re.S)[-1].replace('__DADOS__', '{}'), encoding='utf-8')
chk_js = subprocess.run(['node', '--check', str(scr)], capture_output=True, text=True); assert chk_js.returncode == 0, "script do painel inválido: " + chk_js.stderr[-400:]
# dadosForm (lê o formulário) não roda no Node: confere ao menos que nenhum campo ficou dentro de um comentário de linha
df_src = re.search(r"function dadosForm\(.*?\n(?=function )", html, re.S).group(0)
assert not re.search(r"//[^\n]*\b\w+: ", df_src), "dadosForm: há campos dentro de comentário //"
for campo in ['pop:', 'pib:', 'capital:', 'idade:', 'menos1:', 'dprev:']: assert campo in re.sub(r"//[^\n]*", "", df_src), f"dadosForm sem {campo}"
A = pd.read_parquet(P23 / "p4_amostra.parquet"); A = A[A.parte == 'teste'].sample(3000, random_state=7)
X = pd.read_parquet(P23 / "p4_X2.parquet").set_index('cnpj_basico').loc[A.cnpj_basico]
n1 = pd.read_parquet(P23 / "p4_notas_teste.parquet").set_index('cnpj_basico').loc[A.cnpj_basico]; n2 = pd.read_parquet(P23 / "p4_notas_teste_fechou.parquet").set_index('cnpj_basico').loc[A.cnpj_basico]
NAT = {2135: 'empresário individual', 2062: 'sociedade limitada', 2240: 'sociedade simples', 2054: 'S.A. fechada', 2305: 'EIRELI'}
f = lambda v: None if pd.isna(v) else float(v)
reg = [dict(porte=r.grupo_23, natureza=NAT.get(int(r.natureza_juridica), 'outra natureza'), div=r.cnae_principal[:2], uf=r.uf,
            simples={'S': 'optante', 'N': 'excluída do Simples'}.get(r.opcao_simples, 'nunca optou'), idade=f(r.idade_anos), pop=f(r.populacao), pib=f(r.pib_per_capita),
            capital=f(r.capital_social) or 0.0, cnae=f(r.n_cnae_sec), filiais=f(r.n_filiais), spf=f(r.n_socios_pf), spj=f(r.n_socios_pj) or 0.0, temSocioPF=not pd.isna(r.c1_socios_pf),
            oat=f(r.n_outras_ativas) or 0.0, oatd=f(r.n_outras_ativas_divida) or 0.0, ofe=f(r.n_outras_fechadas) or 0.0, ofed=f(r.n_outras_fechadas_divida) or 0.0,
            dn=f(r.t1_inscricoes) or 0.0, dc=f(r.t1_em_cobranca) or 0.0, dv=f(r.t1_valor) or 0.0, dprev=f(r.t1_previdenciaria) or 0.0) for r in A.itertuples()]
tmp = pathlib.Path.home() / "teste_calc.js"; dados = (RAIZ / "resultados/painel_dados.json").read_text(encoding='utf-8')
tmp.write_text(f"const D = {dados};\n{func}\nconst R = {json.dumps(reg)};\nconsole.log(JSON.stringify(R.map(x => {{ const c = categorias(x); return [c, pontuar('divida', c).nota, pontuar('fechamento', c).nota, pontuar('divida', c).faixa, regras(x)]; }})));", encoding='utf-8')
out = json.loads(subprocess.run(['node', str(tmp)], capture_output=True, text=True, check=True).stdout)
cat_ok = np.mean([all(str(o[0][v]) == (str(X.iloc[i][v]) if pd.notna(X.iloc[i][v]) else 'sem dado') for v in VARIAVEIS) for i, o in enumerate(out)])
d1 = np.abs(np.array([o[1] for o in out]) - n1.nota.values); d2 = np.abs(np.array([o[2] for o in out]) - n2.nota.values); igual = np.mean([o[3] for o in out] == n1.faixa.values)
rg_js = np.array([len(o[4]) > 0 for o in out]); rg_py = X.regra_politica.notna().values; rg_ok = np.mean(rg_js == rg_py)
print(f"regras de política: mesma decisão (barrada ou não) em {100*rg_ok:.2f}%")
print(f"calculadora × modelo (3.000 empresas, dados brutos): faixas iguais nas 15 variáveis em {100*cat_ok:.2f}%; nota idêntica (até 0,01) em {100*np.mean(d1 < 0.01):.2f}% (dívida) e {100*np.mean(d2 < 0.01):.2f}% (fechamento); mesma faixa A–E em {100*igual:.2f}%")
sys.exit(0 if cat_ok > 0.99 and igual > 0.99 and rg_ok > 0.999 else 1)
