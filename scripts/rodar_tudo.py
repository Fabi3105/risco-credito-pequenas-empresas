# -*- coding: utf-8 -*-
"""Roda o estudo na ordem: testes → (conversão e bases, opcional) → validação → análises → nota → oportunidades → gráficos → painel → conferências.
Uso: python rodar_tudo.py            (do passo 1 ao fim, sem a conversão dos dados brutos)
     python rodar_tudo.py 5 9        (do passo 5 ao 8)
     python rodar_tudo.py --completo (inclui a conversão dos arquivos brutos e a montagem das bases; horas de processamento)
Passos que rodam por partição repetem o script para cada dígito/código. Num ambiente com pouca memória, rode por partes."""
import subprocess, sys, os
P = lambda *a: [sys.executable, *a]
DIG = [str(d) for d in range(10)]; HEX = list('0123456789abcdef')
# PGFN e SCR: etl_pgfn.py <zip> <membro> e etl_scr.py <zip> rodam por arquivo (nomes em dados/FONTES.md), antes destes passos.
CONVERSAO = ([P('etl_cnpj.py', t, d) for t in ('empresas', 'estab', 'socios') for d in DIG] + [P('etl_cnpj.py', 'simples', '0')] +
             [P('montar_base.py', d) for d in DIG] + [P('q1_sobrevivencia.py', '--montar'), P('municipios_ibge.py')] + [P('c1_socios.py', h) for h in HEX] +
             [P('p2_montar.py', '2012', '2015'), P('p2_montar.py', '2016', '2020')] + [P('montar_base_2023.py', d) for d in DIG] +
             [P('pgfn_devedores_2023.py')] + [P('c1_socios_2023.py', h) for h in HEX] + [P('p4_montar.py', d) for d in DIG] + [P('p3_base_2026.py', d) for d in DIG])
# (para 2023-05: EXTRACAO=2023-05 nos etl_cnpj; PGFN_PERIODO=2023T1 no etl_pgfn — ver dados/FONTES.md)
PASSOS = [
    ('testes das contas sensíveis', [P('testes.py')]),
    ('validação dos dados', [P('validar_dados.py')]),
    ('P1 sobrevivência (números oficiais, setores, cidades, enchente, alojamento e alimentação)', [P('q1_oficial.py'), P('q1b_horizonte_setores.py'), P('q1c_cidades.py'), P('q1d_rs_enchente.py'), P('q1e_alojamento_alimentacao.py', 'a'), P('q1e_alojamento_alimentacao.py', 'b')]),
    ('C2 concorrência local', [P('q2_concorrencia.py', '--contar'), P('q2_concorrencia.py'), P('q2b_concorrencia_fechamento.py')]),
    ('P2 e C3 sinais de risco e época', [P('p2_fatores.py'), P('p2b_fatores_2023.py'), P('c3_epoca_abertura.py')]),
    ('P4 nota de risco', [P('p4_amostra.py'), P('p4_features.py'), P('p4_tabela.py'), P('p4_modelo.py', 'y_nova_divida', 'geral'), P('p4_modelo.py', 'y_nova_divida', 'scorecard'),
                          P('p4_modelo.py', 'y_fechou', 'geral'), P('p4_modelo.py', 'y_fechou', 'scorecard'), P('p4_modelo.py', 'y_nova_divida', 'setor'),
                          P('p4_scorecard.py', 'y_nova_divida'), P('p4_scorecard.py', 'y_fechou'), P('p4_pontuar.py'), P('p4_alerta_lgbm.py'),
                          P('p4_matriz_duas_notas.py'), P('p4_calibra_scr.py'), P('gerar_anexo_p4.py'), P('conferir_p4.py')]),
    ('P3 e C4 bons clientes e MEIs que crescem', [P('p3_notas_2026.py', d) for d in DIG] + [P('p3_oportunidades.py'), P('p3_rs.py'), P('p3_municipios.py'), P('c4_mei_cresce.py')]),
    ('pilotos e metas', [P('p5_pilotos_metas.py')]),
    ('gráficos, painel e relatório', [P('graficos.py'), P('painel_dados.py'), P('painel.py'), P('teste_calculadora.py'), P('relatorio_html.py')]),
    ('conferência do relatório', [P('conferir_relatorio.py')]),
]
args = [a for a in sys.argv[1:] if not a.startswith('--')]
ini = int(args[0]) if args else 1; fim = int(args[1]) if len(args) > 1 else len(PASSOS) + 1
os.chdir(os.path.dirname(os.path.abspath(__file__)))
if '--completo' in sys.argv:
    for c in CONVERSAO: print('>>', ' '.join(c[1:])); subprocess.run(c, check=True)
for i, (nome, cmds) in enumerate(PASSOS, 1):
    if not (ini <= i < fim): continue
    print(f"\n=== {i}. {nome} ===")
    for c in cmds: print('>>', ' '.join(c[1:])); subprocess.run(c, check=True)
print("\nconcluído")
