# -*- coding: utf-8 -*-
"""Monta os dados do painel (JSON embutido no index.html). Mesma fonte do relatório: resultados/*.csv."""
import json, numpy as np, pandas as pd
from base import RAIZ, RES
DIV = {'01': 'Agricultura e pecuária', '02': 'Produção florestal', '03': 'Pesca e aquicultura', '05': 'Extração de carvão', '06': 'Extração de petróleo e gás',
 '07': 'Extração de minerais metálicos', '08': 'Extração de minerais não metálicos', '09': 'Apoio à extração', '10': 'Alimentos', '11': 'Bebidas', '12': 'Fumo',
 '13': 'Têxteis', '14': 'Confecção e vestuário', '15': 'Couro e calçados', '16': 'Produtos de madeira', '17': 'Celulose e papel', '18': 'Impressão e reprodução',
 '19': 'Derivados de petróleo', '20': 'Químicos', '21': 'Farmacêuticos', '22': 'Borracha e plástico', '23': 'Minerais não metálicos', '24': 'Metalurgia',
 '25': 'Produtos de metal', '26': 'Informática e eletrônicos', '27': 'Máquinas e materiais elétricos', '28': 'Máquinas e equipamentos', '29': 'Veículos',
 '30': 'Outros equipamentos de transporte', '31': 'Móveis', '32': 'Produtos diversos', '33': 'Manutenção e instalação de máquinas', '35': 'Eletricidade e gás',
 '36': 'Água', '37': 'Esgoto', '38': 'Coleta e tratamento de resíduos', '39': 'Descontaminação', '41': 'Construção de edifícios', '42': 'Obras de infraestrutura',
 '43': 'Serviços especializados de construção', '45': 'Comércio e reparação de veículos', '46': 'Comércio atacadista', '47': 'Comércio varejista',
 '49': 'Transporte terrestre', '50': 'Transporte aquaviário', '51': 'Transporte aéreo', '52': 'Armazenagem e apoio ao transporte', '53': 'Correio e entregas',
 '55': 'Alojamento', '56': 'Alimentação (bares e restaurantes)', '58': 'Edição', '59': 'Cinema, vídeo e som', '60': 'Rádio e televisão', '61': 'Telecomunicações',
 '62': 'Tecnologia da informação', '63': 'Serviços de informação', '64': 'Serviços financeiros', '65': 'Seguros e previdência', '66': 'Auxiliares financeiros',
 '68': 'Atividades imobiliárias', '69': 'Jurídicas e contábeis', '70': 'Sedes e consultoria em gestão', '71': 'Arquitetura e engenharia', '72': 'Pesquisa e desenvolvimento',
 '73': 'Publicidade e pesquisa de mercado', '74': 'Outras atividades profissionais', '75': 'Veterinárias', '77': 'Aluguel de bens', '78': 'Seleção e agenciamento de mão de obra',
 '79': 'Agências de viagem', '80': 'Vigilância e segurança', '81': 'Serviços para edifícios', '82': 'Serviços de escritório e apoio', '84': 'Administração pública',
 '85': 'Educação', '86': 'Saúde humana', '87': 'Saúde e assistência social integradas', '88': 'Assistência social', '90': 'Artes e espetáculos', '91': 'Patrimônio cultural e ambiental',
 '92': 'Jogos e apostas', '93': 'Esporte e lazer', '94': 'Organizações associativas', '95': 'Reparação de objetos e equipamentos', '96': 'Outros serviços pessoais',
 '97': 'Serviços domésticos', '99': 'Organismos internacionais'}
SEC = {'A': 'Agropecuária', 'B': 'Extração', 'C': 'Indústria', 'DE': 'Energia, água e resíduos', 'F': 'Construção', 'G': 'Comércio', 'H': 'Transporte',
 'I': 'Alojamento e alimentação (juntos)', 'I1': 'Hotéis e pousadas', 'I2': 'Alimentação', 'J': 'Informação e comunicação', 'K': 'Financeiro', 'L': 'Imobiliário', 'M': 'Profissionais e técnicas', 'N': 'Administrativas',
 'O': 'Administração pública', 'P': 'Educação', 'Q': 'Saúde', 'R': 'Artes e lazer', 'S': 'Outros serviços'}
r = lambda df, c=4: json.loads(df.round(c).replace({np.nan: None}).to_json(orient='records', force_ascii=False))
D = {'divisoes': DIV, 'secoes': SEC}
D['p1_grupo'] = r(pd.read_csv(RES / "q1_oficial_grupo.csv"), 1)
D['p1_risco'] = r(pd.read_csv(RES / "q1_oficial_risco_anual.csv")[['grupo', 'ano_de_vida', 'risco_baixa_voluntaria_pct']], 2)
s = pd.read_csv(RES / "q1_oficial_secao.csv"); D['p1_secao'] = r(s[s.empresas_2016_2020 >= 1000][['secao', 'grupo', 'empresas_2016_2020', 'sobrevive_1a', 'sobrevive_3a', 'sobrevive_5a', 'fechou_com_divida_5a']], 1)
D['p1_uf'] = r(pd.read_csv(RES / "q1c_uf.csv")[['uf', 'empresas', 'sobrevive_5a_pct', 'razao_fechamento', 'margem_95_razao', 'razao_baixa_vol']], 3)
m = pd.read_csv(RES / "p3_municipios.csv")
m = m[['cod_ibge', 'municipio', 'uf', 'populacao', 'pib_per_capita', 'empresas_ativas', 'bons', 'bons_pct', 'bons_por_mil_hab', 'risco_divida_medio', 'risco_fechamento_medio',
       'empresas_turmas_2016_2020', 'sobrevive_5a_pct', 'razao_fechamento', 'margem_95_razao']]
m = m.assign(populacao=m.populacao.round(0), pib_per_capita=m.pib_per_capita.round(0))
D['municipios'] = {'cols': list(m.columns), 'rows': json.loads(m.round(4).replace({np.nan: None}).to_json(orient='values', force_ascii=False))}   # colunar (menor)
f = pd.read_csv(RES / "p2b_fatores_2023.csv"); D['p2_fatores'] = r(f[['caracteristica', 'valor', 'empresas', 'fechou_pct', 'razao', 'nova_divida_pct', 'razao_nova_divida']], 3)
D['p4_faixas'] = r(pd.read_csv(RES / "p4_faixas.csv"), 4); D['p4_faixas_fechou'] = r(pd.read_csv(RES / "p4_faixas_fechou.csv"), 4)   # 4 casas: o painel arredonda uma vez só
D['p4_curva'] = r(pd.read_csv(RES / "p4_curva_aprovacao.csv"), 4); D['p4_matriz'] = r(pd.read_csv(RES / "p4_matriz_divida_fechamento.csv"), 2)
D['p4_setor'] = r(pd.read_csv(RES / "p4_comparacao_y_nova_divida_setor.csv")[['modelo', 'grupo', 'n_teste', 'auc']], 3)
D['p4_alerta'] = r(pd.read_csv(RES / "p4_alerta_discordancia.csv"), 2)
seg = pd.read_csv(RES / "p3_segmentos.csv")
D['p3_segmentos'] = r(seg[['uf', 'secao', 'porte_scr', 'empresas', 'bons', 'bons_esperados', 'bons_pct', 'bons_pct_esperado', 'pct_mei', 'credito_por_empresa', 'indice_atendimento', 'inad_scr', 'inad_br',
                           'comparavel', 'pouco_atendido', 'inadimplencia_ate_nacional']], 4)
D['p3_uf'] = r(pd.read_csv(RES / "p3_resumo_uf.csv")[['uf', 'empresas', 'bons', 'bons_pct', 'indice_atendimento', 'inad_scr']], 4)
D['c3'] = r(pd.read_csv(RES / "c3_semestres.csv")[['semestre', 'empresas', 'razao_1a', 'razao_vol_3a', 'selic_abertura', 'selic_12m_seguintes', 'epoca']], 3)
q = pd.read_csv(RES / "q1e_atividades.csv").merge(pd.read_csv(RES / "q1e_aberturas.csv")[['atividade', 'cresc_2021_vs_2019_pct']], on='atividade').merge(pd.read_csv(RES / "q1e_pandemia_turmas.csv")[['atividade', 'razao_pandemia_vs_antes']], on='atividade')
q['atividade'] = q.atividade.str[2:]; D['q1e'] = r(q, 4)   # alojamento e alimentação por atividade
D['c4_destino'] = r(pd.read_csv(RES / "c4_mei_destino.csv"), 2)
D['c4_setor'] = r(pd.read_csv(RES / "c4_mei_cresce_setor.csv"), 2); D['c4_uf'] = r(pd.read_csv(RES / "c4_mei_cresce_uf.csv"), 2)
D['pilotos'] = r(pd.read_csv(RES / "p5_pilotos.csv"), 2); D['pilotos_viab'] = r(pd.read_csv(RES / "p5_viabilidade.csv"), 1)
D['p3_sens'] = r(pd.read_csv(RES / "p3_sensibilidade_mei.csv"), 0); D['p4_bons'] = r(pd.read_csv(RES / "p4_bons_clientes.csv"), 2); D['p4_fluxo'] = r(pd.read_csv(RES / "p4_fluxo_decisao.csv"), 4)
# calculadora: tabela de pontos v2 (mesma especificação de faixas de p4_tabela.py)
from p4_tabela import NUM, VARIAVEIS
calc = {'faixas': {v: {'limites': l, 'rotulos': r} for v, (c, l, r) in NUM.items()}, 'variaveis': VARIAVEIS}
for suf, nome in [('', 'divida'), ('_fechou', 'fechamento')]:
    pts = pd.read_csv(RES / f"p4_scorecard_pontos{suf}.csv"); k = pd.read_csv(RES / f"p4_scorecard_constantes{suf}.csv").iloc[0]
    cortes = pd.read_csv(RES / f"p4_cortes_faixas{suf}.csv", float_precision='round_trip').nota.tolist()
    junta = json.load(open(RES / f"p4_scorecard_juncoes{suf}.json", encoding='utf-8'))
    calc[nome] = {'pontos': {v: dict(zip(g.faixa, g.pontos.round(4))) for v, g in pts.groupby('variavel', sort=False)}, 'juncoes': junta,
                  'cortes': cortes, 'BASE': float(k.BASE), 'PDO': float(k.PDO), 'ODDS': float(k.ODDS_BASE)}
D['calc'] = calc
D['fator_scr'] = pd.read_csv(RES / 'p4_calibragem_scr_secao_porte.csv').groupby('porte').fator_scr_sobre_nota.median().round(2).to_dict()   # mediana das seções por porte
txt = json.dumps(D, ensure_ascii=False, separators=(',', ':'))
(RAIZ / "resultados/painel_dados.json").write_text(txt, encoding='utf-8'); print(len(txt) / 1e6, 'MB')
