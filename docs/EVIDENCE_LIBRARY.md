# Biblioteca científica controlada (RAG v0: recuperação lexical local)

## Objetivo
Iniciar a camada científica sem criar citações falsas ou transformar correspondência textual em recomendação clínica.

## Implementado
- Catálogo fechado de publicações oficiais: página geral IWGDF 2023, guideline de cicatrização IWGDF 2023 e biblioteca SOBEST. O catálogo identifica **páginas de editoras** e não afirma ter verificado cada trecho.
- Registro de trechos **curtos**, informado e atestado pelo operador: ID da fonte, seção/página/localização exata, idioma, palavras-chave, anotações de aplicabilidade, identificador do responsável e hash SHA-256.
- Consulta local por termos com normalização de acentos, remoção de termos comuns e ranking transparente por quantidade de termos compartilhados. **Não há embeddings**, banco vetorial nem LLM nesta etapa.
- Pesquisa opcional de temas explícitos da anamnese da **avaliação atual**: diabetes informado, preocupação com perfusão, relato de alívio de pressão e compressão. Temas são atalhos de busca, **não diagnóstico**.
- Fontes pesquisadas sempre exibem link para o documento da editora e localização registrada do trecho.
- As informações são apresentadas como **material para conferência manual**, e não afirmações clínicas validadas para o caso.
- Testes de regras de catálogo, autenticação, confirmações, palavras-chave, duplicatas e ausência de recomendações.

## Endpoints protegidos
- `GET /evidence/catalog` — metadados de páginas oficiais.
- `GET /evidence/passages` — trechos atestados.
- `POST /evidence/passages` — inclusão append-only de trecho com localização e confirmação explícita.
- `GET /evidence/search?q=...` — pesquisa lexical dos trechos cadastrados.
- `GET /evidence/assessments/{assessment_id}/candidates` — tópicos de busca derivados somente de campos explícitos da anamnese atual, sem inferir etiologia.

## O que NÃO foi feito
- Não houve cópia nem indexação automática dos PDFs oficiais; respeitar direitos autorais e permissões de uso.
- Não há validação independente de que o trecho atestado foi transcrito corretamente ou permanece vigente.
- `verification_status=publisher_page_identified` atesta apenas identificação da página de publicação; não substancia recomendações.
- O hash impede alterações silenciosas de *uma representação textual*, mas sozinho não prova que o trecho seja autêntico ou completo.
- **Não existe motor capaz de diagnosticar, selecionar coberturas, sugerir antimicrobianos ou decidir contraindicações.**
- Não existe avaliação formal de qualidade de evidência ou aplicabilidade ao paciente.
- Recuperação por palavras não equivale a busca semântica e pode perder documentos relevantes.

## Segurança do raciocínio
Os resultados retornam `reasoning_executed=false`, `recommendations_enabled=false` e `clinical_applicability_validated=false`. A funcionalidade preexistente `/assessments/{id}/evidence-readiness` **continua bloqueada para recomendações**.

### Próximo marco antes de qualquer hipótese clínica
1. Receber/licenciar corpus permitido; extrair conteúdo mantendo páginas e referências.
2. Implementar validação independente de citações e controle de versões.
3. Criar conjunto de casos sintéticos com respostas de especialistas para avaliar recuperação, interpretação e segurança.
4. Só então oferecer hipóteses diferenciais com evidência favorável/contrária, informações ausentes e exigência de revisão profissional.
5. Avaliar aspectos legais, LGPD e riscos regulatórios antes de dados reais.

## Fonte das páginas do catálogo
- https://iwgdfguidelines.org/guidelines-2023/
- https://iwgdfguidelines.org/wound-healing-2023/
- https://sobest.com.br/biblioteca/

Documentação de arquitetura existente: `docs/SECOND_OPINION_CONTEXT.md`.

**Software experimental apenas para dados sintéticos; não usar no cuidado de pacientes.**
