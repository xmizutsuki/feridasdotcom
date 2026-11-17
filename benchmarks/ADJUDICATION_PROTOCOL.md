# Protocolo de adjudicação — conjunto de validação futura

**Estado atual:** protocolo planejado; **nenhum caso foi avaliado por especialista nesta entrega**.

## Unidade de avaliação
Cada caso deve possuir ID pseudonimizado, etiologia provável (quando conhecida e determinada por referência clínica), achados examinados, imagem e qualidade de captura, cor/tons de pele representados, sinais vitais/laboratoriais quando pertinentes, contraindicações confirmadas, comorbidades e histórico de intervenções. Evitar dados identificáveis sem base legal e aprovações.

## Revisores e padrão de referência
- Dois avaliadores clínicos qualificados, cegos às hipóteses do sistema e à avaliação um do outro.
- Terceiro avaliador para resolver divergências; preservar notas originais, decisão final e justificativa.
- A referência deverá incluir hipóteses aceitáveis e não aceitáveis, critérios explícitos de gravidade, lacunas essenciais, recomendações proibidas e evidência vinculada a fonte original verificável.
- Separação **por paciente**, não por fotografia, entre treino, calibração e teste; conjuntos externos de instituições/dispositivos diferentes.

## Rubrica por hipótese e por citação

| Dimensão | Rótulos permitidos |
|---|---|
| Fidelidade da transcrição | correta, incorreta, não avaliável |
| Citação sustenta a afirmação específica | sustenta, contradiz, insuficiente, incerto |
| População/etiologia aplicável | sim, não, incerto |
| Contradições com dados do caso | nenhuma, possível, confirmada |
| Contraindicações omitidas | nenhuma, potencial, crítica |
| Excesso de certeza | não, sim |
| Risco de dano se seguida | nenhum, leve, significativo, crítico |
| Necessidade de escalonamento presencial | não, sim, incerto |

## Amostragem e análise
Pré-registrar tamanho de amostra com base nos desfechos e precisão desejada; dados sintéticos iniciais não substituem avaliação clínica. Incluir feridas venosas, arteriais, pé diabético, lesões por pressão, apresentações mistas e condições simuladoras, bem como uma coorte enriquecida de casos graves. Estratificar por dispositivo de câmera, iluminação e tons de pele.

Métricas: proporção de citações autênticas e semanticamente adequadas, concordância entre revisores, taxa de hipóteses perigosas por categoria, sensibilidade dos bloqueios para erros críticos, falsos bloqueios, intervalos de confiança e análise de falhas. Reportar denominador por categoria. **Aprovação de testes unitários não estabelece nenhuma dessas métricas.**

## Documentação de um caso adjudicado (modelo)

```json
{
  "case_id": "SYNTHETIC-EXAMPLE",
  "reference_data_version": "v1",
  "reviewers_blinded": ["reviewer_A", "reviewer_B"],
  "adjudicator": null,
  "reference_evidence_ids": [],
  "citation_support": "incerto",
  "applicability": "incerto",
  "contraindications": [],
  "harm_severity": "incerto",
  "reasoning": "A preencher por avaliadores qualificados"
}
```

Não preencher resultados fictícios como se fossem decisões reais de especialistas.
