# feridasdotcom

Protótipo de prontuário longitudinal de lesões e suporte à segunda opinião clínica.

> **AVISO:** software experimental, **não validado clinicamente**. Não usar para orientar decisões clínicas, publicar na internet ou armazenar dados reais de pacientes. A API agora exige senha de proprietário único, sessão com cookie HttpOnly e token CSRF. O armazenamento local de fotografias é criptografado, mas **a versão ainda não tem validação clínica ou certificação de segurança**.

## Marco 1 — núcleo de registros e revisão humana

Implementado:
- Pacientes com identificador pseudonimizado, lesões e avaliações.
- Achados semiológicos com proveniência e sustentação (alta, limitada ou não avaliável).
- Revisão humana por campo: confirmar, corrigir ou rejeitar.
- Acesso por senha local de proprietário único; sessões HttpOnly / SameSite Strict e verificação CSRF.
- Upload JPEG/PNG/WebP limitado a 8 MB, validação de imagem, remoção de EXIF e criptografia com Fernet em disco.
- Listagem/visualização de fotografias vinculadas à avaliação somente após autenticação.
- Finalização somente após revisão e bloqueio de alterações posteriores por esses endpoints.
- Auditoria básica de eventos e tendência de área com cálculos determinísticos.
- Testes de integração com informações fictícias.

Interface web responsiva incluída: painel com totais, pacientes, lesões, avaliações, revisão de achados, finalização e gráfico de evolução. **Análise visual experimental opcional adicionada.** Ela gera propostas semiológicas com revisão humana, sem diagnóstico ou condutas. Está desligada por padrão; ver `docs/VISION.md`. O processamento de imagens continua incluindo validação de formato/dimensões e remoção de EXIF. O núcleo foi estruturado para recebê-los nas etapas seguintes.

### Executar localmente

Requer Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.security  # insira a senha; copie as três variáveis geradas para .env
set -a; source .env; set +a  # Linux/macOS; no PowerShell, defina as variáveis no ambiente
uvicorn app.main:app --reload --host 127.0.0.1
```

Aplicativo web: http://127.0.0.1:8000/app/\n\nAPI interativa: http://127.0.0.1:8000/docs

### Testar

```bash
pytest -q
```

### Organização

- `app/models.py`: entidades e rastreabilidade.
- `app/schemas.py`: contratos de entrada/saída.
- `web/`: interface responsiva servida pelo backend (HTML, CSS e JavaScript).\n- `app/main.py`: endpoints do núcleo clínico e interface web.
- `tests/`: testes automatizados com dados fictícios.
- `docs/ARCHITECTURE.md`: status, limites e próximos passos.

### Segurança

Não incluir `.env`, imagens reais ou banco de pacientes no Git. Antes de uso real: revisão independente de segurança, criptografia do banco e backups, controles de acesso por profissional, consentimentos/bases legais, LGPD, migrações, adendos, recuperação de desastres e validação clínica. **Não publicar o servidor**; mantenha `127.0.0.1` e dados sintéticos. Cookies `Secure` dependem de HTTPS (`FERIDAS_COOKIE_SECURE=true`).

### Estado desta entrega

Interface e API integradas no código, com testes de integração escritos. A execução dos testes automatizados ainda precisa ser confirmada em ambiente Python ou CI. A interface depende de um backend rodando localmente e **não** implementa autenticação, IA, armazenamento de fotografias ou sincronização offline. Não hospedar esta versão publicamente.

## Fotografia e limites de segurança

O arquivo original não é preservado: a foto é normalizada para JPEG e regravada sem EXIF, cifrada no diretório configurado em `FERIDAS_STORAGE_DIR`. A chave **não pode** ser compartilhada no Git ou perdida: sem ela as imagens não serão recuperadas. Os campos do banco (textos clínicos) ainda **não** têm criptografia própria. Não usar pacientes reais. O protótipo não inclui rotação de chaves, backups, isolamento multiusuário ou trilha de auditoria inviolável.

## Testes

Os testes usam credenciais sintéticas em `tests/conftest.py`; não são credenciais do aplicativo. `pytest -q` deve rodar após instalar dependências. O GitHub Actions executa testes a cada push e PR.

## Nova etapa — rascunho visual multimodal

Com uma fotografia de **teste** vinculada a uma avaliação em rascunho, a interface apresenta o recurso de análise visual. Por segurança, permanece desligado por padrão; para testá-lo com imagens sintéticas, configure explicitamente `FERIDAS_REMOTE_IMAGE_ANALYSIS=true`, `FERIDAS_VISION_MODEL` e `FERIDAS_OPENAI_API_KEY` no ambiente. O operador confirma cada envio. **Nunca envie fotos de pacientes reais neste protótipo.**

O modelo apenas sugere características visuais por campo. A API valida o esquema, registra limitações e deixa tudo `pending` até revisão humana. As regras clínicas e diagnósticas, a validação científica e o histórico de planos terapêuticos ainda não foram implementados. Consulte `docs/VISION.md`.

## Qualidade das fotografias e comparações longitudinais

A verificação técnica por foto agora oferece alertas experimentais de iluminação, resolução, contraste e detalhe aparente. O aplicativo apresenta recomendações de recaptura, mas não bloqueia a documentação. Na área **Evolução**, há uma comparação exploratória de metadados entre duas fotografias da mesma lesão em datas diferentes. **Não** há alinhamento espacial validado nem cálculo automático de área. Veja `docs/IMAGE_QUALITY.md`.

Endpoints locais protegidos: `GET /photos/{photo_id}/quality` e `GET /photos/{current_id}/compare/{previous_id}`. Testes em `tests/test_quality.py`; é necessário conferir CI antes de mesclar.

## Anamnese estruturada e intervenções (novo marco)

Na tela de avaliação, a seção **Anamnese e exame clínico** permite registrar dor, tempo de evolução, sintomas relatados, possível alteração de perfusão, fatores relacionados a pressão/compressão, comorbidades, alergias, medicamentos e contexto. Campos vazios significam **não registrado**, nunca resposta negativa. Cada nova revisão gera um registro adicional. O histórico anterior somente é exibido se existir uma avaliação finalizada da mesma lesão; seus dados não são herdados como achados confirmados.

A seção **Condutas e intervenções** diferencia ações planejadas, realizadas e não realizadas. Na aba **Evolução**, uma linha do tempo exibe dados clínicos declarados e eventos terapêuticos, sem inferir relação causal ou recomendar tratamentos.

Há avisos determinísticos **experimentais** sobre determinados relatos de piora, febre e perfusão, mas não foram validados para identificar ou excluir emergências. **A ausência de aviso não significa segurança clínica.**

API: `app/clinical_routes.py`; contratos: `app/clinical_schemas.py`; regras: `app/clinical_rules.py`; tela: `web/clinical.js`; testes: `tests/test_clinical.py`. Documentação: `docs/CLINICAL_HISTORY.md`.

Esta é uma implementação de protótipo com dados sintéticos. Persistem lacunas importantes: migrações, criptografia de campos do banco, autenticação por profissional, assinatura/adendos, avaliação clínica de regras e validação da aplicação.

## Base para segunda opinião (nova etapa)

Na tela de cada avaliação, a seção **Base para segunda opinião** reúne apenas achados semiológicos revisados pelo profissional, a última revisão de anamnese da **mesma avaliação** e registros terapêuticos com o estado planejado/realizado preservado. O sistema destaca lacunas, campos não avaliáveis, achados pendentes e rejeitados, além de fornecer a origem e o identificador das informações.

Rotas autenticadas: `GET /assessments/{id}/clinical-context` e `GET /assessments/{id}/evidence-readiness`.

**Ainda não existe motor de segunda opinião diagnóstica nem RAG científico funcional.** A camada de evidências é uma interface estrutural sem fontes verificadas: não apresenta hipóteses, referências inventadas ou recomendações clínicas. Nenhum processamento externo é acionado ao consultar esse painel.

Detalhes: `docs/SECOND_OPINION_CONTEXT.md`, `app/second_opinion.py`, `app/second_opinion_schemas.py` e `tests/test_second_opinion.py`.

## Biblioteca científica controlada (novo)

Foi acrescentado um catálogo de páginas oficiais (IWGDF 2023 e biblioteca SOBEST), registro de trechos curtos com localização conferida pelo operador e busca lexical local. Também é possível localizar **candidatos de pesquisa** com base em informações explícitas registradas na anamnese atual, sem inferir diagnósticos. A interface dessa biblioteca está dentro da avaliação.

Apenas identificar uma página de diretriz **não valida seu conteúdo**. Um trecho cadastrado com confirmação do operador **não equivale a verificação independente** nem comprova que se aplica ao caso. Ainda não há RAG com geração de hipóteses ou recomendações clínicas; a emissão de condutas continua desabilitada.

Ver `docs/EVIDENCE_LIBRARY.md` e testes `tests/test_evidence.py` e `tests/test_evidence_context.py`. **Não use dados reais de pacientes.**

## PDF científico local e auditoria de hipóteses (novo marco)

O aplicativo agora permite **enviar PDFs científicos autorizados ou fictícios** (até 6 MB e 100 páginas), guardá-los criptografados e conferir se uma citação curta consta do texto extraído de determinada página. A confirmação registra o identificador do arquivo e hashes do documento, do trecho e da página. Essa conferência de correspondência textual **não** prova autenticidade, qualidade da diretriz ou aplicabilidade clínica.

Foi adicionada uma tela para o profissional preencher hipóteses **manualmente** e testar se os vínculos com observações revisadas e citações registradas são válidos. O resultado é uma **auditoria estrutural**, não diagnóstico, recomendação, comprovação científica ou autorização terapêutica.

Dependências: `pip install -r requirements.txt`; testes de PDFs sintéticos exigem `pip install -r requirements-dev.txt`. Arquivos principais: `app/pdf_evidence.py`, `app/document_routes.py`, `app/differential_routes.py`, `web/document_evidence.js`, `web/differential.js`, `tests/test_document_ingestion.py`. Veja `docs/PDF_CITATIONS_AND_DIFFERENTIAL.md`.

**Importante:** não inserir documentos com dados de pacientes, não expor o servidor e não usar esta versão para decisões de cuidado.

## Raciocínio diferencial experimental (somente cenários sintéticos)

O protótipo agora contém um adaptador opcional para geração de **hipóteses diferenciais preliminares** com IA, estruturadas em argumentos favoráveis e contrários, IDs de evidências, informações faltantes e contraindicações a investigar. Não fornece indicações de tratamento. O módulo fica **desligado por padrão**, requer confirmação do uso de dados inteiramente fictícios e autorização explícita de processamento externo.

A resposta do modelo passa por auditoria de IDs de achados humanos revisados e citações literais reconferidas nos PDFs. **Isso verifica vínculos, não a correção clínica dos argumentos**: as hipóteses permanecem não validadas e não podem orientar cuidados reais. Avisos urgentes detectados nas regras existentes bloqueiam a execução, mas a ausência desses avisos não exclui emergências.

Configuração opcional em `.env.example`: `FERIDAS_EXPERIMENTAL_REASONING=true`, `FERIDAS_REASONING_MODEL` e `FERIDAS_OPENAI_API_KEY`. Use somente dados sintéticos. Ver `docs/EXPERIMENTAL_REASONING.md`.

## Auditoria semântica independente e testes sintéticos (novo marco)

O motor de IA experimental agora possui **um segundo modelo configurável** para revisar a adequação semântica de cada citação usada em hipóteses. A análise verifica vínculos entre afirmações, trechos, população-alvo, contraindicações e informações faltantes. O sistema bloqueia e oculta hipóteses se a auditoria não estiver habilitada, falhar ou identificar inconsistências. Mesmo quando um segundo modelo considera os vínculos adequados, o parecer continua **não validado clinicamente**.

Configurações adicionais: `FERIDAS_SEMANTIC_AUDIT=false` (padrão) e `FERIDAS_REVIEW_MODEL` (deve ser diferente do modelo gerador). **Nenhum dado de paciente real deve ser enviado.**

O conjunto `benchmarks/semantic_contract_cases.json` tem 12 desafios artificiais para testar contratos e bloqueios; **não é uma avaliação de precisão de modelo, não foi adjudicado por especialistas e não valida segurança clínica**. O protocolo para futura avaliação cega está em `benchmarks/ADJUDICATION_PROTOCOL.md`. Leia `docs/SEMANTIC_AUDIT.md` para limites e próximas etapas.
