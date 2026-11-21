# Gerenciamento de acessos e informações sensíveis

O repositório público contém código, dados públicos agregados, metadados e exemplos de configuração. Tokens Aiven, senha PostgreSQL, certificados locais, arquivos de configuração privados, planos e estado Terraform ficam fora do Git.

| Informação | Uso e armazenamento |
| --- | --- |
| Token pessoal Aiven | Variável de processo `AIVEN_TOKEN`, preenchida por prompt oculto; autentica apenas o Terraform |
| Senha do banco | Variável de processo `PGPASSWORD`, preenchida por prompt oculto; autentica o Psycopg no Python |
| Host, porta, banco e usuário | Variáveis `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`; não são incluídas na evidência publicada |
| CA do serviço | Arquivo local apontado por `PGSSLROOTCERT`; permite conferir a identidade do servidor |
| Estado Terraform | Backend local em diretório privado fora do repositório e do OneDrive; acesso restrito ao responsável pela implantação |

Os scripts PowerShell incluídos solicitam os segredos com `Read-Host -AsSecureString`. O valor é passado ao processo via ambiente, sem gravar a senha no histórico de comandos ou em arquivos. Variáveis de ambiente continuam sendo informações sensíveis na memória do processo. Execute apenas em uma máquina confiável e encerre a janela ou remova as variáveis ao terminar:

```powershell
Remove-Item Env:AIVEN_TOKEN, Env:PGPASSWORD -ErrorAction SilentlyContinue
```

A conexão Python usa `sslmode=verify-full`, certificado CA e confirmação de TLS na sessão PostgreSQL. O Python não imprime erros brutos do driver, parâmetros de conexão ou traceback na execução normal. O filtro de rede do Terraform aceita apenas CIDRs informados pela equipe e rejeita abertura global `/0`. Quando o IP público mudar, atualize a lista e aplique novamente o plano.

O schema, tabelas e view têm privilégios de `PUBLIC` revogados. A carga inicial usa a conta fornecida pelo serviço. Para acesso futuro por aplicações, criar usuário separado e conceder somente leitura da view conforme a necessidade; não compartilhar o usuário administrativo com aplicações ou avaliadores.

O painel usa `caged_dashboard`, com leitura da view e transações somente leitura. Guarde o arquivo dotenv privado fora de pastas sincronizadas e indique seu caminho em `CAGED_ENV_FILE`, ou use o cofre de segredos da hospedagem. O verificador de segredos examina o índice Git e o empacotador examina os arquivos de texto selecionados para o envio. Os dois reportam caminhos de arquivos. [Permissões do painel](../sql/permissoes_dashboard.sql)

O `.gitignore` exclui `.Renviron`, `.env`, `segredos/`, `*.tfvars`, `*.tfstate*`, planos, chaves, `.venv/` e caches Python. Os exemplos e os locks de dependências podem ser publicados. A exclusão pelo Git não protege arquivos já publicados anteriormente, arquivos enviados manualmente ou o armazenamento local.

O provider Aiven pode gravar credenciais retornadas pela API dentro do state, mesmo sem outputs de senha. `sensitive=true` mascara exibição; não criptografa o arquivo. Por isso, o guia usa state fora da pasta sincronizada e proíbe sua publicação. Para colaboração, usar backend remoto privado com criptografia, controle de acesso e bloqueio de estado. Não compartilhar logs completos de `TF_LOG`, JSON de state/plan, URI de conexão ou captura do painel com senhas visíveis.

O Terraform usa `prevent_destroy=true`. A configuração `termination_protection` ativa a proteção contra exclusão no Aiven por padrão e aceita o valor real no reaproveitamento de um serviço. A carga ocorre em transação e recusa tabelas já preenchidas, evitando perda ou duplicação acidental.

Em caso de exposição: revogar o token ou trocar a senha no provedor imediatamente, atualizar o ambiente local e remover o segredo do histórico do Git. Apenas apagar o arquivo no último commit não revoga uma credencial exposta.

Referências: [autenticação do provider Aiven](https://registry.terraform.io/providers/aiven/aiven/latest/docs), [dados sensíveis no Terraform](https://developer.hashicorp.com/terraform/language/manage-sensitive-data).
