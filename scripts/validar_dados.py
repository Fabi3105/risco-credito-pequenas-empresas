# -*- coding: utf-8 -*-
"""Validação da base antes de qualquer análise. Saída: resultados/validacao_dados.csv e tabelas de apoio."""
import pandas as pd
from base import conectar, salvar, DATA_BASE
con = conectar()
q = lambda s: con.execute(s).fetchone()[0]
L = []
def reg(tema, checagem, valor, tratamento=""):
    L.append({"tema": tema, "checagem": checagem, "valor": valor, "tratamento": tratamento}); print(tema, "|", checagem, "|", valor, flush=True)

reg("tamanho", "estabelecimentos", q("select count(*) from estab"))
reg("tamanho", "empresas", q("select count(*) from empresas"))
reg("tamanho", "registros Simples/MEI", q("select count(*) from simples"))
reg("tamanho", "vínculos de sócio", q("select count(*) from socios"))
# chaves (consultas pesadas no nível do estabelecimento; resultado conferido em 15/10/2026)
reg("chaves", "estabelecimentos duplicados (cnpj_basico+ordem)", q("select count(*) from (select cnpj_basico, cnpj_ordem from estab where cnpj_basico like '9%' group by 1,2 having count(*)>1)") , "amostra do dígito 9; base inteira conferida: 0")
reg("chaves", "empresas na tabela montada (uma linha por CNPJ básico)", q("select count(*) from base"))
reg("chaves", "CNPJ básico repetido na tabela montada", q("select count(*) from (select cnpj_basico from base group by 1 having count(*)>1)"), "1 caso (duas matrizes); mantido, efeito nulo")
reg("chaves", "matrizes sem registro em empresas", q("select count(*) from base where porte is null and natureza_juridica is null"))
reg("datas", "data de abertura nula", q("select count(*) from base where data_inicio is null"))
reg("datas", "abertura depois da extração", q(f"select count(*) from base where data_inicio > DATE '{DATA_BASE}'"))
reg("datas", "abertura antes de 1900", q("select count(*) from base where data_inicio < DATE '1900-01-01'"))
reg("datas", "baixada/inapta sem data da situação", q("select count(*) from base where situacao in (4,8) and data_situacao is null"))
reg("datas", "data da situação antes da abertura (baixada/inapta)", q("select count(*) from base where situacao in (4,8) and data_situacao < data_inicio"), "descartar da sobrevivência")
reg("datas", "baixada no mesmo dia da abertura", q("select count(*) from base where situacao=8 and data_situacao = data_inicio"), "manter, com duração zero")
reg("datas", "opção pelo MEI antes da abertura", q("select count(*) from base where data_opcao_mei < data_inicio"))
reg("campos", "município nulo", q("select count(*) from base where municipio_rf is null"))
reg("campos", "no exterior (UF EX)", q("select count(*) from base where uf='EX'"), "excluir")
reg("campos", "CNAE principal sem tradução", q("select count(*) from base b anti join aux_cnaes c on b.cnae_principal=c.codigo"))
reg("campos", "município sem tradução", q("select count(*) from base b anti join aux_municipios m on lpad(b.municipio_rf::varchar,4,'0')=m.codigo where b.municipio_rf is not null"))
reg("campos", "porte nulo", q("select count(*) from base where porte is null"))
reg("campos", "capital social negativo", q("select count(*) from base where capital_social < 0"))
reg("campos", "já optantes pelo MEI alguma vez", q("select count(*) from base where data_opcao_mei is not null"))
reg("cruzamento", "devedores PJ na PGFN (cnpj_basico distintos, todos os tipos de devedor)", q("select count(distinct cnpj_basico) from pgfn"))
reg("cruzamento", "empresas com dívida ativa como devedor principal", q("select count(*) from base where n_inscricoes_pgfn > 0"))
reg("cruzamento", "devedores principais PGFN sem registro no CNPJ", q("select count(*) from (select distinct cnpj_basico from pgfn where upper(tipo_devedor)='PRINCIPAL') p anti join base using (cnpj_basico)"))
reg("cruzamento", "meses no SCR.data (PJ)", q("select count(distinct data_base) from scr"))
salvar(pd.DataFrame(L), "validacao_dados.csv")

# situação e motivos (matrizes)
salvar(con.execute("""select e.situacao, e.motivo_situacao, m.descricao motivo, count(*) n
  from base e left join aux_motivos m on lpad(e.motivo_situacao::varchar,2,'0')=m.codigo
  group by all order by n desc""").df(), "val_situacao_motivo.csv")
# baixas por ano e motivo (para achar baixas em massa de ofício)
salvar(con.execute("""select year(data_situacao) ano, motivo_situacao, count(*) n from base
  where situacao=8 and data_situacao >= DATE '2010-01-01' group by all order by ano, n desc""").df(), "val_baixas_ano_motivo.csv")
