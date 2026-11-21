# Verificações desta revisão

## Entrega final · 21/11/2026

| Verificação | Resultado |
| --- | --- |
| Carga no Aiven | 1.006.405 linhas, 51.893.337 movimentações, 12 competências e 195.507.903 bytes. Hash, totais mensais, somas salariais e TLS conferidos. |
| Carga integral em PostgreSQL descartável local | 1.006.405 linhas, 51.893.337 movimentações, 12 competências e 195.398.803 bytes. Hash, totais mensais, somas salariais e TLS conferidos. |
| Consultas do painel | Cinco testes aprovados no PostgreSQL local e repetidos com sucesso no Aiven, com a conta de leitura. Cobrem conexão TLS, catálogo, filtros cruzados, saldo, turnover, média e referência salariais e participação. |
| Terraform | Formatação e validação aprovadas. Quatro testes com provider simulado passaram. No Aiven, o ajuste de rede foi aplicado e um novo plano retornou código 0. |
| Segredos | Teste do índice Git aprovado. O empacotador também verifica os arquivos de texto selecionados. |

[Carga no Aiven](../verificacoes/carga_nuvem.json) · [Carga de teste local](../verificacoes/carga_dashboard_teste_local.json) · [Conferência histórica no Aiven](../verificacoes/carga_nuvem_historica.json) · [Infraestrutura](../verificacoes/terraform_entrega.json)

Para repetir os testes do painel, configure `PG*` para o PostgreSQL carregado, defina `CAGED_TESTE_DASHBOARD=1` e execute `python -m unittest discover -s testes -p "test_indicadores_dashboard.py" -v`. Os testes do painel usam transações somente leitura. Os testes antigos de carga e rollback em `test_integracao_postgres.py` continuam restritos a um PostgreSQL descartável em loopback.

## Histórico da Fase 3

Revisão preparada em 20/10/2026 a partir do commit `1173c84` do repositório da equipe.

| Verificação executada | Resultado |
| --- | --- |
| Extração do ZIP e SHA-256 do CSV publicado | Confere com `resultados/resumo_processamento.json` |
| Validação independente de toda a base em Python/DuckDB | 1.006.405 linhas; 51.893.337 movimentações; 12 competências |
| Totais de admissões, desligamentos e saldo | 26.382.492; 25.510.845; 871.647 |
| IDs e combinações de agrupamento | Sem duplicação |
| Igualdades dos indicadores e regras das medidas salariais | Aprovadas na base publicada |
| Metadados de origem e auditoria histórica | 12 arquivos; 21 ocorrências salariais; hashes do manifesto conferidos |
| `testes/testar_regras.R` | Aprovado: idades, fluxos, salário zero/negativo, decimais e notação científica |
| Testes Python locais | 10 aprovados: base válida, hash, duplicações, saldo, auditoria incompleta, mudança após validação, ZIP indevido, configuração TLS, filtragem do pacote e bloqueio de envio sem evidência |
| Testes Python de integração com PostgreSQL local | 2 aprovados: COPY/decimais/Unicode/TLS e rejeição de segunda carga; erro antes do commit com rollback da estrutura e dos dados |
| Carga integral por Python em PostgreSQL 17.6 temporário | 1.006.405 linhas, todos os totais e a soma salarial conferidos com TLS; servidor encerrado após o teste |
| Sintaxe dos scripts R, Python e PowerShell | Aprovada |
| `terraform fmt -check -recursive` | Aprovado |
| `terraform validate` | Configuração válida |
| `terraform test` com provider simulado | 4 testes aprovados: proteção do serviço, rejeição de plano pago, rede global e CIDR inválido |

Ambiente de verificação: Windows, Python 3.12, DuckDB 1.5.6, Psycopg 3.3.6, PostgreSQL 17.6 local, R 4.6.1, Terraform 1.13.3 e provider Aiven 4.64.0. As versões Python verificadas estão em `requirements-lock.txt`; o provider está fixado no lock Terraform. Ambientes virtuais, bibliotecas e binários do teste não são redistribuídos no pacote.

A evidência de validação Python está em [validacao_base_atual.json](../verificacoes/validacao_base_atual.json), e o resultado da carga em banco local está em [carga_python_teste_local.json](../verificacoes/carga_python_teste_local.json). A auditoria salarial foi reconstruída a partir dos CSVs históricos de anomalias já versionados; não foi feita uma nova leitura integral dos TXT nesta revisão. Os scripts originais de tratamento e as regras SQL de transformação foram preservados. A conexão, validação após o tratamento e carga foram migradas para Python.

Para executar os testes locais, use `.\.venv\Scripts\python.exe -m unittest discover -s testes -p "test_*.py" -v`. Os dois testes de integração são ignorados por padrão. Sua execução exige `CAGED_TESTE_POSTGRES_LOCAL=1` e as variáveis `PG*` apontando para um banco descartável em `localhost`/`127.0.0.1`, com CA válida. Esses testes apagam o schema `caged` desse banco de teste para verificar o rollback; não devem ser usados no banco da entrega. Os comandos normais de carga não apagam tabelas.

## Limites da verificação

Não houve `terraform plan/apply` com conta real, criação de serviço Aiven ou carga em PostgreSQL remoto. Houve carga real somente no PostgreSQL temporário local com Psycopg. A equipe informou que ainda não possui conta ou banco na nuvem. Os testes Terraform usam `mock_provider` e não criam recursos. A implantação e a carga no serviço Aiven ainda precisam ser executadas antes do envio final.

A revisão está preparada localmente para publicação manual pela equipe. O arquivo `verificacoes/carga_nuvem.json` não acompanha esta preparação, pois deve ser gerado somente após uma conferência real da carga.
