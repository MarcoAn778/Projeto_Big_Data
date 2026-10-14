# Teste pequeno das regras, sem ler os TXT ou acessar o Aiven.
source("codigo/00_configuracao.R")
dbExecute(con, "CREATE TEMP TABLE bruto AS SELECT
  '202508' AS competenciamov, '1' AS regiao, '11' AS uf, '1100015' AS municipio,
  'a' AS secao, '0111301' AS subclasse, saldo AS saldomovimentacao,
  '10' AS tipomovimentacao, '1' AS sexo, '1' AS racacor, idade,
  '7' AS graudeinstrucao, '40' AS horascontratuais, salario,
  '1' AS tamestabjan, '0' AS indtrabintermitente, '0' AS indtrabparcial
  FROM (VALUES ('17','1000,25','1'), ('24','0','-1'),
    ('13','-10','1'), ('101','7,40e+08','-1'),
    (NULL,'1.234,50','1'), ('18','1.5','0')) AS v(idade,salario,saldo)")
dbExecute(con, ler_sql("sql/limpar.sql"))
dbExecute(con, ler_sql("sql/categorias.sql"))
dbExecute(con, ler_sql("sql/agregar.sql"))
x <- dbGetQuery(con, "SELECT SUM(total_registros) AS total, SUM(admissoes) AS adm,
 SUM(desligamentos) AS des, SUM(saldo_invalido) AS invalido,
 SUM(quantidade_salarios_validos) AS validos,
 CAST(SUM(soma_salarios_validos) AS DOUBLE) AS soma FROM agregado_mes")
stopifnot(x$total==6, x$adm==3, x$des==2, x$invalido==1,
  x$validos==4, x$soma==2236.25)
x <- dbGetQuery(con, "SELECT SUM(total_registros) AS n FROM agregado_mes
 WHERE faixa_etaria='Nao informado ou invalido'")
stopifnot(x$n==3)
dbDisconnect(con, shutdown=TRUE)
cat("Regras de idade, fluxo, zeros, negativos, decimais e notacao cientifica: OK.\n")
