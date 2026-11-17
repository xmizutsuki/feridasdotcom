# Análise visual experimental (sem validação clínica)

## Estado
Este módulo **não é** uma segunda opinião diagnóstica nem recomenda condutas. Ele descreve aspectos visíveis e sempre produz **rascunhos pendentes de revisão humana**.

## Fluxo
1. A foto, anteriormente normalizada e protegida em armazenamento local, é selecionada dentro de uma avaliação não finalizada.
2. O operador confirma explicitamente o processamento externo no momento do envio.
3. O servidor exige `FERIDAS_REMOTE_IMAGE_ANALYSIS=true`, `FERIDAS_VISION_MODEL` e `FERIDAS_OPENAI_API_KEY`. O padrão é **desligado**.
4. A imagem é transmitida ao provedor configurado. **Não utilizar imagens de pacientes reais neste estágio.**
5. A resposta é convertida para um contrato Pydantic estrito: campos predefinidos, origem, sustentação e limitações.
6. O sistema rejeita profundidade classificada como achado visual confirmado, campos duplicados e estruturas inválidas.
7. Registra apenas propostas `pending`; não finaliza avaliações nem altera achados já existentes.
8. O profissional deve confirmar, corrigir ou rejeitar cada item para então finalizar.

## Contrato estruturado
Campos aceitos: `wound_bed`, `tissue_appearance`, `edges`, `periwound`, `color`, `exudate_appearance`, `depth`, `limitations`.

- `source=image`: informação observável na foto.
- `source=unknown`: não observável.
- `support=high|limited|not_evaluable`: sustentação qualitativa, **não** probabilidade validada.
- A profundidade é explicitamente `unknown/not_evaluable`.
- A avaliação **não** infere dor, odor, pulso, perfusão ou medida de exsudato pela foto.

## Limites e riscos
- O esquema impede algumas classes de resposta inconsistente; **não** detecta todas as alucinações semânticas.
- Não há detecção validada de sinais de gravidade nem medição automática de ferida.
- Ausência de autenticação empresarial, controle de consentimentos, governança de dados e estudos clínicos impede uso com pacientes reais.
- O provedor externo possui seus próprios termos de retenção e proteção de dados. O operador deve verificar requisitos legais antes de qualquer uso futuro.
- Se a análise falhar, o endpoint retorna erro e não grava achados incompletos.
- Não há reprocessamento automático de análises anteriores. Rascunhos existentes bloqueiam nova proposta automatizada para evitar sobrescrita silenciosa.

## Testes
`tests/test_vision.py` usa objetos fictícios e simula o provedor, sem acesso a rede. Avalia validação de esquema, opt-in, vínculo correto da foto e status de revisão. A suíte CI precisa ser executada e aprovada antes de integração.

## Próximos passos
- Estudos de benchmark e confiabilidade em diferentes condições de captura.
- Revisão de segurança das rotas e política de uso com informações clínicas.
- Serviço de leitura independente de imagens, mecanismos de abstenção e qualidade visual.
- Raciocínio clínico separado, com RAG científico, após validação das descrições.
