# Base rastreável para segunda opinião — MVP experimental

## Escopo implementado

A interface de avaliação apresenta a seção **Base para segunda opinião**, alimentada exclusivamente por um endpoint de leitura local:

- `GET /assessments/{assessment_id}/clinical-context`
- `GET /assessments/{assessment_id}/evidence-readiness`

As chamadas exigem autenticação de proprietário no backend. **Nenhum conteúdo desta funcionalidade é enviado a um modelo remoto.**

## Regras de incorporação dos dados

1. **Semiologia:** entram somente `Finding` da avaliação atual com `validation_status=confirmed|corrected`, `validated_text` preenchido, revisor e horário da revisão registrados. `pending`, `rejected` e os classificados como `not_evaluable` ou `source=unknown` são explicitamente excluídos dos fatos visuais.
2. **Anamnese:** é utilizada apenas a **última revisão humana registrada na avaliação atual**; campos `null`, `unknown` e `not_assessed` não são convertidos em ausências de sinais/sintomas. Um valor `false` explicitamente informado permanece como relato negativo, acompanhado de origem e identificação de registro.
3. **Intervenções:** são preservados `planned`, `performed` e `not_performed` sem igualar uma prescrição à execução. Cada entrada informa quando foi registrada e por quem.
4. **Proveniência:** os dados incluem identificador da avaliação, identificador de registro original, horário de registro/revisão e registrador.
5. **Histórico anterior:** não é importado automaticamente como evidência de avaliação atual. Existe endpoint específico para consulta histórica em outra tela.
6. **Mensuração:** a área legada não é incorporada como medida aprovada para decisões. O contexto marca `validacao_especifica_da_area` enquanto não houver verificação formal da metodologia e da medida.
7. **Alertas:** são somente os avisos determinísticos da última revisão da anamnese, sem diagnóstico ou garantia de ausência de emergência quando vazios.

## Contrato científico

O resultado de `/evidence-readiness` possui explicitamente:

- `sources=[]`
- `evidence_verified=false`
- `reasoning_executed=false`
- `differential_diagnoses=[]`
- `suggested_interventions=[]`

Esses valores são intencionalmente fixos nesta etapa. **Nenhuma fonte é fabricada. Nenhum raciocínio diagnóstico ou recomendação terapêutica é emitido.**

A futura integração RAG exigirá: documentação licenciada/autorizada, versão e data, identificação do trecho/página, verificação da citação, avaliação de aplicabilidade clínica por etiologia, controle de revisões e testes com casos independentes. Recuperar um trecho não comprova adequação ao caso.

## Restrições e próximo trabalho

- Protótipo local, somente informações fictícias. Persistem lacunas de governança e segurança de dados.
- Ainda não há modelo de IA para geração de segunda opinião clínica nem recuperador de evidências ativo.
- A consistência estrutural não constitui validação do diagnóstico, segurança de alertas ou precisão do modelo.
- Não há assinatura eletrônica ou auditoria inviolável dos registros.
- A automação deverá trabalhar apenas com um **snapshot versionado** antes de executar raciocínio; não usar achados pendentes nem completar automaticamente campos ausentes.

## Testes

`tests/test_second_opinion.py` cobre rejeição de achados pendentes, de achados negados, dados não avaliáveis, correções humanas, retenção de valores negativos explícitos, origem das informações, diferença planejado/realizado, ausência de evidências inventadas e isolamento de uma avaliação anterior.

Rodar `python -m pytest -q` e validar os resultados na CI antes de mesclar. Os testes ainda não são comprovação de segurança clínica.
