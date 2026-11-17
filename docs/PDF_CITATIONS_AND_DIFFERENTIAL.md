# PDFs científicos e auditoria estrutural de hipóteses — marco experimental

## Implementado
- Envio autenticado de um **arquivo PDF local autorizado**, vinculado a uma fonte do catálogo fechado e a um rótulo de edição.
- Limites de proteção do parser: até 6 MB, 100 páginas, validação do cabeçalho PDF, rejeição de PDFs criptografados e de páginas cujo texto extraído excede o limite. PDFs escaneados sem texto extraível **não são processados por OCR**.
- Armazenamento local **criptografado** do PDF por meio da infraestrutura de mídia já existente; o documento completo não é enviado a modelos de IA.
- Conferência de citação **literal** mediante: ID do documento, página física (contada desde 1), texto do trecho e identidade declarada do verificador. O código extrai o texto da página e verifica correspondência estrita após normalizar espaços e maiúsculas/minúsculas.
- Hash SHA-256 dos bytes do PDF, do trecho e do texto da página verificada, com trilha de auditoria. PDF original enviado não é modificado pelo verificador.
- Interface para upload de PDFs e registro da citação literal.
- Auditoria de um rascunho de hipótese **escrito pelo próprio profissional** com campos separados para achados favoráveis/contrários, informações faltantes, contraindicações e IDs de citações verificadas.
- Bloqueios quando um achado não estiver confirmado/revisado, quando sua origem pertencer a outra avaliação ou quando a citação não existir no conjunto documental. Um resultado aprovado significa **somente presença de vínculos de dados**.
- Testes com PDFs completamente fictícios gerados localmente, sem depender de bibliografia protegida ou diagnósticos reais.

## NÃO está implementado
- Não há interpretação diagnóstica automatizada, geração de hipóteses pelo LLM, ranking probabilístico, escolha de terapia ou prescrição.
- Não existe validador semântico independente que certifique que um trecho **sustenta** a conclusão clínica proposta.
- O parser não comprova autenticidade do arquivo enviado, atualização da diretriz, edição oficial, completude documental, permissão de reprodução, qualidade metodológica ou aplicabilidade ao caso.
- Uma citação textual correta na página não confirma que a recomendação seja segura.
- **Nenhuma hipótese passa a ser clinicamente validada** por esse mecanismo, mesmo que todas as referências e observações estejam vinculadas.
- A autenticação é de protótipo local, ainda sem controles institucionais e sem separação de credenciais profissionais.

## Endpoints
- `POST /evidence/documents?source_id=...&edition_label=...` com multipart `file`.
- `GET /evidence/documents`.
- `POST /evidence/documents/{id}/verify-quote`.
- `GET /evidence/documents/{id}/citations`.
- `POST /assessments/{id}/audit-differential` (não persiste nem executa condutas).

## Próximos passos seguros
1. Testar e revisar o processo de ingestão com documentos permitidos e benchmarks de variação no texto PDF.
2. Validar integridade de proveniência, controle de versões e detecção de atualização/retirada de diretrizes.
3. Definir protocolo de revisão semântica independente: citação correta **e** correspondência entre trecho, população-alvo, contraindicação e afirmação; incluir avaliadores clínicos.
4. Modelar raciocínio diferencial automatizado como proposta explicitamente não validada, com métricas de segurança por etiologia; somente após benchmarks e revisões de risco.
5. Revisão de segurança de parsing de PDF (isolamento de processo, quotas, logs, backups, LGPD e gestão de chaves) antes de usar dados reais.

## Dependências e testes
- Runtime: `pypdf` para leitura local.
- Testes: `reportlab` em `requirements-dev.txt` apenas para gerar PDFs fictícios.
- Executar `pip install -r requirements-dev.txt && python -m pytest -q`.
- Revisar resultado no GitHub Actions antes de integrar. Testes de API não são validação científica.

**Este é um protótipo para dados sintéticos, não um software assistencial.**
