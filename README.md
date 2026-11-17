# feridasdotcom

Protótipo de prontuário longitudinal de lesões e suporte à segunda opinião clínica.

> **AVISO:** software experimental, **não validado clinicamente**. Não usar para orientar decisões clínicas, publicar na internet ou armazenar dados reais de pacientes. A API inicial **não tem autenticação** e utiliza SQLite local de desenvolvimento.

## Marco 1 — núcleo de registros e revisão humana

Implementado:
- Pacientes com identificador pseudonimizado, lesões e avaliações.
- Achados semiológicos com proveniência e sustentação (alta, limitada ou não avaliável).
- Revisão humana por campo: confirmar, corrigir ou rejeitar.
- Finalização somente após revisão e bloqueio de alterações posteriores por esses endpoints.
- Auditoria básica de eventos e tendência de área com cálculos determinísticos.
- Testes de integração com informações fictícias.

Interface web responsiva incluída: painel com totais, pacientes, lesões, avaliações, revisão de achados, finalização e gráfico de evolução. **Ainda não há processamento de imagem ou IA.** O núcleo foi estruturado para recebê-los nas etapas seguintes.

### Executar localmente

Requer Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
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

Não incluir `.env`, imagens reais ou banco de pacientes no Git. Antes de uso real: autenticação, perfis de acesso, criptografia, tratamento LGPD, migrações, backups, adendos e validação clínica.

### Estado desta entrega

Interface e API integradas no código, com testes de integração escritos. A execução dos testes automatizados ainda precisa ser confirmada em ambiente Python ou CI. A interface depende de um backend rodando localmente e **não** implementa autenticação, IA, armazenamento de fotografias ou sincronização offline. Não hospedar esta versão publicamente.
