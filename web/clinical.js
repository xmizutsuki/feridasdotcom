"use strict";
/* Structured assessment extension. All displayed values are HTML escaped.
   This interface only accepts synthetic data. */
const HISTORY_FIELDS = [
  ["onset_days","Tempo de evolução (dias)","number"],
  ["pain_score","Dor relatada (0 a 10)","number"],
  ["pain_worsening","Dor em piora","tri"],
  ["fever_reported","Febre relatada","tri"],
  ["rapidly_worsening","Piora rápida da lesão","tri"],
  ["spreading_redness","Eritema em expansão (informado)","tri"],
  ["purulent_drainage_reported","Drenagem purulenta relatada","tri"],
  ["malodor_reported","Odor relatado","tri"],
  ["exudate_amount","Quantidade de exsudato (exame/relato)","choice",["none","low","moderate","high","unknown"]],
  ["perfusion_exam","Avaliação de perfusão","choice",["not_assessed","no_concern_reported","concern_reported"]],
  ["diabetes_reported","Diabetes informado","tri"],
  ["pressure_offloading","Medidas de alívio de pressão","choice",["yes","no","unknown","not_applicable"]],
  ["compression_used","Compressão em uso","choice",["yes","no","unknown","not_applicable"]],
  ["allergies","Alergias informadas","text"],
  ["comorbidities","Comorbidades informadas","text"],
  ["current_medications","Medicações informadas","text"],
  ["context_notes","Observações complementares","text"]
];
const CLINICAL_LABELS = Object.fromEntries(HISTORY_FIELDS.map(f=>[f[0],f[1]]));
const CLINICAL_OPTIONS = {
  yes:"Sim",no:"Não",unknown:"Desconhecido",not_applicable:"Não se aplica",
  none:"Ausente",low:"Pequena",moderate:"Moderada",high:"Elevada",
  not_assessed:"Não examinada",no_concern_reported:"Sem alteração relatada",concern_reported:"Possível alteração relatada"
};
const readable = v => v===null||v===undefined||v===""?"Não registrado":typeof v==="boolean"?(v?"Sim":"Não"):(CLINICAL_OPTIONS[v]||String(v));
const selectHtml=(name,items)=>'<div class="form-group"><label for="ch-'+name+'">'+escapeHtml(CLINICAL_LABELS[name])+'</label><select name="'+name+'" id="ch-'+name+'"><option value="">Não avaliado / sem registro</option>'+items.map(x=>'<option value="'+escapeHtml(x)+'">'+escapeHtml(readable(x))+'</option>').join("")+'</select></div>';
function historyFieldHtml([name,label,type,options]){
 if(type==="tri")return '<div class="form-group"><label for="ch-'+name+'">'+escapeHtml(label)+'</label><select name="'+name+'" id="ch-'+name+'"><option value="">Não avaliado / desconhecido</option><option value="true">Sim</option><option value="false">Não</option></select></div>';
 if(type==="choice")return selectHtml(name,options);
 if(type==="number")return '<div class="form-group"><label for="ch-'+name+'">'+escapeHtml(label)+'</label><input type="number" name="'+name+'" id="ch-'+name+'" min="0" max="'+(name==="pain_score"?10:36500)+'" placeholder="Não avaliado"></div>';
 return '<div class="form-group"><label for="ch-'+name+'">'+escapeHtml(label)+'</label><textarea name="'+name+'" id="ch-'+name+'" maxlength="'+(name==="context_notes"?2000:1000)+'" placeholder="Não registrado"></textarea></div>';
}
function historyPayload(fd){
 const body={reporter:fd.get("reporter"),recorder_id:String(fd.get("recorder_id")||"").trim(),human_confirmed:fd.get("human_confirmed")==="on"};
 for(const [name,,type] of HISTORY_FIELDS){
   const value=fd.get(name);
   body[name] = value===null || String(value).trim()==="" ? null : type==="number"?Number(value):type==="tri"?value==="true":String(value).trim();
 }
 return body;
}
function renderHistorySnapshot(item){
 let lines=Object.entries(item.data).filter(([,v])=>v!==null&&v!=="").map(([k,v])=>'<tr><td>'+escapeHtml(CLINICAL_LABELS[k]||k)+'</td><td>'+escapeHtml(readable(v))+'</td></tr>');
 const alerts=(item.alerts||[]).map(a=>'<div class="clinical-warning"><strong>'+escapeHtml(a.priority==="urgent_review"?"Revisão urgente":"Reavaliação")+'</strong><p>'+escapeHtml(a.message)+'</p></div>').join("");
 return '<div class="assessment-card"><p class="tiny">Revisão '+item.revision+' · '+date(item.recorded_at)+' · Origem: '+escapeHtml(item.reporter)+' · Registrado por '+escapeHtml(item.recorder_id)+'</p>'+alerts+table(["Informação","Registro"],lines)+'</div>';
}
async function renderClinicalSection(assessment,element){
 const id=encodeURIComponent(assessment.id);
 const [history,interventions,previous]=await Promise.all([
   api("/assessments/"+id+"/history"),
   api("/assessments/"+id+"/interventions"),
   api("/assessments/"+id+"/previous-history")
 ]);
 if(state.selectedAssessment!==assessment.id || !element.isConnected)return;
 const latest=history.at(-1);
 let html='<section class="clinical-section"><div class="panel-header"><h2>Anamnese e exame clínico</h2><span class="tiny">Dados declarados · revisão humana</span></div>';
 if(previous?.data)html+='<div class="history-banner">Há anamnese anterior de '+date(previous.source_captured_at)+'. É apenas referência histórica, não confirmação atual.</div>';
 html+=latest?renderHistorySnapshot(latest):'<p class="muted">Nenhuma anamnese registrada nesta avaliação. Campos ausentes não significam achados negativos.</p>';
 if(history.length>1)html+='<details><summary>Consultar revisões anteriores ('+(history.length-1)+')</summary>'+history.slice(0,-1).reverse().map(renderHistorySnapshot).join("")+'</details>';
 if(assessment.status!=="validated")html+='<button class="secondary-btn" type="button" id="history-new">'+(latest?"Registrar nova revisão":"Preencher anamnese")+'</button>';
 html+='</section><section class="clinical-section"><div class="panel-header"><h2>Condutas e intervenções</h2><span class="tiny">Planejado ≠ realizado</span></div>';
 html+=interventions.length?table(["Tipo","Situação","Descrição","Registro"],interventions.map(x=>'<tr><td>'+escapeHtml(x.type)+'</td><td>'+escapeHtml(x.status)+'</td><td>'+escapeHtml(x.description)+'</td><td>'+date(x.recorded_at)+'</td></tr>')):'<p class="muted">Nenhuma intervenção registrada. A ausência de registro não demonstra ausência de tratamento.</p>';
 if(assessment.status!=="validated")html+='<button class="secondary-btn" type="button" id="intervention-new">+ Registrar intervenção</button>';
 html+='</section>';
 const region=document.createElement("div");
 region.id="clinical-region";region.innerHTML=html;
 element.append(region);
 renderSecondOpinionContext(assessment.id,region).catch(e=>notice("Falha ao carregar o contexto: "+e.message,true));
 $("history-new")?.addEventListener("click",()=>openHistoryForm(assessment.id));
 $("intervention-new")?.addEventListener("click",()=>openInterventionForm(assessment.id));
}
function openHistoryForm(assessmentId){
 const fields='<p class="tiny">Preencha apenas achados obtidos por relato ou exame. Deixe sem resposta o que não foi avaliado.</p><div class="form-two-columns">'+HISTORY_FIELDS.map(historyFieldHtml).join("")+'</div>'+
 '<div class="form-group"><label>Origem das informações</label><select name="reporter"><option value="professional">Exame / profissional</option><option value="patient">Paciente</option><option value="caregiver">Cuidador</option><option value="record_review">Prontuário anterior</option></select></div>'+
 field("recorder_id","Identificação do registrador (fictícia)","text",true,'maxlength="100" placeholder="PROF-TESTE"')+
 '<label class="clinical-confirm"><input type="checkbox" name="human_confirmed" required> Confirmo que revisei os dados informados; informações não preenchidas permanecem desconhecidas.</label>';
 modal("Anamnese estruturada",fields,fd=>api("/assessments/"+encodeURIComponent(assessmentId)+"/history",{method:"POST",body:JSON.stringify(historyPayload(fd))}));
}
function openInterventionForm(assessmentId){
 const types=["cleansing","dressing","offloading","compression","debridement","referral","other"];
 const fields='<div class="form-group"><label>Tipo</label><select name="type">'+types.map(x=>'<option value="'+x+'">'+x+'</option>').join("")+'</select></div>'+
 '<div class="form-group"><label>Situação</label><select name="status" id="int-status"><option value="planned">Planejada</option><option value="performed">Realizada</option><option value="not_performed">Não realizada</option></select></div>'+
 '<div class="form-group"><label>Descrição factual da intervenção</label><textarea name="description" required minlength="3" maxlength="2000"></textarea></div>'+
 '<div class="form-group"><label>Data/hora, se realizada</label><input name="performed_at" type="datetime-local"></div>'+
 '<div class="form-group"><label>Observações</label><textarea name="notes" maxlength="1000"></textarea></div>'+
 field("recorder_id","Identificação do registrador (fictícia)","text",true,'maxlength="100" placeholder="PROF-TESTE"')+
 '<label class="clinical-confirm"><input type="checkbox" name="human_confirmed" required> Confirmo que o registro corresponde ao que foi planejado ou realizado.</label>';
 modal("Registro de intervenção",fields,fd=>{
   const performed=fd.get("status")==="performed";
   const raw=fd.get("performed_at");
   if(performed&&!raw)throw Error("Informe data/hora da intervenção realizada.");
   return api("/assessments/"+encodeURIComponent(assessmentId)+"/interventions",{method:"POST",body:JSON.stringify({
     type:fd.get("type"),status:fd.get("status"),description:String(fd.get("description")).trim(),
     notes:fd.get("notes")||null,recorder_id:fd.get("recorder_id"),human_confirmed:fd.get("human_confirmed")==="on",
     performed_at:performed?new Date(raw).toISOString():null
   })});
 });
}

async function renderClinicalTimeline(lesionId){
 const host=$("clinical-timeline");
 if(!host)return;
 const rows=await api("/lesions/"+encodeURIComponent(lesionId)+"/clinical-timeline");
 if(!host.isConnected||state.selectedLesion!==lesionId)return;
 host.innerHTML='<div class="panel-header"><h2>Linha do tempo clínica</h2><span class="tiny">Dados registrados, sem interpretação automatizada</span></div>'+
 (rows.length?rows.map(item=>{
   const data=item.history?.data||{};
   const alerts=item.history?.alerts||[];
   return '<div class="assessment-card"><strong>'+date(item.captured_at)+' · '+escapeHtml(item.assessment_status)+'</strong>'+
   '<p class="tiny">Dor: '+escapeHtml(readable(data.pain_score))+' · Febre relatada: '+escapeHtml(readable(data.fever_reported))+' · Exsudato: '+escapeHtml(readable(data.exudate_amount))+'</p>'+
   '<p class="tiny">Intervenções registradas: '+item.interventions.length+' · Avisos: '+alerts.length+'</p>'+
   alerts.map(a=>'<div class="clinical-warning">'+escapeHtml(a.message)+'</div>').join("")+
   (item.interventions.length?'<p class="tiny">'+item.interventions.map(x=>escapeHtml(x.type)+': '+escapeHtml(x.status)).join(' | ')+'</p>':'')+
   '</div>';
 }).join(""):empty("Sem histórico clínico","Registre anamnese e intervenções nas avaliações."));
}
