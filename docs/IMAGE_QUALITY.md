# Qualidade fotográfica e comparação longitudinal (protótipo)

## O que foi implementado
- Relatório técnico por imagem, gerado localmente a partir de JPEG normalizado e protegido.
- Indicadores: resolução, luminância média, desvio-padrão de luminância e variância de filtro de bordas.
- Avisos de brilho, baixo contraste, resolução insuficiente e possível falta de detalhes.
- Alertas de recaptura na interface após upload ou consulta manual.
- Comparação de metadados entre fotografias **de avaliações distintas da mesma lesão**, com checagem de ordem temporal.
- Acesso aos relatórios via sessão autenticada, sem chamadas a provedores externos.
- Testes com imagens sintéticas e restrições entre lesões diferentes.

## Endpoints
- `GET /photos/{photo_id}/quality`
- `GET /photos/{current_id}/compare/{previous_id}`
- Upload de fotos retorna também `quality`.

## Limites metodológicos essenciais
Os limites de brilho, contraste e variância são **heurísticas de engenharia arbitradas para testes**, não limiares publicados ou validados para feridas. Em particular, a variância de bordas medida com Pillow não é equivalente à variância do Laplaciano do OpenCV e pode dar falso aviso em fotos de pele uniformemente colorida ou falsos negativos em fotos ruidosas.

**Sem inferência autorizada de área em cm².** Uma foto com resolução suficiente e dimensões iguais não garante calibração, mesma perspectiva, correspondência anatômica ou comparabilidade clínica.

- `quantitative_measurement_allowed=false` e `clinical_validation=false` sempre.
- `spatial_alignment_validated=false` e `quantitative_area_comparison_allowed=false` sempre.
- Não há diagnóstico, classificação de risco, identificação de infecção ou indicação de conduta a partir deste módulo.
- Não compare fotos de pacientes reais; permanecem pendentes governança, validação e controles necessários.

## Validação necessária
Antes de decisões baseadas no gatekeeper, construir conjunto rotulado por profissionais para: nitidez, iluminação, sombras, reflexos, perspectiva, presença de régua, qualidade suficiente para cada tarefa e tons de pele. Estimar sensibilidade para fotos inadequadas, falsos bloqueios e variação por dispositivo.

A função atualmente **avisa, não impede** que um profissional registre avaliação. Isso evita que limiares experimentais descartem documentação clínica útil. No módulo de IA, registrar e comunicar essas incertezas; não interpretar avisos como certeza de imagem inválida.

## Testes e manutenção
Rodar `python -m pytest -q`. Os testes não constituem validação clínica. A CI deve ser aprovada antes de integrar mudanças.
