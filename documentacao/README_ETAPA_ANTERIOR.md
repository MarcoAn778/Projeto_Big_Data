# Projeto_Big_Data

## Equipe: 
### João Victor Rocha Massena, Luísa Garrido Matos e Marco Antônio Duarte Oliveira

# Dinâmica de Emprego Formal e Turnover Setorial

Projeto de preparação e armazenamento dos dados do Novo CAGED, com recorte de agosto de 2025 a julho de 2026.

## Organização

- `codigo/`: scripts em R para tratamento, finalização e carga no banco.
- `sql/`: regras de limpeza, agregação e estrutura do PostgreSQL.
- `dados/`: identificação dos arquivos de origem.
- `referencias/`: dicionários das categorias.
- `resultados/`: base tratada compactada e resumo do processamento.
- `verificacoes/`: registros históricos de qualidade dos dados.
- `testes/`: teste das regras de tratamento.

## Execução

Dependências: `DBI`, `duckdb`, `digest`, `jsonlite` e `RPostgres`.

Com a pasta do projeto definida como diretório de trabalho, coloque os 12 arquivos exemplo: `CAGEDMOV202508.txt` a `CAGEDMOV202607.txt` contidas na base de dados disponibilizadas.

Execute, na mesma sessão do R:

1. `codigo/00_configuracao.R`
2. `codigo/01_tratar.R`
3. `codigo/02_finalizar.R`

Para conexão e carga no PostgreSQL/Aiven, configure as variáveis locais de conexão e execute `03_conectar.R` e `04_carregar.R`. Ao finalizar, execute `05_encerrar.R`.

Para utilizar diretamente a base disponibilizada, extraia `resultados/base_tratada.zip` na própria pasta `resultados/`.

## Resultado

- 12 competências.
- 51.893.337 movimentações representadas.
- 1.006.405 linhas agregadas.
- 26.382.492 admissões e 25.510.845 desligamentos.
- Saldo do recorte MOV: 871.647.

O tratamento parte dos TXT originais, sem depender de uma base tratada anterior. A validação da conexão real com o Aiven permanece pendente. Credenciais não acompanham o repositório.

Fonte: Ministério do Trabalho e Emprego — PDET / Novo CAGED.
