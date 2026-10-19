# -*- coding: utf-8 -*-
"""Testes das regras do estudo com casos construídos à mão. Sai com erro se algum falhar."""
import sys, duckdb, metodos as M
con = duckdb.connect()
con.execute("""CREATE TABLE base AS SELECT * FROM (VALUES
 ('a', 2062, 'RS', DATE '2015-03-01', 2, NULL::DATE, 0, NULL::DATE, 1),
 ('b', 2135, 'RS', DATE '2015-03-01', 8, DATE '2017-03-01', 1, DATE '2015-03-10', 1),
 ('c', 2062, 'SP', DATE '2016-01-01', 8, DATE '2019-01-01', 2, NULL, 3),
 ('d', 4090, 'SP', DATE '2016-08-01', 8, DATE '2016-12-01', 1, NULL, 5),
 ('e', 2062, 'EX', DATE '2016-01-01', 2, NULL, 0, NULL, 5),
 ('f', 2062, 'RS', DATE '2018-01-01', 4, DATE '2017-01-01', 63, NULL, 1),
 ('g', 2135, 'PR', DATE '2018-01-01', 4, DATE '2022-06-01', 63, DATE '2018-12-01', 1)
) t(id, natureza_juridica, uf, data_inicio, situacao, data_situacao, motivo_situacao, data_opcao_mei, porte)""")
ok = True
def teste(nome, sql, esperado):
    global ok
    r = con.execute(sql).fetchall()
    r = [x[0] for x in r]
    passou = r == esperado; ok &= passou
    print(("ok   " if passou else "FALHA"), nome, r if not passou else "")
teste("universo exclui candidato, exterior e data incoerente", f"select id from base where {M.UNIVERSO} order by id", ['a', 'b', 'c', 'g'])
teste("fechamento ignora incorporação", f"select id from base where {M.FECHOU} and {M.UNIVERSO} order by id", ['b', 'g'])
teste("baixa voluntária", f"select id from base where {M.BAIXA_VOLUNTARIA} order by id", ['b', 'd'])
teste("grupo MEI só se optou em até 180 dias", f"select {M.GRUPO} from base where id in ('b','g') order by id", ['MEI', 'ME'])
teste("duração até a baixa (2 anos)", f"select round({M.DURACAO}, 2) from base where id='b'", [2.0])
teste("duração censurada na extração", f"select round({M.DURACAO}, 1) from base where id='a'", [11.6])
teste("formato brasileiro", "select 1", [1]) if M.br(1234567.891, 2) == "1.234.567,89" else teste("formato brasileiro", "select 0", [1])
con.execute("ALTER TABLE base ADD COLUMN n_inscricoes_pgfn INT DEFAULT 0; ALTER TABLE base ADD COLUMN cnae_principal VARCHAR DEFAULT '4711302'")
con.execute("UPDATE base SET n_inscricoes_pgfn = 2 WHERE id = 'g'; UPDATE base SET cnae_principal = '4110700' WHERE id = 'c'")
teste("fechamento com dívida ativa", f"select id from base where {M.FECHOU_COM_DIVIDA} order by id", ['g'])
teste("incorporação é encerramento planejado", f"select id from base where {M.PLANEJADO}", ['c'])
print("0 falha(s)" if ok else "HÁ FALHAS"); sys.exit(0 if ok else 1)
