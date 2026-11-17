"use strict";
/* Explicit clinician-authored differential audit; not diagnosis or treatment. */
async function renderDifferentialAudit(parent,assessmentId,context){
 if(!parent?.isConnected)return;
 const section=document.createElement("section");
 section.className="clinical-section";
 section.id="differential-audit";
 parent.append(section);
 const docs=await api("/evidence/documents");
 const grouped=await Promise.all(docs.map(async d=>({
   doc:d,citations:await api("/evidence/documents/"+encodeURIComponent(d.id)+"/citations")
 })));
 if(!section.isConnected||state.selectedAssessment!==assessmentId)return;
 const citations=grouped.flatMap(x=>x.citations);
 const observations=context.observations;
 const option=(id,label)=>'<option value="'+escapeHtml(id)+'">'+escapeHtml(label)+'</option>';
 const findingOptions=observations.map(o=>option(o.provenance.record_id,o.field_name+": "+o.text.slice(0,70))).join("");
 const citeOptions=citations.map(c=>option(c.id,"Pág. "+c.page_number+" · "+c.excerpt.slice(0,75))).join("");
 section.innerHTML='<div class="panel-header"><h2>Auditoria de hipótese diferencial</h2><span class="tiny">Experimental · sem raciocínio automatizado</span></div>'+
 '<p class="muted">Escreva uma hipótese sintética manualmente. O sistema verificará apenas os vínculos com achados revisados e citações existentes. A aprovação estrutural nunca significa diagnóstico correto.</p>'+
 '<form id="differential-form" class="assessment-card">'+
 '<div class="form-group"><label for="differential-title">Hipótese proposta pelo profissional (teste)</label><input id="differential-title" name="title" maxlength="180" required placeholder="Ex.: hipótese fictícia para teste"></div>'+
 '<div class="form-group"><label for="diff-support">Achado favorável revisado</label><select id="diff-support" name="support"><option value="">Nenhum selecionado</option>'+findingOptions+'</select></div>'+
 '<div class="form-group"><label for="diff-contrary">Achado contrário revisado</label><select id="diff-contrary" name="contrary"><option value="">Nenhum selecionado</option>'+findingOptions+'</select></div>'+
 '<div class="form-group"><label for="diff-cite">Citação literal conferida em PDF</label><select id="diff-cite" name="citation"><option value="">Nenhuma selecionada</option>'+citeOptions+'</select></div>'+
 '<div class="form-group"><label for="diff-missing">Informação ainda necessária</label><textarea id="diff-missing" name="missing" required minlength="3"></textarea></div>'+
 '<div class="form-group"><label for="diff-contraindications">Contraindicações/riscos a verificar</label><textarea id="diff-contraindications" name="contraindications" required minlength="3"></textarea></div>'+
 '<div class="form-group"><label for="diff-note">Justificativa do profissional</label><textarea id="diff-note" name="clinician_note" required minlength="10" maxlength="1200"></textarea></div>'+
 '<div class="form-group"><label for="diff-reviewer">Identificador fictício do revisor</label><input id="diff-reviewer" name="clinician_id" required maxlength="100"></div>'+
 '<button class="secondary-btn" type="submit">Auditar vínculos (não é diagnóstico)</button></form>'+
 '<div id="differential-results" aria-live="polite"></div>';
 $("differential-form").addEventListener("submit",async e=>{
   e.preventDefault();const fd=new FormData(e.currentTarget);
   const support=String(fd.get("support")||"");
   const opposing=String(fd.get("contrary")||"");
   const citation=String(fd.get("citation")||"");
   const candidate={
     title:String(fd.get("title")),supporting_finding_ids:support?[support]:[],
     opposing_finding_ids:opposing?[opposing]:[],citation_ids:citation?[citation]:[],
     missing_information:[String(fd.get("missing"))],
     contraindications_to_check:[String(fd.get("contraindications"))],
     clinician_note:String(fd.get("clinician_note"))
   };
   try {
     const result=await api("/assessments/"+encodeURIComponent(assessmentId)+"/audit-differential",{
       method:"POST",body:JSON.stringify({clinician_id:String(fd.get("clinician_id")),candidates:[candidate]})
     });
     const item=result.candidates[0];
     $("differential-results").innerHTML='<div class="assessment-card"><strong>'+escapeHtml(result.status==="blocked"?"Vínculos incompletos":"Vínculos estruturais localizados")+'</strong>'+
       '<p class="tiny">Correspondência de achados: '+item.linked_confirmed_observations+' · Citações verificadas: '+item.linked_verified_pdf_quotes+'</p>'+
       (item.blocking_issues.length?'<ul>'+item.blocking_issues.map(x=>'<li>'+escapeHtml(x)+'</li>').join("")+'</ul>':'<p>Sem bloqueios estruturais detectados; verificação clínica continua necessária.</p>')+
       '<p class="tiny">Adequação clínica não validada. Nenhum diagnóstico ou tratamento foi gerado pelo aplicativo.</p></div>';
   }catch(error){$("differential-results").textContent=error.message;}
 });
}
