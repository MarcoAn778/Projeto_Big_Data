# Atendimento aos entregáveis do documento

O PDF recebido começa na seção 4, como continuação da AI 03. Este mapa cobre o conteúdo recebido e a lista final de entrega; não presume instruções ausentes das páginas anteriores.

| Exigência | Artefato ou evidência | Situação |
| --- | --- | --- |
| Código de tratamento | `codigo/00` a `02`, `sql/limpar.sql`, `categorias.sql`, `agregar.sql` | Já existente; mantido |
| Base de dados tratada | `resultados/base_tratada.zip` e resumo com SHA-256 | Disponível e validada localmente |
| Banco na nuvem com carga | `codigo/03`, `04`, `07`, `sql/estrutura.sql`; futura `verificacoes/carga_nuvem.json` | Pendente de conta, provisionamento e carga reais |
| 4. Infraestrutura em Terraform | `infraestrutura/*.tf`, exemplo, lock e testes | Código validado; apply real pendente |
| 5. Segurança das informações | `.gitignore`, prompts ocultos, TLS, `documentacao/SEGURANCA.md` | Implementado no código e documentado |
| 6. Repositório organizado | Diretórios de código, SQL, infraestrutura, dados e documentação | Publicado na branch de revisão; incorporação à principal pendente |
| 7. README atualizado | Fonte/recorte, tratamento, decisões, modelagem, infraestrutura e execução | Atualizado |
| 8. Justificativa tecnológica | README e `documentacao/MODELAGEM.md` | Documentada |
| 9. Resultado esperado | TXT → R/DuckDB → agregados → PostgreSQL/Aiven → evidências | Etapa na nuvem ainda precisa ser executada |

Antes do envio final, concluir a implantação pelo [guia](GUIA_IMPLANTACAO.md), incorporar a revisão à branch principal no GitHub e recuperar a data/URL de download dos arquivos originais quando possível. Não afirmar que o banco foi criado ou carregado com base apenas em testes locais.

## Evidências para a apresentação

- Mostrar os `.tf` e o resultado real de `terraform apply`, sem informações de acesso.
- Mostrar o serviço disponível e a consulta SQL com 1.006.405 linhas agregadas, 51.893.337 movimentações e 12 competências.
- Mostrar o diagrama e explicar a granularidade escolhida e a média salarial ponderada.
- Mostrar a estratégia de credenciais sem abrir valores de senha/token.
- Mostrar o link do repositório atualizado, README e a evidência real da carga.
