"use strict";
const $ = (id) => document.getElementById(id);
let csrfToken = "";
const labels = {dashboard:"Visão geral",patients:"Pacientes",lesions:"Lesões",assessments:"Avaliações",trends:"Evolução"};
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const date = (d) => d ? new Date(d).toLocaleDateString("pt-BR") : "—";
const state = {view:"dashboard",patients:[],lesions:[],assessments:[],selectedPatient:"",selectedLesion:"",selectedAssessment:"",findings:[]};
async function api(path, options={}) {
  const isForm = options.body instanceof FormData;
  const method = (options.method || "GET").toUpperCase();
  const headers = {...(!isForm && options.body ? {"Content-Type":"application/json"} : {}),...(options.headers || {})};
  if(!["GET","HEAD","OPTIONS"].includes(method) && csrfToken)headers["X-CSRF-Token"]=csrfToken;
  const response=await fetch(path,{...options,credentials:"same-origin",headers});
  const raw=await response.text(); let data;
  try {data=raw?JSON.parse(raw):null;} catch {data=null;}
  if(!response.ok) throw new Error(typeof data?.detail==="string"?data.detail:"Erro "+response.status+" ao carregar os dados");
  return data;
}
function notice(message,isError=false){const n=$("notice");n.textContent=message;n.classList.toggle("error",isError);n.hidden=false;window.scrollTo({top:0,behavior:"smooth"});}
function hideNotice(){$("notice").hidden=true;}
function empty(message,description="") {return '<div class="empty"><div class="empty-icon">✳</div><strong>'+escapeHtml(message)+'</strong><p>'+escapeHtml(description)+'</p></div>';}
function chip(status){const isValid=status==="validated";return '<span class="chip '+(isValid?"":"draft")+'">'+(isValid?"Validada":"Rascunho")+'</span>';}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(h=>'<th>'+escapeHtml(h)+'</th>').join("")+'</tr></thead><tbody>'+rows.join("")+'</tbody></table></div>';}
function patientName(id){return state.patients.find(p=>p.id===id)?.pseudonym||"Não identificado";}
function lesionName(id){const x=state.lesions.find(l=>l.id===id);return x?x.location:"Não selecionada";}
function selectOptions(items,selected,render){return items.map(x=>'<option value="'+escapeHtml(x.id)+'" '+(selected===x.id?"selected":"")+'>'+escapeHtml(render(x))+'</option>').join("");}
async function load(){
  state.patients=await api("/patients");
  state.lesions=(await Promise.all(state.patients.map(p=>api("/patients/"+encodeURIComponent(p.id)+"/lesions")))).flat();
  state.assessments=(await Promise.all(state.lesions.map(l=>api("/lesions/"+encodeURIComponent(l.id)+"/assessments")))).flat();
  if(!state.patients.some(p=>p.id===state.selectedPatient))state.selectedPatient=state.patients[0]?.id||"";
  if(!state.lesions.some(l=>l.id===state.selectedLesion))state.selectedLesion=state.lesions[0]?.id||"";
  if(!state.assessments.some(a=>a.id===state.selectedAssessment))state.selectedAssessment=state.assessments[0]?.id||"";
}
function setView(view){state.view=view;hideNotice();document.querySelectorAll(".navitem").forEach(b=>b.classList.toggle("active",b.dataset.view===view));$("breadcrumb").textContent=labels[view];$("page-title").textContent=labels[view];$("eyebrow").textContent=view==="dashboard"?"PAINEL CLÍNICO":"REGISTROS CLÍNICOS";$("page-subtitle").textContent=({dashboard:"Acompanhe registros e avaliações em um único lugar.",patients:"Cadastre apenas identificadores fictícios neste protótipo.",lesions:"Organize e acompanhe cada lesão de forma independente.",assessments:"Registre achados e revise cada informação antes da finalização.",trends:"Compare medidas de avaliações validadas."})[view];const actions={dashboard:["+ Novo paciente",()=>modalPatient()],patients:["+ Novo paciente",()=>modalPatient()],lesions:["+ Nova lesão",()=>modalLesion()],assessments:["+ Nova avaliação",()=>modalAssessment()],trends:["+ Nova avaliação",()=>modalAssessment()]};$("primary-action").textContent=actions[view][0];$("primary-action").onclick=actions[view][1];render();}
function render(){
  const c=$("content");
  if(state.view==="dashboard"){
    const valid=state.assessments.filter(a=>a.status==="validated").length;
    c.innerHTML='<div class="stats"><div class="stat"><div class="stat-label">Pacientes cadastrados</div><div class="stat-number">'+state.patients.length+'</div><div class="stat-foot">Registros fictícios</div></div><div class="stat"><div class="stat-label">Lesões acompanhadas</div><div class="stat-number">'+state.lesions.length+'</div><div class="stat-foot">Em acompanhamento</div></div><div class="stat"><div class="stat-label">Avaliações validadas</div><div class="stat-number">'+valid+'</div><div class="stat-foot">'+(state.assessments.length-valid)+' rascunho(s) pendente(s)</div></div></div><section class="panel"><div class="panel-header"><h2>Avaliações recentes</h2><button class="link-btn" data-go="assessments">Ver todas →</button></div>'+(state.assessments.length?renderAssessmentsTable(state.assessments.slice().reverse().slice(0,6)):empty("Nenhuma avaliação ainda","Comece cadastrando um paciente fictício e sua primeira lesão."))+'</section><section class="panel"><div class="panel-header"><h2>Sobre esta versão</h2></div><p class="muted">Este protótipo permite registrar avaliações estruturadas e revisar achados manualmente. Não realiza diagnóstico, análise de fotos ou segunda opinião por IA. Não inserir dados reais de pacientes.</p></section>';
  } else if(state.view==="patients"){
    c.innerHTML='<section class="panel"><div class="panel-header"><h2>Pacientes</h2><span class="tiny">'+state.patients.length+' registro(s)</span></div>'+(state.patients.length?table(["Identificador","Cadastro","Ação"],state.patients.map(p=>'<tr><td class="data-name">'+escapeHtml(p.pseudonym)+'</td><td>'+date(p.created_at)+'</td><td><button class="link-btn" data-patient="'+escapeHtml(p.id)+'">Ver lesões →</button></td></tr>')):empty("Nenhum paciente","Cadastre um identificador fictício para começar."))+'</section>';
  } else if(state.view==="lesions"){
    c.innerHTML='<section class="panel"><div class="panel-header"><h2>Lesões</h2><span class="tiny">'+state.lesions.length+' registro(s)</span></div>'+(state.lesions.length?table(["Localização","Paciente","Etiologia","Abertura","Ação"],state.lesions.map(l=>'<tr><td class="data-name">'+escapeHtml(l.location)+'</td><td>'+escapeHtml(patientName(l.patient_id))+'</td><td>'+escapeHtml(l.etiology||"Não informada")+'</td><td>'+date(l.opened_at)+'</td><td><button class="link-btn" data-lesion="'+escapeHtml(l.id)+'">Avaliar →</button></td></tr>')):empty("Nenhuma lesão cadastrada","Crie uma lesão associada a um paciente fictício."))+'</section>';
  } else if(state.view==="assessments"){
    const items=state.assessments.filter(a=>!state.selectedLesion||a.lesion_id===state.selectedLesion);
    c.innerHTML='<div class="filters"><div class="form-group"><label for="lesion-filter">Filtrar por lesão</label><select id="lesion-filter"><option value="">Todas as lesões</option>'+selectOptions(state.lesions,state.selectedLesion,l=>l.location+" · "+patientName(l.patient_id))+'</select></div></div><section class="panel"><div class="panel-header"><h2>Avaliações registradas</h2><span class="tiny">'+items.length+' avaliação(ões)</span></div>'+(items.length?renderAssessmentsTable(items.slice().reverse()):empty("Nenhuma avaliação","Adicione uma avaliação para iniciar o histórico."))+'</section><section class="panel" id="review-panel"><div class="panel-header"><h2>Revisão dos achados</h2></div><div id="review-content">'+empty("Selecione uma avaliação","Clique em 'Revisar' em uma linha da tabela.")+'</div></section>';
    $("lesion-filter").value=state.selectedLesion;
    $("lesion-filter").addEventListener("change",ev=>{state.selectedLesion=ev.target.value;render();});
    if(state.selectedAssessment && items.some(a=>a.id===state.selectedAssessment))renderReview().catch(e=>notice(e.message,true));
  } else if(state.view==="trends")renderTrends();
}
function renderAssessmentsTable(items){return table(["Data","Lesão","Área","Situação","Ação"],items.map(a=>'<tr><td>'+date(a.captured_at)+'</td><td class="data-name">'+escapeHtml(lesionName(a.lesion_id))+'</td><td>'+escapeHtml(a.area_cm2===null?"Não medida":a.area_cm2+" cm²")+'</td><td>'+chip(a.status)+'</td><td><button class="link-btn" data-assessment="'+escapeHtml(a.id)+'">Revisar →</button></td></tr>'));}
async function renderReview(){
  const a=state.assessments.find(x=>x.id===state.selectedAssessment);
  const el=$("review-content");if(!el||!a)return;
  state.findings=await api("/assessments/"+encodeURIComponent(a.id)+"/findings");
  let html='<p class="muted">Avaliação de '+date(a.captured_at)+' · '+escapeHtml(lesionName(a.lesion_id))+' · '+(a.status==="validated"?"Finalizada":"Em revisão")+'</p>';
  if(!state.findings.length)html+=empty("Sem achados registrados","Adicione um achado para iniciar a revisão.");
  else html+=state.findings.map(f=>'<div class="review-item"><h3>'+escapeHtml(f.field_name)+'</h3><div class="tiny">Origem: '+escapeHtml(f.source)+' · Sustentação: '+escapeHtml(f.support)+' · Revisão: '+escapeHtml(f.validation_status)+'</div><p>Proposto: '+escapeHtml(f.proposed_text)+'</p>'+(f.validated_text?'<p><strong>Validado:</strong> '+escapeHtml(f.validated_text)+'</p>':'')+(f.validation_status==="pending"&&a.status!=="validated"?'<div class="review-actions"><button class="secondary-btn" data-review="'+escapeHtml(f.id)+'" data-decision="confirmed">Confirmar</button><button class="secondary-btn" data-review="'+escapeHtml(f.id)+'" data-decision="corrected">Corrigir</button><button class="secondary-btn" data-review="'+escapeHtml(f.id)+'" data-decision="rejected">Rejeitar</button></div>':'')+'</div>').join("");
  if(a.status!=="validated")html+='<div class="detail-actions"><button class="secondary-btn" id="add-finding">+ Adicionar achado</button><button class="primary-btn" id="finalize-assessment" '+(!state.findings.length||state.findings.some(f=>f.validation_status==="pending")?"disabled":"")+'>Finalizar avaliação</button></div>';
  const photos=await api("/assessments/"+encodeURIComponent(a.id)+"/photos");
  html+='<h3>Fotografias da avaliação</h3><p class="tiny">Imagens privadas, reprocessadas sem EXIF e protegidas por criptografia em disco.</p>';
  if(photos.length)html+='<div class="photos-grid">'+photos.map(p=>'<div class="photo-tile"><img loading="lazy" alt="Fotografia clínica cadastrada" src="/photos/'+encodeURIComponent(p.id)+'"><small>'+escapeHtml(p.width)+' × '+escapeHtml(p.height)+' pixels</small></div>').join("")+'</div>';
  else html+='<p class="muted">Nenhuma fotografia enviada.</p>';
  if(a.status!=="validated" && photos.length) {
    html+='<div class="assessment-card"><h3>Análise visual experimental</h3><p>Rascunho morfológico: não diagnostica nem substitui exame físico. Envio externo depende de autorização explícita.</p><label class="tiny"><input type="checkbox" id="vision-consent"> Confirmo autorização para processar externamente esta fotografia fictícia.</label><div class="review-actions"><button class="secondary-btn" id="analyze-photo" '+(state.findings.length?'disabled':'')+'>Gerar descrição preliminar</button></div><p class="tiny">Recurso desabilitado no servidor até configuração voluntária. Não usar imagens reais.</p></div>';
  }
  if(photos.length)html+='<div id="photo-quality"><h3>Qualidade técnica da fotografia</h3><p class="tiny">Indicadores experimentais; não atestam adequação clínica nem permitem medir cm².</p><button class="secondary-btn" id="check-photo-quality" type="button">Verificar imagem</button><div id="quality-results"></div></div>';
  if(a.status!=="validated")html+='<form id="photo-upload" class="photo-upload"><input type="file" name="image" accept="image/jpeg,image/png,image/webp" aria-label="Selecionar fotografia" required><button class="secondary-btn" type="submit">Adicionar fotografia</button></form>';
  el.innerHTML=html;
  renderClinicalSection(a,el).catch(e=>notice("Falha ao carregar anamnese: "+e.message,true));
  $("check-photo-quality")?.addEventListener("click",async()=>{
    const output=$("quality-results");output.textContent="Analisando a qualidade técnica...";
    try{
      const reports=await Promise.all(photos.map(p=>api("/photos/"+encodeURIComponent(p.id)+"/quality")));
      output.innerHTML=reports.map((q,i)=>'<div class="assessment-card"><strong>Fotografia '+(i+1)+'</strong><p>Resolução: '+q.width+'×'+q.height+' · Brilho: '+q.brightness_mean+' · Contraste: '+q.brightness_std+'</p>'+(q.warnings.length?'<ul>'+q.warnings.map(w=>'<li>'+escapeHtml(w)+'</li>').join("")+'</ul>':'<p>Nenhum alerta técnico detectado pelas regras experimentais.</p>')+'<p class="tiny">Mensuração quantitativa não autorizada; método de calibração não validado.</p></div>').join("");
    }catch(e){output.textContent=e.message;}
  });
  $("photo-upload")?.addEventListener("submit",async(ev)=>{
    ev.preventDefault();
    const form=new FormData(ev.currentTarget);
    try{
      const uploaded=await api("/assessments/"+encodeURIComponent(a.id)+"/photos",{method:"POST",body:form});
      await renderReview();
      const warn=uploaded.quality?.warnings?.length ? " Alertas de qualidade: "+uploaded.quality.warnings.join(" ") : "";
      notice("Fotografia criptografada e vinculada à avaliação."+warn,!!warn);
    }catch(e){notice(e.message,true);}
  });
  $("analyze-photo")?.addEventListener("click",async()=>{
    if(!$("vision-consent").checked)return notice("Confirme o envio externo antes de analisar.",true);
    const btn=$("analyze-photo");
    btn.disabled=true;btn.textContent="Analisando...";
    try {
      const result=await api("/assessments/"+encodeURIComponent(a.id)+"/analyze-image?photo_id="+encodeURIComponent(photos[0].id)+"&confirm_external_processing=true",{method:"POST"});
      await renderReview();
      notice(result.needs_better_image?"Imagem limitada: "+result.capture_guidance:"Rascunho visual gerado. Revise cada achado.");
    }catch(e){notice(e.message,true);btn.disabled=false;btn.textContent="Gerar descrição preliminar";}
  });
  $("add-finding")?.addEventListener("click",()=>modalFinding(a.id));
  $("finalize-assessment")?.addEventListener("click",async()=>{const reviewer=window.prompt("Identificação do revisor (apenas fictícia neste protótipo):","REVISOR-TESTE");if(!reviewer?.trim())return;try{await api("/assessments/"+encodeURIComponent(a.id)+"/finalize?reviewer="+encodeURIComponent(reviewer.trim()),{method:"POST"});await reload("Avaliação finalizada.");}catch(e){notice(e.message,true);}});
}
async function renderTrends(){
 const c=$("content");if(!state.lesions.length){c.innerHTML='<section class="panel">'+empty("Nenhuma lesão cadastrada","Crie uma lesão para visualizar tendências.")+'</section>';return;}
 c.innerHTML='<section class="panel"><div class="filters"><div class="form-group"><label for="trend-lesion">Selecionar lesão</label><select id="trend-lesion">'+selectOptions(state.lesions,state.selectedLesion,l=>l.location+" · "+patientName(l.patient_id))+'</select></div></div><div id="trend-content">Carregando...</div></section>';
 $("trend-lesion").addEventListener("change",ev=>{state.selectedLesion=ev.target.value;renderTrends().catch(e=>notice(e.message,true));});
 const lesionId=state.selectedLesion;
 const assessments=state.assessments.filter(a=>a.lesion_id===lesionId);
 const photoLists=await Promise.all(assessments.map(a=>api("/assessments/"+encodeURIComponent(a.id)+"/photos")));
 const photoChoices=photoLists.flatMap((photos,i)=>photos.map(p=>({id:p.id,assessment_id:assessments[i].id,at:assessments[i].captured_at}))).sort((a,b)=>new Date(a.at)-new Date(b.at));
 const comparables=photoChoices.length>1 ? '<div class="assessment-card"><h3>Comparação de fotografias (experimental)</h3><p class="tiny">Compara apenas metadados e indicadores de qualidade. Não realiza alinhamento espacial ou medição de área.</p><div class="filters"><div class="form-group"><label for="photo-prev">Anterior</label><select id="photo-prev">'+photoChoices.map(p=>'<option value="'+escapeHtml(p.id)+'">'+date(p.at)+'</option>').join("")+'</select></div><div class="form-group"><label for="photo-current">Atual</label><select id="photo-current">'+photoChoices.map(p=>'<option value="'+escapeHtml(p.id)+'">'+date(p.at)+'</option>').join("")+'</select></div></div><button class="secondary-btn" id="compare-photo">Verificar comparabilidade</button><div id="compare-result" aria-live="polite"></div></div>' : '<p class="tiny">Adicione fotografias a duas avaliações diferentes para verificar a comparabilidade técnica.</p>';
 $("trend-content").insertAdjacentHTML("afterend",'<div id="comparison-content">'+comparables+'</div>');
 if(photoChoices.length>1){
   $("photo-prev").value=photoChoices[0].id;
   $("photo-current").value=photoChoices[photoChoices.length-1].id;
   $("compare-photo").addEventListener("click",async()=>{
      const output=$("compare-result");output.textContent="Verificando...";
      try{
        const result=await api("/photos/"+encodeURIComponent($("photo-current").value)+"/compare/"+encodeURIComponent($("photo-prev").value));
        output.innerHTML='<p class="muted">'+escapeHtml(result.interpretation)+'</p><p class="tiny">Dimensões iguais: '+(result.same_pixel_dimensions?'sim':'não')+'. Comparação quantitativa autorizada: não.</p>';
      }catch(e){output.textContent=e.message;}
   });
 }
 const trends=await api("/lesions/"+encodeURIComponent(state.selectedLesion)+"/trend");
 const measured=trends.filter(t=>t.area_cm2!==null);
 $("comparison-content").insertAdjacentHTML("afterend", '<section class="panel" id="clinical-timeline"></section>');
 renderClinicalTimeline(lesionId).catch(e=>notice("Falha ao carregar linha do tempo: "+e.message,true));
 $("trend-content").innerHTML=measured.length?'<div class="panel-header"><h2>Evolução da área registrada</h2><span class="tiny">Somente avaliações validadas</span></div><div class="bar-chart">'+measured.map(t=>{const max=Math.max(...measured.map(x=>x.area_cm2),1);return '<div class="bar-group"><div class="bar-value">'+escapeHtml(t.area_cm2)+' cm²</div><div class="bar" style="height:'+Math.max(3,Math.round(t.area_cm2/max*155))+'px"></div><div class="bar-label">'+date(t.captured_at)+'</div></div>';}).join("")+'</div><p class="muted">Variação desde a primeira área válida: '+escapeHtml(measured.at(-1).change_from_baseline_percent)+'%. Os números são descritivos, não constituem interpretação clínica nem confirmação de resposta terapêutica.</p>':empty("Sem medições validadas","Registre a área e finalize ao menos uma avaliação.");
}
function modal(title,fields,onSave){
 $("modal-title").textContent=title;$("modal-fields").innerHTML=fields;$("modal").hidden=false;
 $("modal-form").onsubmit=async ev=>{ev.preventDefault();const submit=$("modal-form").querySelector('[type="submit"]');submit.disabled=true;try{await onSave(new FormData(ev.currentTarget));closeModal();await reload("Registro salvo com sucesso.");}catch(e){notice(e.message,true);}finally{submit.disabled=false;}};
 $("modal").querySelector("input,select,textarea")?.focus();
}
function closeModal(){$("modal").hidden=true;$("modal-form").onsubmit=null;}
function field(name,label,type="text",required=true,extra=""){return '<div class="form-group"><label for="form-'+name+'">'+label+'</label><input id="form-'+name+'" name="'+name+'" type="'+type+'" '+(required?"required":"")+' '+extra+' /></div>';}
function modalPatient(){modal("Novo paciente fictício",field("pseudonym","Identificador pseudonimizado","text",true,'maxlength="80" placeholder="EXEMPLO-001"'),fd=>api("/patients",{method:"POST",body:JSON.stringify({pseudonym:fd.get("pseudonym")})}));}
function modalLesion(){
 if(!state.patients.length)return notice("Cadastre um paciente fictício antes de criar uma lesão.",true);
 const options=selectOptions(state.patients,state.selectedPatient,p=>p.pseudonym);
 modal("Nova lesão",'<div class="form-group"><label for="form-patient">Paciente</label><select id="form-patient" name="patient_id">'+options+'</select></div>'+field("location","Localização anatômica","text",true,'maxlength="180" placeholder="Ex.: face medial da perna"')+field("etiology","Etiologia (se conhecida)","text",false,'maxlength="120"'),fd=>api("/lesions",{method:"POST",body:JSON.stringify({patient_id:fd.get("patient_id"),location:fd.get("location"),etiology:fd.get("etiology")||null})}));
}
function modalAssessment(){
 if(!state.lesions.length)return notice("Cadastre uma lesão antes de criar uma avaliação.",true);
 modal("Nova avaliação",'<div class="form-group"><label for="form-lesion">Lesão</label><select id="form-lesion" name="lesion_id">'+selectOptions(state.lesions,state.selectedLesion,l=>l.location+" · "+patientName(l.patient_id))+'</select></div>'+field("area","Área (cm²), opcional","number",false,'min="0" step="any" placeholder="Ex.: 12.5"')+field("method","Método de mensuração, se houver","text",false,'placeholder="Ex.: planimetria manual"')+'<div class="form-group"><label for="form-notes">Anotações</label><textarea id="form-notes" name="notes" maxlength="2000" placeholder="Somente dados fictícios"></textarea></div>',async fd=>{const area=fd.get("area");const body={lesion_id:fd.get("lesion_id"),area_cm2:area===""?null:Number(area),area_method:fd.get("method")||null,notes:fd.get("notes")||null};const a=await api("/assessments",{method:"POST",body:JSON.stringify(body)});state.selectedAssessment=a.id;state.selectedLesion=a.lesion_id;state.view="assessments";});
}
function modalFinding(id){modal("Adicionar achado",field("field_name","Campo semiológico","text",true,'placeholder="Ex.: bordas"')+'<div class="form-group"><label for="form-text">Descrição proposta</label><textarea id="form-text" name="proposed_text" required></textarea></div><div class="form-group"><label for="form-source">Origem</label><select id="form-source" name="source"><option value="exam">Exame informado</option><option value="reported">Relato</option><option value="image">Imagem</option><option value="unknown">Desconhecido</option></select></div><div class="form-group"><label for="form-support">Sustentação</label><select id="form-support" name="support"><option value="high">Alta</option><option value="limited">Limitada</option><option value="not_evaluable">Não avaliável</option></select></div>',fd=>api("/assessments/"+encodeURIComponent(id)+"/findings",{method:"POST",body:JSON.stringify(Object.fromEntries(fd))}));}
async function reload(message){await load();setView(state.view);if(message)notice(message);}
document.addEventListener("click",async ev=>{
 const go=ev.target.closest("[data-go]");if(go)return setView(go.dataset.go);
 const patient=ev.target.closest("[data-patient]");if(patient){state.selectedPatient=patient.dataset.patient;return setView("lesions");}
 const lesion=ev.target.closest("[data-lesion]");if(lesion){state.selectedLesion=lesion.dataset.lesion;state.selectedAssessment="";return setView("assessments");}
 const assessment=ev.target.closest("[data-assessment]");if(assessment){state.selectedAssessment=assessment.dataset.assessment;state.selectedLesion=state.assessments.find(a=>a.id===state.selectedAssessment)?.lesion_id||"";setView("assessments");return;}
 const review=ev.target.closest("[data-review]");if(review){const decision=review.dataset.decision;let corrected_text=null;if(decision==="corrected"){corrected_text=window.prompt("Texto corrigido e verificado:");if(!corrected_text?.trim())return;}const reviewer=window.prompt("Identificação fictícia do revisor:","REVISOR-TESTE");if(!reviewer?.trim())return;try{await api("/findings/"+encodeURIComponent(review.dataset.review)+"/review",{method:"POST",body:JSON.stringify({decision,reviewer:reviewer.trim(),corrected_text})});await reload("Achado revisado.");}catch(e){notice(e.message,true);}}
});
document.querySelectorAll("[data-view]").forEach(el=>el.addEventListener("click",()=>setView(el.dataset.view)));
$("close-modal").onclick=closeModal;$("cancel-modal").onclick=closeModal;
$("modal").addEventListener("click",e=>{if(e.target===$("modal"))closeModal();});
document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!$("modal").hidden)closeModal();});
function showLogin(error=""){
  $("login-screen").hidden=false;
  $("login-error").hidden=!error;
  $("login-error").textContent=error;
  $("login-password").focus();
}
async function start(){
  try{
    const session=await api("/auth/session");
    csrfToken=session.csrf;
    $("login-screen").hidden=true;
    await load();
    setView("dashboard");
  }catch(e){
    if(e.message.includes("Autenticação"))showLogin();
    else {showLogin("Não foi possível conectar ao servidor: "+e.message);}
  }
}
$("login-form").addEventListener("submit",async(ev)=>{
  ev.preventDefault();
  try{
    const response=await api("/auth/login",{method:"POST",body:JSON.stringify({password:$("login-password").value})});
    csrfToken=response.csrf;
    $("login-password").value="";
    $("login-screen").hidden=true;
    await load();
    setView("dashboard");
  }catch(e){showLogin(e.message);}
});
$("logout-button").addEventListener("click",async()=>{
  try{await api("/auth/logout",{method:"POST"});}catch(e){}
  csrfToken="";
  state.patients=[];state.lesions=[];state.assessments=[];state.findings=[];
  $("content").replaceChildren();
  showLogin();
});
start();
