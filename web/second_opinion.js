"use strict";
/* Second-opinion readiness view: facts vs hypotheses. NO diagnosis, no recommendations. */
async function renderSecondOpinionContext(assessmentId, parent){
  if(!parent || !parent.isConnected)return;
  const section=document.createElement("section");
  section.className="clinical-section";
  section.id="evidence-readiness";
  section.innerHTML='<div class="panel-header"><h2>Base para segunda opinião</h2><span class="tiny">Sem diagnóstico automatizado</span></div><p class="muted">Organizando fatos revisados e informações declaradas...</p>';
  parent.append(section);
  const result=await api("/assessments/"+encodeURIComponent(assessmentId)+"/evidence-readiness");
  if(!section.isConnected || state.selectedAssessment!==assessmentId)return;
  const context=result.context;
  const observed=context.observations.map(f=>'<tr><td>'+escapeHtml(f.field_name)+'</td><td>'+escapeHtml(f.text)+'</td><td>'+escapeHtml(f.proposed_source)+' / '+escapeHtml(f.human_decision)+'</td></tr>');
  const reported=context.reported_clinical_data.map(d=>'<tr><td>'+escapeHtml(d.field_name)+'</td><td>'+escapeHtml(readable(d.value))+'</td><td>'+escapeHtml(d.reporter)+'</td></tr>');
  const executed=context.interventions.map(i=>'<tr><td>'+escapeHtml(i.type)+'</td><td>'+escapeHtml(i.status)+'</td><td>'+escapeHtml(i.description)+'</td></tr>');
  const missing=context.missing_sections.map(s=>'<li>'+escapeHtml(s.replaceAll("_"," "))+'</li>').join("");
  const warnings=context.warnings.map(a=>'<div class="clinical-warning"><strong>'+escapeHtml(a.priority)+'</strong><p>'+escapeHtml(a.message)+'</p></div>').join("");
  section.innerHTML=
    '<div class="panel-header"><h2>Base para segunda opinião</h2><span class="tiny">Somente dados rastreáveis</span></div>'+
    '<p class="muted">A separação abaixo impede que a IA apresente propostas não revisadas como observações confirmadas.</p>'+
    '<div class="assessment-card"><strong>Semiologia revisada ('+context.observations.length+')</strong>'+
    (observed.length?table(["Campo","Observação validada","Origem proposta / revisão"],observed):'<p class="muted">Nenhum achado visual confirmado nesta avaliação.</p>')+'</div>'+
    '<div class="assessment-card"><strong>Anamnese registrada ('+reported.length+')</strong>'+
    (reported.length?table(["Campo","Valor registrado","Informante"],reported):'<p class="muted">Nenhum dado clínico atual registrado.</p>')+'</div>'+
    '<div class="assessment-card"><strong>Intervenções registradas ('+executed.length+')</strong>'+
    (executed.length?table(["Tipo","Situação","Descrição"],executed):'<p class="muted">Nenhuma intervenção informada.</p>')+'</div>'+
    warnings+
    '<div class="assessment-card"><strong>Dados excluídos e pendências</strong><p class="tiny">Achados pendentes: '+context.excluded_unreviewed_count+
    ' · Rejeitados: '+context.excluded_rejected_count+
    ' · Não avaliáveis: '+context.not_evaluable_count+'</p>'+
    (missing?'<ul class="tiny">'+missing+'</ul>':'<p class="tiny">Nenhuma lacuna estrutural sinalizada por este contrato.</p>')+'</div>'+
    '<div class="clinical-warning"><strong>Segunda opinião científica ainda não habilitada</strong>'+
    '<p>Não há fontes científicas verificadas associadas a este contexto. Diagnósticos diferenciais e sugestões de manejo permanecem vazios. A ausência de alerta não exclui gravidade clínica.</p></div>'+
    '<p class="tiny">Modelo: '+escapeHtml(context.schema_version)+' · Status: '+escapeHtml(context.assessment_status)+
    ' · Histórico atual: '+escapeHtml(context.history_revision===null?"não registrado":"revisão "+context.history_revision)+
    ' · Sem envio externo nesta visualização.</p>';
}
