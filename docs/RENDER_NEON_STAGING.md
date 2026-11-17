# Implantação de testes — Render Free + Neon Free

## Escopo

Ambiente de **testes com dados fictícios**, sem imagens reais, sem documentos clínicos e sem IA habilitada. É proibido inserir dados pessoais ou de pacientes reais. O Render Free pode suspender após inatividade; a primeira requisição pode demorar.

**Projeto Render existente:** `feridasdotcom-staging` (Free)  
**URL prevista:** https://feridasdotcom-staging.onrender.com/app/  
**Painel:** https://dashboard.render.com/web/srv-dbu9emp5efls739m5sbg  
**GitHub:** `xmizutsuki/feridasdotcom`, branch `feat/clinical-core-mvp`  
**Neon:** projeto PostgreSQL criado na conta conectada (gerenciar conexão exclusivamente em painel seguro).

### Passo obrigatório no painel (ainda não concluído)

O recurso de conexão automático entre contas foi bloqueado pelas verificações de segurança, então **não copiar senhas ou URLs privadas nesta conversa**. No Render abra o serviço → **Environment** e adicione:

| Chave | Valor |
|---|---|
| `DATABASE_URL` | String de conexão PostgreSQL do Neon, obtida no painel Neon em **Connect**, com `sslmode=require` e credenciais privadas |
| `FERIDAS_PASSWORD_HASH` | Saída da geração local com `python -m app.security` |
| `FERIDAS_SESSION_SECRET` | Segredo aleatório gerado com `python -m app.security` |
| `FERIDAS_IMAGE_KEY` | Chave Fernet aleatória gerada com `python -m app.security` (necessária para inicialização, ainda que uploads estejam bloqueados) |

Para gerar as três últimas variáveis localmente, execute:

```bash
pip install -r requirements.txt
python -m app.security
```

O comando pede uma senha de entrada (mínimo 12 caracteres) e imprime o hash e as chaves. Anote a senha em um gerenciador; **não** salve a senha em GitHub, logs, issues ou arquivos do projeto. Não compartilhe a string Neon por chat.

### Variáveis públicas de configuração já fornecidas ao Render

```ini
FERIDAS_REQUIRE_POSTGRES=true
FERIDAS_DISABLE_MEDIA_UPLOADS=true
FERIDAS_COOKIE_SECURE=true
FERIDAS_REMOTE_IMAGE_ANALYSIS=false
FERIDAS_EXPERIMENTAL_REASONING=false
FERIDAS_SEMANTIC_AUDIT=false
PYTHON_VERSION=3.12.8
```

Essas variáveis devem permanecer assim no ambiente de testes.

### Reimplantar

Com os quatro segredos preenchidos e salvos no Render, selecione **Manual Deploy → Deploy latest commit** para a branch `feat/clinical-core-mvp`. A implantação inicial pode falhar até receber os segredos; isso é esperado e **não** deve ser contornado deixando autenticação desligada.

### Verificar

1. Abra `https://feridasdotcom-staging.onrender.com/health` — deve responder `{"status":"ok","clinical_validation":false}`.
2. Abra `https://feridasdotcom-staging.onrender.com/app/` e entre com a senha de teste definida localmente.
3. Cadastre **somente** um caso fictício, crie uma lesão, registre anamnese, revise achados e finalize uma avaliação.
4. Reinicie o serviço e confirme que os registros de teste permanecem no Neon.
5. Verifique que POST de foto e PDF retorna HTTP 503 e que os módulos de IA continuam desligados.

### Limitações de segurança

- Backend possui autenticação **de único proprietário**, ainda não adequada a serviço clínico multiusuário.
- Banco de dados estruturado tem dados em texto legível para quem possui acesso administrativo ao banco; **não usar dados reais**.
- `Base.metadata.create_all` é provisório; ainda não há migrations revisionadas nem restauração de backups validada.
- Fotos/PDFs gravados no disco efêmero do Render se perderiam em reinicializações. Uploads estão bloqueados por padrão.
- HTTPS e cookie Secure são obrigatórios em hospedagem.
- A versão de testes não tem validação clínica, autorização de tratamento nem integração ativa de IA.
- Evite auto deploy até testar alterações na branch. O serviço foi criado com autoDeploy desabilitado.

Em etapa futura será necessário criar armazenamento durável privado, governança de segredos, migrações e controle de acesso institucional.
