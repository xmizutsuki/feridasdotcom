# Auditoria semântica independente — laboratório sintético

## Escopo e limites

O Feridas.com agora implementa um segundo modelo de linguagem **separadamente configurado** para revisar as hipóteses do gerador. Este recurso permanece desligado por padrão e é destinado somente a casos integralmente fictícios.

**Independência aqui significa modelo distinto, não independência institucional ou ausência de erros correlacionados.** Dois modelos podem produzir o mesmo erro, interpretar a citação incorretamente ou deixar de identificar uma contraindicação. Nenhum parecer substitui avaliação clínica por especialistas.

## Fluxo fail-closed

1. Requer dados sintéticos, consentimento de processamento externo e avaliação finalizada.
2. Exige achados revisados, anamnese atual e citações conferidas literalmente no PDF local.
3. Impede geração quando regras existentes sinalizam prioridade urgente. **A ausência desse sinal não exclui emergências.**
4. O modelo gerador produz hipóteses com IDs de fatos/citações.
5. Auditoria determinística confere os vínculos e rejeita referências inexistentes ou registros não revisados.
6. Somente se a auditoria estrutural passar e o revisor semântico estiver configurado, um segundo modelo avalia:
   - se cada trecho sustenta a afirmação;
   - se população e escopo são compatíveis;
   - se há contradições ou contraindicações;
   - se existem afirmações sem base, linguagem excessiva ou informações críticas não disponíveis.
7. O backend exige um resultado do revisor para cada hipótese e cada citação; respostas incompletas e respostas incompatíveis são bloqueadas.
8. Se qualquer bloqueio ocorrer, hipóteses geradas **não são exibidas**; somente os motivos estruturais e de auditoria são retornados.
9. Resultados com parecer positivo permanecem `review_required`, `clinical_validation=false`, `semantic_evidence_verified=false` e `therapeutic_recommendations_enabled=false`.

## Configuração

```ini
FERIDAS_EXPERIMENTAL_REASONING=false
FERIDAS_REASONING_MODEL=
FERIDAS_SEMANTIC_AUDIT=false
FERIDAS_REVIEW_MODEL=
FERIDAS_OPENAI_API_KEY=
```

Para experimento voluntário com dados **100% fictícios**, ambos os módulos devem ser explicitamente habilitados, e os nomes dos modelos devem ser diferentes. O código não expõe chaves na interface. Dados enviados ao provedor externo continuam sujeitos à política do provedor e não devem incluir informações de pacientes reais.

## Banco de testes sintéticos

`benchmarks/semantic_contract_cases.json` contém **12 casos criados para testar a lógica**, envolvendo afirmações contraditas, suporte insuficiente, população incompatível, conflito de contraindicação, ausência de informação crítica, citação inventada/omitida e saída excessivamente confiante.

`tests/test_semantic_benchmark.py` executa essas verificações, mas **não mede precisão real de LLMs** porque usa respostas simuladas e rótulos definidos pelo desenvolvedor. Não há adjudicação clínica de especialistas neste conjunto.

O formulário em `benchmarks/ADJUDICATION_PROTOCOL.md` descreve como construir futuramente um conjunto cego revisado por profissionais, incluindo casos graves e representatividade de etiologias e tons de pele.

### Lacunas antes de qualquer utilização clínica

- Validar identidade e versão dos documentos, integridade e licenciamento.
- Separar casos de ajuste de prompt dos casos de teste externos.
- Obter julgamentos independentes de especialistas e adjudicação de divergências.
- Medir adequação semântica, erros por etiologia, contraindicações e falsos negativos de gravidade, com intervalos de confiança.
- Conduzir estudo de fatores humanos e monitoramento de viés de automação.
- Implementar autorização profissional, segurança institucional, governança LGPD e avaliação regulatória.

**Esta camada não é uma segunda opinião clínica validada e não pode orientar pacientes reais.**
