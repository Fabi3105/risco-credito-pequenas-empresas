# -*- coding: utf-8 -*-
"""RELATORIO.md -> relatorio_impressao.html (identidade "Mesa de crédito", gráficos embutidos), base do RELATORIO.pdf.
O PDF é gerado com Chromium (page.pdf, A4, rodapé com título curto e página)."""
import base64, re, markdown
from base import RAIZ
md = (RAIZ / "RELATORIO.md").read_text(encoding='utf-8')
def img(m):
    p = RAIZ / m.group(2); b = base64.b64encode(p.read_bytes()).decode()
    return f'<figure><img alt="{m.group(1)}" src="data:image/png;base64,{b}"></figure>'
md = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", img, md)
html = markdown.markdown(md, extensions=['tables', 'sane_lists'])
html = html.replace('<h2>Sumário executivo</h2>', '<h2 class="secao">Sumário executivo</h2>')
html = re.sub(r'<h2>(\d\. [^<]+)</h2>', r'<h2 class="secao">\1</h2>', html)
html = re.sub(r'<h2>(Anexo [^<]+)</h2>', r'<h2 class="anexo">\1</h2>', html).replace('<h2 class="anexo">Anexo A.', '<h2 class="anexo" id="anexo-a">Anexo A.')
# quadro de KPIs: primeira tabela depois de "A situação em poucos números" vira cartões
def kpis(m):
    linhas = re.findall(r'<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>', m.group(0), re.S)
    return '<div class="kpis">' + ''.join(f'<div class="kpi"><b>{v}</b><span>{k}</span></div>' for k, v in linhas) + '</div>'
html = re.sub(r'(?<=A situação em poucos números</h3>\n)<table>.*?</table>', kpis, html, count=1, flags=re.S)
css = """@page{size:A4;margin:16mm 15mm 18mm}
body{font:10pt/1.45 'IBM Plex Sans','Liberation Sans','DejaVu Sans',sans-serif;color:#0E3B43}
h1{font-size:20pt;margin:0 0 6px;padding:14px 16px;background:#0E3B43;color:#fff;border-bottom:4px solid #1F7A4D}
h2{font-size:14pt;margin:18px 0 6px}
h2.secao{background:#0E3B43;color:#fff;padding:6px 10px;border-left:6px solid #1F7A4D;page-break-after:avoid}
h2.anexo{border-bottom:2px solid #1F7A4D;padding-bottom:3px;page-break-after:avoid}
h2#anexo-a{page-break-before:always}h3{page-break-after:avoid}
h3{font-size:11.5pt;margin:12px 0 4px;color:#0E3B43}
p,li{margin:4px 0}ul,ol{padding-left:18px}
table{border-collapse:collapse;width:100%;margin:6px 0 10px;font-size:8.6pt;page-break-inside:avoid}
th{background:#E8EEEE;text-align:left;padding:4px 6px;border-bottom:1.5px solid #0E3B43}
td{padding:4px 6px;border-bottom:1px solid #D5DFE0;vertical-align:top}
figure{margin:8px 0 10px;text-align:center;page-break-inside:avoid}figure img{max-width:100%;max-height:105mm}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:6px 0 10px}
.kpi{border:1px solid #D5DFE0;border-left:4px solid #0E3B43;border-radius:3px;padding:6px 8px;page-break-inside:avoid}
.kpi b{display:block;font:600 13pt 'IBM Plex Mono','Liberation Mono','DejaVu Sans Mono',monospace}.kpi span{font-size:8pt;color:#3E5A60}
code{font-family:'IBM Plex Mono','Liberation Mono',monospace;font-size:8.6pt;background:#F3F6F5;padding:0 3px}
hr{border:none;border-top:1px solid #D5DFE0;margin:12px 0}
strong{color:#0E3B43}"""
doc = f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Sobrevivência de pequenas empresas e risco de crédito PJ</title><style>{css}</style></head><body>{html}</body></html>'
(RAIZ / "relatorio_impressao.html").write_text(doc, encoding='utf-8'); print('ok', len(doc) // 1000, 'KB')
