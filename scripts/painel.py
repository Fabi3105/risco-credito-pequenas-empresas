# -*- coding: utf-8 -*-
"""Gera o painel index.html: modelo (scripts/painel_modelo.html) + dados (resultados/painel_dados.json, de painel_dados.py)."""
from base import RAIZ
m = (RAIZ / "scripts/painel_modelo.html").read_text(encoding='utf-8'); d = (RAIZ / "resultados/painel_dados.json").read_text(encoding='utf-8')
import base64
assert '__DADOS__' in m and '__FLUXO__' in m
m = m.replace('__FLUXO__', 'data:image/png;base64,' + base64.b64encode((RAIZ / "graficos/g11_fluxo_decisao.png").read_bytes()).decode())   # fluxograma do relatório
(RAIZ / "index.html").write_text(m.replace('__DADOS__', d.replace('</', '<\\/')), encoding='utf-8'); print('index.html', round((RAIZ / "index.html").stat().st_size / 1e6, 2), 'MB')
