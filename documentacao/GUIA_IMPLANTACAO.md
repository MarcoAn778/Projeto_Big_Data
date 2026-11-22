# Concluir a implantação e a entrega

O código está preparado, mas a criação do banco exige uma conta da equipe. Este guia usa o Aiven porque a conexão PostgreSQL do projeto anterior já previa esse provedor. Nenhuma senha ou token deve ser enviado pelo chat ou publicado no GitHub.

## 1. Preparar a máquina e validar a base

Instalar R, Git e Terraform pelos distribuidores oficiais. No R:

```r
install.packages(c("DBI", "duckdb", "digest", "jsonlite", "RPostgres"))
```

Abra PowerShell na raiz do projeto e execute `Rscript codigo/executar.R validar`. Se Rscript não estiver no PATH, use o caminho da versão instalada, por exemplo:

```powershell
& 'C:\Program Files\R\R-4.6.1\bin\Rscript.exe' codigo/executar.R validar
```

O comando extrai a base publicada, verifica o SHA-256 e os totais e prepara a auditoria. Não é necessário copiar novamente os TXT para carregar essa versão. Para reproduzir o tratamento integral, use os 12 TXT em `dados_originais/` e o modo `tratamento` antes da validação.

## 2. Criar a conta e o projeto Aiven

1. Acesse [Aiven Console](https://console.aiven.io/) e crie a conta da equipe, concluindo a verificação de e-mail.
2. Identifique ou crie um projeto e anote seu nome exato.
3. Gere um token pessoal nas configurações de autenticação da conta, com prazo e permissões adequados ao projeto.
4. Não crie o serviço manualmente: o próximo passo cria o PostgreSQL por Terraform.

O plano padrão do código é `free-1-1gb`. Confirme que ele está disponível para o projeto. Se a plataforma não disponibilizar o plano gratuito, interrompa a implantação e revise a escolha; o código bloqueia planos pagos. A existência de um serviço gratuito do mesmo tipo na organização pode impedir outro.

## 3. Configurar e aplicar o Terraform

Na raiz do repositório:

```powershell
Copy-Item infraestrutura/terraform.tfvars.example infraestrutura/terraform.tfvars
.\infraestrutura\configurar_token.ps1
```

Edite apenas a cópia local `infraestrutura/terraform.tfvars`:

- substitua `project_name` pelo nome real do projeto;
- mantenha `plan = "free-1-1gb"` se disponível;
- substitua `203.0.113.10/32` pelo IP público da sua rede seguido de `/32`;
- inclua os demais IPs necessários para a equipe, se aplicável.

O IP do exemplo é reservado para documentação e não permite acesso da sua máquina. O token é solicitado em entrada oculta pelo script, sem aparecer no histórico.

Como esta pasta pode estar no OneDrive, guarde o estado Terraform fora dela. Os comandos abaixo criam o diretório privado de estado no perfil local da máquina:

```powershell
$estadoCaged = Join-Path $env:LOCALAPPDATA 'ProjetoBigData'
New-Item -ItemType Directory -Path $estadoCaged -Force | Out-Null
$arquivoEstadoCaged = (Join-Path $estadoCaged 'terraform.tfstate').Replace('\', '/')
terraform -chdir=infraestrutura init -backend-config="path=$arquivoEstadoCaged"
terraform -chdir=infraestrutura fmt -check -recursive
terraform -chdir=infraestrutura validate
terraform -chdir=infraestrutura test
terraform -chdir=infraestrutura plan
terraform -chdir=infraestrutura apply
```

Leia o plano antes de confirmar o `apply`: deve criar um serviço PostgreSQL no projeto correto, no plano gratuito, sem exclusões. Aguarde o serviço ficar disponível. Preserve o mesmo state em execuções futuras e mantenha uma cópia privada segura. O lock `.terraform.lock.hcl` deve ser versionado; `terraform.tfvars`, state e planos não devem ser publicados. Não use `terraform output -json` ou exportação do state como evidência pública.

Se um banco já tiver sido criado manualmente antes de seguir este guia, configure o nome e parâmetros correspondentes e importe-o primeiro:

```powershell
terraform -chdir=infraestrutura import aiven_pg.caged PROJETO/SERVICO
terraform -chdir=infraestrutura plan
```

Importar um recurso existente não prova que ele foi originalmente provisionado por Terraform. Registre essa distinção na entrega caso esse caminho seja utilizado.

## 4. Configurar a conexão e carregar

No painel do serviço, obtenha host, porta, banco, usuário e senha e baixe a CA. Mantenha o arquivo CA em local privado. É possível usar `segredos/ca.pem`, ignorado pelo Git; o certificado CA serve para verificar o servidor e não substitui a senha.

Na mesma janela PowerShell em que executará Rscript:

```powershell
.\codigo\configurar_conexao.ps1
Rscript codigo/executar.R carga
Rscript codigo/executar.R verificar-nuvem
```

Informe os valores do painel nos prompts. O banco geralmente é `defaultdb`, mas use o valor realmente informado pelo serviço. A senha será solicitada com entrada oculta. Se a conexão falhar, confira o IP público autorizado, a porta e a CA. Não desative a validação de certificado.

A carga usa uma transação e blocos de 20 mil linhas. Se houver erro antes do commit, as alterações da carga são revertidas. Se o schema já tiver dados, a carga para para evitar duplicação; para conferir uma carga existente, use `verificar-nuvem`. Nenhuma tabela é apagada automaticamente.

## 5. Guardar evidências e atualizar o status

Após uma execução real bem-sucedida:

1. Confirme `verificacoes/carga_nuvem.json` com status `carga_nuvem_validada` e os totais da base.
2. No Aiven, confira o serviço disponível, plano e uso de disco. Não confunda o tamanho do CSV com o tamanho do banco, índices e espaço de operação. O plano gratuito tem capacidade limitada.
3. Guarde uma evidência do `apply` concluído, com data e quantidade de recursos criados, removendo dados de acesso. Uma captura deve ocultar senha, token e URI de conexão.
4. Execute [consultas_validacao.sql](../sql/consultas_validacao.sql) para apresentar resultados por mês e a auditoria.
5. Atualize o status no README e em `documentacao/ENTREGA.md` somente depois dessas verificações. Registre a data real do provisionamento e da carga.

A evidência gerada por R contém totais, hash, confirmação de TLS e data. Ela não contém host, usuário, senha ou token. Não publique um arquivo de exemplo se passando por evidência real.

## 6. Publicar no GitHub e enviar

Revise `git status` e `git diff` antes de publicar. A pasta desta revisão é uma cópia do repositório original; os arquivos precisam ser enviados ao mesmo repositório da equipe. Com Git configurado e acesso à conta, pode-se publicar a branch da revisão e abrir uma pull request:

```powershell
git status --short
git diff --check
git add .
git commit -m "Completa infraestrutura e documentacao do marco 2"
git push -u origin codex/entrega-terraform-seguranca
```

Se a revisão já estiver commitada, basta publicar a branch. No GitHub, abra a pull request dessa branch para a branch principal e incorpore após revisar. Se preferir upload manual, copie o conteúdo do pacote para a raiz do repositório existente, preservando nomes e diretórios. Inclua `.gitignore` e o lock do Terraform. Não envie o ZIP como substituto dos arquivos de código navegáveis.

Envie na plataforma da disciplina o link do repositório atualizado, conforme o procedimento da turma. O pacote e o guia não substituem o banco provisionado com a carga.

Ao terminar, remova `AIVEN_TOKEN` e `PGPASSWORD` da sessão ou feche a janela. Preserve o serviço durante o período em que será avaliado; planos gratuitos podem ser desligados por inatividade, conforme as regras do provedor.

Fontes: [plano gratuito e limites](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier), [criação de serviço](https://aiven.io/docs/products/postgresql/get-started), [provider Terraform](https://registry.terraform.io/providers/aiven/aiven/latest/docs/resources/pg).
