# Motor experimental de raciocínio diferencial — somente casos sintéticos

## Implementado
- Integração opcional com um modelo de linguagem para **propor hipóteses diferenciais preliminares**, não conclusões diagnósticas.
- Padrão desabilitado: `FERIDAS_EXPERIMENTAL_REASONING=false`. Exige modelo definido e chave de API configurada no ambiente local, nunca no Git.
- Confirmação explícita de cenário inteiramente fictício e autorização de processamento externo antes de cada envio.
- Exige avaliação finalizada, anamnese atual preenchida e ao menos um achado revisado; não importa registros de visitas anteriores.
- Exige IDs selecionados de citações previamente verificadas em PDFs locais, e reconfere as citações e o hash do texto da página antes de enviar contexto.
- Interrompe análise se houver avisos determinísticos classificados como `urgent_review`; o modelo não pode emitir saída tranquilizadora em casos sinalizados por essas regras. **A ausência de alerta não exclui emergências.**
- Contrato JSON Pydantic estrito: até 3 hipóteses, justificativa, identificadores de achados favoráveis e contrários, citações, informações ausentes, riscos/contraindicações a verificar e incertezas.
- Motor de auditoria determinística verifica se os IDs de fatos e citações que o modelo mencionou pertencem ao conjunto autorizado. IDs inventados bloqueiam a saída.
- Resultados sempre possuem `clinically_validated=false`, `semantic_evidence_verified=false` e `therapeutic_recommendations_enabled=false`. Mesmo a saída de status `review_required` **não é aprovada para uso clínico**.
- A interface oferece o laboratório sintético dentro da revisão de avaliação, com aviso persistente de não utilização assistencial.
- Apenas logs técnicos do modelo, resultado e quantidade de hipóteses; o resultado não é salvo como diagnóstico clínico.

## O que a auditoria NÃO verifica
- **Não verifica semanticamente** se um trecho do PDF realmente sustenta a hipótese proposta.
- Não consegue garantir que a diretriz seja autêntica, atual ou aplicável ao paciente.
- Não valida exames, classificação de lesão, contraindicações nem qualidade da hipótese.
- Não previne todas as alucinações: um modelo pode escolher um ID existente e atribuir-lhe significado incorreto.
- Não há decisão terapêutica, escolha de cobertura, prescrição, cálculo de risco probabilístico nem emissão de laudo.
- Não há comprovação clínica de sensibilidade para sinais graves; o monitoramento sintético não permite atender pacientes reais.
- **Não habilitar com dados reais**: há envio externo de dados desidentificados/rotulados, e a plataforma ainda não dispõe da governança necessária.

## Fluxo técnico
1. Enfermeiro revisa dados sintéticos e finaliza a avaliação.
2. Seleciona citações já verificadas por presença literal no PDF.
3. Confirma cenário sintético e envio externo.
4. Backend reconfere citações, exclui dados não avaliados e bloqueia avisos urgentes conhecidos.
5. Modelo recebe apenas uma seleção de registros de avaliação, sem fotos e sem identificador de paciente/lesão.
6. Resposta é analisada por contrato tipado.
7. Auditor independente de regras confere ID de observações/citações e acusa lacunas.
8. A interface apresenta rascunho **sempre para revisão**, sem salvar como conclusão clínica.

## Arquivos
- `app/reasoning_schemas.py` — contrato de saída.
- `app/reasoning.py` — adaptador para LLM e auditoria.
- `app/reasoning_routes.py` — acesso e bloqueios.
- `web/reasoning.js` — laboratório sintético.
- `tests/test_reasoning.py` — testes sem chamadas reais à IA.

## Como testar
Instalar `requirements-dev.txt`; usar apenas dados sintéticos. Para realizar uma chamada real com dados fictícios, definir no ambiente:
```shell
FERIDAS_EXPERIMENTAL_REASONING=true
FERIDAS_REASONING_MODEL=<modelo-compatível>
FERIDAS_OPENAI_API_KEY=<chave-privada>
```
Credenciais ficam somente em variáveis de ambiente locais. Modelos, políticas de envio e formatos da API estão sujeitos a atualização. O teste por mock não garante que um modelo real retorne contrato válido.

## Próximo marco científico
Avaliar segurança em conjunto de casos sintéticos adjudicados por especialistas; calibrar bloqueios por etiologia, estabelecer validação semântica independente de citações e testar vieses de automação antes de qualquer aplicação clínica.
