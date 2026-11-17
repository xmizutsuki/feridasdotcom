# Anamnese clínica estruturada e registro de intervenções

## Escopo da entrega
Protótipo de coleta estruturada e acompanhamento **sem inferência diagnóstica**.

- Anamnese por avaliação: tempo de evolução, dor (0–10), piora da dor, febre, piora rápida, eritema em expansão, drenagem purulenta, odor, exsudato, condição de perfusão informada, diabetes informado, medidas de descarga de pressão/compressão, alergias, comorbidades e medicações.
- Registros opcionais permanecem **null** quando não informados. Não interpretar null como ausência de sintoma.
- Fonte dos dados: profissional, paciente, cuidador ou prontuário anterior.
- Revisão declarada pelo registrador para salvar; isto **não equivale a assinatura digital ou autenticação de identidade profissional**.
- Revisões de anamnese adicionam nova linha com número de versão; não sobrescrevem registro anterior.
- Tratamentos com estados separados `planned`, `performed` e `not_performed`; uma intervenção realizada exige data/hora.
- Consulta de anamnese anterior **apenas de avaliação finalizada da mesma lesão** e com rótulo de informação histórica, nunca pré-validada.
- Linha do tempo de dados da lesão sem inferência causal.
- Alertas conservadores por regras determinísticas explícitas (veja abaixo), sem diagnóstico.

## Endpoints autenticados
- `POST/GET /assessments/{id}/history`
- `GET /assessments/{id}/previous-history`
- `POST/GET /assessments/{id}/interventions`
- `GET /lesions/{id}/interventions`
- `GET /lesions/{id}/clinical-timeline`

## Limites dos alertas
Exemplos de gatilhos experimentais em `app/clinical_rules.py`:
- Piora rápida relatada: orientação de avaliação presencial urgente.
- Febre associada a eritema em expansão ou drenagem purulenta relatada: avaliação presencial urgente.
- Possível alteração de perfusão informada: avaliação clínica/vascular com prioridade segundo gravidade.
- Piora da dor e alterações locais: recomendação de reavaliação.

**Nenhum gatilho validou sensibilidade/especificidade para sepse, infecção, isquemia ou fasceíte. A ausência de alerta NÃO exclui doença grave.** Os campos dependem de informação humana, não de inspeção automática da foto. Não existe recomendação de cobertura, antimicrobiano ou desbridamento.

## Imutabilidade e integridade
- API não oferece edição ou exclusão das revisões/condutas.
- Avaliações finalizadas recusam novos registros por essas rotas.
- Há trilha básica de criação de anamnese/intervenções com metadados, sem copiar dados sensíveis no log.
- Falta auditoria inviolável, assinatura digital, controle de perfis, migrações, correção por adendo após finalização e mecanismos de concorrência robustos.
- **Não é prontuário eletrônico certificado**.

## Testes e governança
`tests/test_clinical.py` verifica campos desconhecidos, limites de validação, revisões, segurança dos endpoints, histórico da mesma lesão e planejado versus executado.

Use apenas dados sintéticos. Não implantar com dados reais ou para orientar condutas assistenciais. A efetiva execução dos testes em CI deve ser confirmada antes de mesclar o PR.

## Próxima etapa
- Protocolos de testes clínico-computacionais e benchmark dos sinais de alerta.
- Autenticação profissional, criptografia dos campos do banco e adendos formalmente auditáveis.
- Ligação de achados confirmados, imagens e anamnese aos módulos de raciocínio clínico, após validação independente.
