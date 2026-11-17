# Arquitetura inicial — feridasdotcom

## Objetivo
Prontuário longitudinal experimental com avaliação semiológica revisável e rastreabilidade. Os sete agentes previstos no planejamento permanecem como **módulos lógicos futuros**, não como serviços independentes.

## Implementado neste marco
- Paciente pseudonimizado → Lesões → Avaliações → Achados por campo.
- Achado possui texto proposto, origem, sustentação e decisão humana independente.
- Finalização bloqueada até revisão de todos os achados.
- Registros finalizados não podem ser alterados por endpoints de revisão.
- Eventos de criação, revisão e finalização geram trilha de auditoria.
- Tendência de área apenas entre avaliações validadas, usando cálculo determinístico.
- Testes com dados sintéticos.

## Não implementado ainda
- Autenticação e autorização; isolamento entre usuários.
- Armazenamento protegido de fotografias, criptografia e sincronização offline.
- IA multimodal, segmentação, qualidade de imagem, mensuração automática.
- RAG, protocolos clínicos versionados, triagem de risco, prescrições e condutas.
- Adendos formais, imutabilidade protegida no banco, assinatura e backups.
- Validação científica, avaliação regulatória e uso com pacientes reais.

## Próximos passos
1. Identidade/acesso e armazenamento criptografado.
2. Migrações Alembic e adendos auditáveis.
3. Interface PWA com dados de demonstração.
4. Captura padronizada e contrato JSON para avaliação multimodal.
5. Benchmark de avaliação e testes de segurança.
6. Apenas após validação: segunda opinião com recuperação de evidências.

**Nota:** SQLite e ausência de autenticação são exclusivos para desenvolvimento local. Não hospedar publicamente esta API nem inserir dados reais de pacientes.
