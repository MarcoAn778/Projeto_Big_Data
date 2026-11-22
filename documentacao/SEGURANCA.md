# Gerenciamento de acessos e informações sensíveis

O repositório público contém código, dados públicos agregados, metadados e exemplos de configuração. Tokens Aiven, senha PostgreSQL, certificados locais, arquivos de configuração privados, planos e estado Terraform ficam fora do Git.

| Informação | Uso e armazenamento |
| --- | --- |
| Token pessoal Aiven | Variável de processo `AIVEN_TOKEN`, preenchida por prompt oculto; autentica apenas o Terraform |
| Senha do banco | Variável de processo `PGPASSWORD`, preenchida por prompt oculto; autentica o RPostgres |
| Host, porta, banco e usuário | Variáveis `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`; não são incluídas na evidência publicada |
| CA do serviço | Arquivo local apontado por `PGSSLROOTCERT`; permite conferir a identidade do servidor |
| Estado Terraform | Backend local em diretório privado fora do repositório e do OneDrive; acesso restrito ao responsável pela implantação |

Os scripts PowerShell incluídos solicitam os segredos com `Read-Host -AsSecureString`. O valor é passado ao processo via ambiente, sem gravar a senha no histórico de comandos ou em arquivos. Variáveis de ambiente continuam sendo informações sensíveis na memória do processo. Execute apenas em uma máquina confiável e encerre a janela ou remova as variáveis ao terminar:

```powershell
Remove-Item Env:AIVEN_TOKEN, Env:PGPASSWORD -ErrorAction SilentlyContinue
```

A conexão usa `sslmode=verify-full`, certificado CA e confirmação de TLS na sessão PostgreSQL. O filtro de rede do Terraform aceita apenas CIDRs informados pela equipe e rejeita abertura global `/0`. Quando o IP público mudar, atualize a lista e aplique novamente o plano.

O schema, tabelas e view têm privilégios de `PUBLIC` revogados. A carga inicial usa a conta fornecida pelo serviço. Para acesso futuro por aplicações, criar usuário separado e conceder somente leitura da view conforme a necessidade; não compartilhar o usuário administrativo com aplicações ou avaliadores.

O `.gitignore` exclui `.Renviron`, `.env`, `segredos/`, `*.tfvars`, `*.tfstate*`, planos e chaves. Os exemplos e o lock de versões do provider podem ser publicados. A exclusão pelo Git não protege arquivos já publicados anteriormente, arquivos enviados manualmente ou o armazenamento local.

O provider Aiven pode gravar credenciais retornadas pela API dentro do state, mesmo sem outputs de senha. `sensitive=true` mascara exibição; não criptografa o arquivo. Por isso, o guia usa state fora da pasta sincronizada e proíbe sua publicação. Para colaboração, usar backend remoto privado com criptografia, controle de acesso e bloqueio de estado. Não compartilhar logs completos de `TF_LOG`, JSON de state/plan, URI de conexão ou captura do painel com senhas visíveis.

O serviço tem `termination_protection=true` e `prevent_destroy=true`. A carga ocorre em transação, recusa tabelas já preenchidas e não executa `DROP`, `TRUNCATE` ou limpeza automática. Isso reduz risco de perda ou duplicação acidental.

Em caso de exposição: revogar o token ou trocar a senha no provedor imediatamente, atualizar o ambiente local e remover o segredo do histórico do Git. Apenas apagar o arquivo no último commit não revoga uma credencial exposta.

Referências: [autenticação do provider Aiven](https://registry.terraform.io/providers/aiven/aiven/latest/docs), [dados sensíveis no Terraform](https://developer.hashicorp.com/terraform/language/manage-sensitive-data).
