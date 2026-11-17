"use strict";
/* Synthetic-case research sandbox. Never show output as clinical advice. */
async function renderExperimentalReasoning(parent, assessmentId){
  if(!parent?.isConnected)return;
  const section=document.createElement("section");
  section.className="clinical-section";
  section.id="synthetic-reasoning";
  parent.append(section);
  const [status,documents]=await Promise.all([
    api("/assessments/reasoning/status"),api("/evidence/documents")
  ]);
  if(!section.isConnected || state.selectedAssessment!==assessmentId)return;
  const citationSets=await Promise.all(documents.map(d=>api("/evidence/documents/"+encodeURIComponent(d.id)+"/citations")));
  const citations=citationSets.flat();
  const selections=citations.map(c=>'<label class="clinical-confirm"><input type="checkbox" name="citation_id" value="'+escapeHtml(c.id)+'"> Página '+escapeHtml(c.page_number)+': '+escapeHtml(c.excerpt.slice(0,130))+'</label>').join("");
  section.innerHTML='<div class="panel-header"><h2>Raciocínio assistido — laboratório sintético</h2><span class="tiny">'+(status.enabled&&status.semantic_reviewer_enabled?"Gerador e auditor configurados":"Indisponível para geração")+'</span></div>'+
    '<p class="muted">Gera hipóteses experimentais, argumentos favoráveis e contrários, lacunas e pontos a investigar. Nunca produz diagnóstico definitivo, recomendações terapêuticas ou validação clínica.</p>'+
    '<form id="reasoning-form" class="assessment-card">'+
      '<p class="tiny">Selecione referências literalmente conferidas contra o PDF carregado. A conferência textual não atesta aplicabilidade clínica.</p>'+
      (selections||'<p class="muted">Nenhuma citação de PDF verificada disponível.</p>')+
      '<label class="clinical-confirm"><input type="checkbox" name="synthetic" required> Confirmo que todos os dados desta avaliação são fictícios e de teste.</label>'+
      '<label class="clinical-confirm"><input type="checkbox" name="external" required> Autorizo o envio externo dos dados fictícios selecionados.</label>'+
      '<button type="submit" class="secondary-btn" '+(!status.enabled||!status.semantic_reviewer_enabled||!citations.length?"disabled":"")+'>Gerar hipóteses experimentais</button>'+
    '</form><div id="reasoning-result" aria-live="polite"></div>'+
    '<p class="tiny">A revisão por um segundo modelo é experimental e pode errar. Mesmo com vínculos corretos, não há validação clínica nem autorização de conduta. Não insira dados reais.</p>';
  $("reasoning-form")?.addEventListener("submit",async event=>{
    event.preventDefault();
    const form=event.currentTarget,button=form.querySelector('button[type="submit"]');
    const fd=new FormData(form);
    const selected=fd.getAll("citation_id").map(String);
    if(!selected.length)return notice("Selecione ao menos uma citação verificada.",true);
    const output=$("reasoning-result");
    button.disabled=true;output.textContent="Verificando dados e gerando rascunho experimental...";
    try{
      const result=await api("/assessments/"+encodeURIComponent(assessmentId)+"/reasoning-draft",{
        method:"POST",body:JSON.stringify({
          citation_ids:selected,
          confirm_synthetic_scenario:fd.get("synthetic")==="on",
          confirm_external_processing:fd.get("external")==="on"
        })
      });
      const heading=result.status==="blocked"?"Saída bloqueada por inconsistências":"Hipóteses para revisão profissional (não validadas)";
      output.innerHTML='<div class="clinical-warning"><strong>'+escapeHtml(heading)+'</strong>'+
       '<p>Não utilizar na assistência. Análise sem validação semântica independente de citações, contraindicações ou adequação clínica.</p></div>'+
       result.hypotheses.map(h=>
        '<div class="assessment-card"><strong>'+escapeHtml(h.title)+'</strong><p>'+escapeHtml(h.rationale)+'</p>'+
        '<p class="tiny">Referências favoráveis: '+h.supporting_record_ids.map(escapeHtml).join(", ")+'</p>'+
        '<p class="tiny">Referências contrárias: '+h.opposing_record_ids.map(escapeHtml).join(", ")+'</p>'+
        '<p class="tiny">Citações (IDs): '+h.citation_ids.map(escapeHtml).join(", ")+'</p>'+
        '<p><strong>Dados faltantes:</strong> '+h.missing_information.map(escapeHtml).join("; ")+'</p>'+
        '<p><strong>Riscos a investigar:</strong> '+h.contraindications_to_check.map(escapeHtml).join("; ")+'</p>'+
        '<p><strong>Incerteza:</strong> '+escapeHtml(h.uncertainty_note)+'</p>'+
        (h.blocking_issues.length?'<div class="clinical-warning">'+h.blocking_issues.map(escapeHtml).join("; ")+'</div>':'')+
        '<p class="tiny">Auditoria semântica: '+escapeHtml(h.semantic_audit_status||"não realizada")+'</p>'+
        (h.semantic_audit_issues?.length?'<div class="clinical-warning">'+h.semantic_audit_issues.map(escapeHtml).join("; ")+'</div>':'')+'</div>'
       ).join("")+
       '<p class="tiny">Modelo gerador: '+escapeHtml(result.model)+' · Revisor independente: '+escapeHtml(result.semantic_audit_model||"não executado")+' · Avaliação semântica executada: '+(result.semantic_audit_performed?"sim":"não")+' · Validação clínica: não · Recomendações: desabilitadas.</p>';
    }catch(err){output.textContent="Rascunho não gerado: "+err.message;}
    finally{button.disabled=!status.enabled||!status.semantic_reviewer_enabled;}
  });
}
