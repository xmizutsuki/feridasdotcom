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
