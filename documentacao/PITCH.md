# Roteiro de apresentação · 10 minutos

| Tempo | Quem apresenta | Conteúdo e ação |
| --- | --- | --- |
| 0:00–1:10 | Integrante 1 | Abra com a pergunta “Quem entra, quem sai e com qual salário no emprego formal brasileiro?”. Explique como gênero e raça/cor se cruzam nas ODS 5 e 18. Apresente o recorte MOV de agosto de 2025 a julho de 2026. |
| 1:10–2:40 | Integrante 1 | Mostre o diagrama. Os TXT passam por R/DuckDB e agregação mensal. Python valida e carrega PostgreSQL no Aiven. O Streamlit envia SQL ao banco por TLS. Mostre `infraestrutura/main.tf`, o recurso no state e o resultado do plano previamente conferido. O serviço original foi criado no painel e depois importado para o Terraform. |
| 2:40–4:00 | Integrante 2 | Mostre MOV como critério de inclusão e explique a exclusão de FOR, EXC e revisões. Descreva a conferência de cabeçalhos, hashes, competências e contagens. Explique o tratamento de idades e raça/cor ausentes e por que o salário inválido sai da média com a movimentação preservada. A base representa 51.893.337 eventos em 1.006.405 linhas agregadas. |
| 4:00–7:50 | Integrante 2 | Demonstre os quatro indicadores na sequência abaixo. Use **Atualizar dados** com o Aiven disponível, mostre o horário da consulta e altere um filtro em tempo real. |
| 7:50–9:15 | Integrante 3 | Discuta os resultados do README. Compare a participação de mulheres em dois setores e a média salarial de mulheres pretas com outro grupo da mesma tela. Lembre que a base cobre movimentos formais, que existe raça/cor sem identificação e que a média é descritiva. Explique por que a razão de fluxos prescinde de estoque e por que ela difere da taxa convencional. |
| 9:15–10:00 | Integrante 3 | Feche com as decisões técnicas. Destaque o ETL mensal em DuckDB, a redução do volume por agregação, a validação e a carga transacional em Python, a média salarial recomposta e a manutenção do Aiven. Aponte o README, o comando local e os arquivos de reprodução. |

## Sequência da demonstração

1. **Saldo mensal.** Comece com o Brasil. Selecione Nordeste e Bahia, depois Mulher e as categorias Preta e Parda. Mostre a série mensal e abra a tabela com admissões e desligamentos.
2. **Turnover setorial.** Fixe uma competência e uma seção CNAE. Mostre o significado da referência 1 e a regra para setores ou estratos sem admissões.
3. **Salário de admissão.** Limpe o filtro de sexo. Compare médias e a coluna com o percentual da maior média daquele recorte. Abra a tabela para mostrar o número de salários válidos.
4. **Participação.** Limpe os filtros demográficos para a comparação nacional. Alterne entre admissões e desligamentos. Mostre como raça/cor afeta a série de mulheres e como sexo afeta a série de pessoas negras.

Antes de apresentar, confirme o plano e a carga com os acessos da equipe e abra o painel. Use apenas saídas que ocultem parâmetros privados. Se o serviço ficar indisponível durante a apresentação, use as capturas do README e identifique a consulta como previamente registrada.
