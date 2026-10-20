# Verificações desta revisão

Revisão preparada em 20/10/2026 a partir do commit `1173c84` do repositório da equipe.

| Verificação executada | Resultado |
| --- | --- |
| Extração do ZIP e SHA-256 do CSV publicado | Confere com `resultados/resumo_processamento.json` |
| Validação de toda a base agregada em R/DuckDB | 1.006.405 linhas; 51.893.337 movimentações; 12 competências |
| Totais de admissões, desligamentos e saldo | 26.382.492; 25.510.845; 871.647 |
| IDs e combinações de agrupamento | Sem duplicação |
| Igualdades dos indicadores e regras das medidas salariais | Aprovadas na base publicada |
| Metadados de origem e auditoria histórica | 12 arquivos; 21 ocorrências salariais; hashes do manifesto conferidos |
| `testes/testar_regras.R` | Aprovado: idades, fluxos, salário zero/negativo, decimais e notação científica |
| `testes/testar_integridade.R` | CSV adulterado bloqueado antes do acesso ao banco |
| Sintaxe dos scripts R e dos dois scripts PowerShell | Aprovada |
| `terraform fmt -check -recursive` | Aprovado |
| `terraform validate` | Configuração válida |
| `terraform test` com provider simulado | 4 testes aprovados: proteção do serviço, rejeição de plano pago, rede global e CIDR inválido |

Ambiente de verificação: Windows, R 4.6.1, Terraform 1.13.3 e provider Aiven 4.64.0 fixado pelo lock. Os pacotes R de processamento foram disponibilizados pela biblioteca local de validação; eles não são redistribuídos no pacote. A instalação das dependências no ambiente de reprodução está descrita no README.

A evidência local está em [validacao_base_atual.json](../verificacoes/validacao_base_atual.json). A auditoria salarial foi reconstruída a partir dos CSVs históricos de anomalias já versionados; não foi feita uma nova leitura integral dos TXT nesta revisão. Os scripts originais de tratamento e as regras SQL de transformação foram preservados.

## Limites da verificação

Não houve `terraform plan/apply` com conta real, criação de serviço Aiven, conexão com PostgreSQL remoto, teste de importação via RPostgres nem execução real da carga. A equipe informou que ainda não possui conta ou banco na nuvem. Os testes Terraform usam `mock_provider` e não criam recursos. O fluxo PostgreSQL deverá ser validado com o serviço real antes do envio final.

O repositório remoto ainda precisa receber esta revisão. O arquivo `verificacoes/carga_nuvem.json` não acompanha esta preparação, pois deve ser gerado somente após uma conferência real da carga.
