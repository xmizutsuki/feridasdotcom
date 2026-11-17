"use strict";
/**
 * Feridas.com standalone demo adapter.
 * Reproduces the real frontend contracts using a per-tab, in-memory synthetic
 * dataset. No server, external model, persistence, authentication, or patient data.
 * ALL fetch calls are handled locally. Refreshing resets the demo.
 */
(() => {
  const day = n => new Date(Date.UTC(2026, 9, 20+n, 12)).toISOString();
  const uid = () => "demo-"+Math.random().toString(36).slice(2,11);
  const patients=[
    {id:"p1",pseudonym:"EXEMPLO-001",created_at:day(1)},
    {id:"p2",pseudonym:"EXEMPLO-002",created_at:day(2)},
    {id:"p3",pseudonym:"EXEMPLO-003",created_at:day(4)}
  ];
  const lesions=[
    {id:"l1",patient_id:"p1",location:"Perna esquerda — cenário fictício",etiology:null,opened_at:day(1)},
    {id:"l2",patient_id:"p2",location:"Região sacral — cenário fictício",etiology:null,opened_at:day(2)},
    {id:"l3",patient_id:"p3",location:"Região plantar — cenário fictício",etiology:null,opened_at:day(4)}
  ];
  const assessments=[
    {id:"a1",lesion_id:"l1",captured_at:day(2),area_cm2:8.4,area_method:"Exemplo fictício (não mensurado)",notes:"Registro sintético",status:"validated"},
    {id:"a2",lesion_id:"l1",captured_at:day(9),area_cm2:7.2,area_method:"Exemplo fictício (não mensurado)",notes:"Segunda avaliação simulada",status:"validated"},
    {id:"a3",lesion_id:"l2",captured_at:day(5),area_cm2:null,area_method:null,notes:"Avaliação para revisão",status:"draft"},
    {id:"a4",lesion_id:"l3",captured_at:day(6),area_cm2:null,area_method:null,notes:"Outro cenário",status:"draft"}
  ];
  const findings=[
    {id:"f1",assessment_id:"a1",field_name:"edges",proposed_text:"Bordas descritas apenas para simulação.",source:"exam",support:"limited",validation_status:"confirmed",validated_text:"Bordas descritas apenas para simulação.",reviewed_by:"REVISOR-FICTICIO",reviewed_at:day(2)},
    {id:"f2",assessment_id:"a2",field_name:"periwound",proposed_text:"Descrição fictícia da pele perilesional.",source:"exam",support:"limited",validation_status:"corrected",validated_text:"Pele perilesional descrita em cenário inventado.",reviewed_by:"REVISOR-FICTICIO",reviewed_at:day(9)},
    {id:"f3",assessment_id:"a3",field_name:"wound_bed",proposed_text:"Leito de ferida fictício; avaliar demonstração.",source:"exam",support:"limited",validation_status:"pending",validated_text:null,reviewed_by:null,reviewed_at:null}
  ];
  const histories=[
    {id:"h1",assessment_id:"a1",revision:1,recorded_at:day(2),recorder_id:"REVISOR-FICTICIO",reporter:"professional",data:{pain_score:4,fever_reported:null,exudate_amount:"low",perfusion_exam:"not_assessed"},alerts:[],clinical_validation:false},
    {id:"h2",assessment_id:"a2",revision:1,recorded_at:day(9),recorder_id:"REVISOR-FICTICIO",reporter:"professional",data:{pain_score:2,fever_reported:false,exudate_amount:"low",perfusion_exam:"no_concern_reported"},alerts:[],clinical_validation:false}
  ];
  const interventions=[
    {id:"i1",assessment_id:"a1",type:"dressing",status:"planned",description:"Exemplo ilustrativo de registro, sem indicação clínica.",performed_at:null,recorder_id:"REVISOR-FICTICIO",recorded_at:day(2),notes:null},
    {id:"i2",assessment_id:"a2",type:"dressing",status:"performed",description:"Evento fictício para demonstrar histórico.",performed_at:day(9),recorder_id:"REVISOR-FICTICIO",recorded_at:day(9),notes:null}
  ];
  const photos=[];
  const sources=[
    {id:"iwgdf-2023-guidelines",title:"IWGDF — Diretrizes 2023",issuer:"IWGDF",edition:"2023",url:"https://iwgdfguidelines.org/guidelines-2023/",scope:["diabetic_foot"],verification_status:"publisher_page_identified"},
    {id:"iwgdf-2023-wound-healing",title:"IWGDF — Cicatrização 2023",issuer:"IWGDF",edition:"2023",url:"https://iwgdfguidelines.org/wound-healing-2023/",scope:["wound_healing"],verification_status:"publisher_page_identified"},
    {id:"sobest-library",title:"SOBEST — Biblioteca científica",issuer:"SOBEST",edition:"catálogo",url:"https://sobest.com.br/biblioteca/",scope:["wounds"],verification_status:"publisher_page_identified"}
  ];
  const passages=[];
  const documents=[];
  const results=[];
  const success=(body,status=200)=>new Response(JSON.stringify(body),{status,headers:{"Content-Type":"application/json"}});
  const fail=(detail,status=400)=>success({detail},status);
  const missing=()=>fail("Registro fictício não encontrado",404);
  const parse=opts=>{try{return JSON.parse(opts.body||"{}")}catch{return {}}};
  const getA=id=>assessments.find(a=>a.id===id);
  const now=()=>new Date().toISOString();
  function context(assessment) {
    const rows=findings.filter(f=>f.assessment_id===assessment.id);
    const observation=rows.filter(f=>["confirmed","corrected"].includes(f.validation_status)&&f.validated_text&&f.support!=="not_evaluable").map(f=>({
      field_name:f.field_name,text:f.validated_text,proposed_source:f.source,support_at_proposal:f.support,human_decision:f.validation_status,
      provenance:{assessment_id:assessment.id,record_id:f.id,recorded_at:f.reviewed_at,recorder_id:f.reviewed_by}
    }));
    const history=histories.filter(h=>h.assessment_id===assessment.id).at(-1);
    const data=history?Object.entries(history.data).filter(([k,v])=>v!==null&&v!==""&&v!=="unknown"&&v!=="not_assessed").map(([k,v])=>({
      field_name:k,value:v,reporter:history.reporter,provenance:{assessment_id:assessment.id,record_id:history.id,recorded_at:history.recorded_at,recorder_id:history.recorder_id}
    })):[];
    const current=interventions.filter(i=>i.assessment_id===assessment.id).map(i=>({
      type:i.type,status:i.status,description:i.description,performed_at:i.performed_at,
      provenance:{assessment_id:assessment.id,record_id:i.id,recorded_at:i.recorded_at,recorder_id:i.recorder_id}
    }));
    const gaps=[];
    if(!observation.length)gaps.push("semiologia_confirmada");
    if(!history)gaps.push("anamnese_atual_registrada");
    if(!current.length)gaps.push("intervencoes_registradas");
    gaps.push("validacao_especifica_da_area");
    return {schema_version:"context-v1",assessment_id:assessment.id,lesion_id:assessment.lesion_id,assessment_status:assessment.status,observations:observation,reported_clinical_data:data,interventions:current,warnings:history?.alerts||[],excluded_unreviewed_count:rows.filter(f=>f.validation_status==="pending").length,excluded_rejected_count:rows.filter(f=>f.validation_status==="rejected").length,not_evaluable_count:rows.filter(f=>f.support==="not_evaluable").length,history_revision:history?.revision||null,missing_sections:gaps,research_ready:false,recommendations_enabled:false,clinical_validation:false};
  }
  const clinicalWarnings=b=>{
    const warnings=[];
    if(b.rapidly_worsening===true)warnings.push({code:"rapid_deterioration",priority:"urgent_review",message:"Piora rápida relatada; em situação real é necessária avaliação clínica presencial.",triggered_by:["rapidly_worsening"]});
    if(b.perfusion_exam==="concern_reported")warnings.push({code:"perfusion_concern",priority:"urgent_review",message:"Possível alteração de perfusão; em caso real exige avaliação profissional.",triggered_by:["perfusion_exam"]});
    if(b.fever_reported===true&&(b.spreading_redness===true||b.purulent_drainage_reported===true))warnings.push({code:"systemic_local_warning",priority:"urgent_review",message:"Febre e alteração local relatadas; em caso real exige avaliação.",triggered_by:["fever_reported"]});
    return warnings;
  };
  async function route(raw,opts={}) {
    const url=new URL(raw,location.href);
    const path=url.pathname;
    const method=(opts.method||"GET").toUpperCase();
    const parts=path.split("/").filter(Boolean);
    const body=method==="GET"?{}:parse(opts);
    if(path==="/auth/session")return success({csrf:"DEMO-LOCAL",owner:"demo"});
    if(path==="/auth/login")return success({csrf:"DEMO-LOCAL"});
    if(path==="/auth/logout")return success({ok:true});
    if(path==="/patients"&&method==="GET")return success(patients);
    if(path==="/patients"&&method==="POST"){
      const name=String(body.pseudonym||"").trim();
      if(name.length<2||patients.some(p=>p.pseudonym===name))return fail("Use um identificador fictício diferente",422);
      const p={id:uid(),pseudonym:name,created_at:now()};patients.push(p);return success(p,201);
    }
    if(parts[0]==="patients"&&parts[2]==="lesions"&&method==="GET")
      return success(lesions.filter(l=>l.patient_id===parts[1]));
    if(path==="/lesions"&&method==="POST"){
      if(!patients.some(p=>p.id===body.patient_id))return missing();
      if(String(body.location||"").length<2)return fail("Localização fictícia obrigatória",422);
      const l={id:uid(),patient_id:body.patient_id,location:body.location,etiology:body.etiology||null,opened_at:now()};lesions.push(l);return success(l,201);
    }
    if(parts[0]==="lesions"&&parts[2]==="assessments"&&method==="GET")
      return success(assessments.filter(a=>a.lesion_id===parts[1]));
    if(path==="/assessments"&&method==="POST"){
      if(!lesions.some(l=>l.id===body.lesion_id))return missing();
      if(body.area_cm2!==null&&body.area_cm2!==undefined&&!body.area_method)return fail("Informe método da medida inventada",422);
      const a={id:uid(),lesion_id:body.lesion_id,captured_at:now(),area_cm2:body.area_cm2??null,area_method:body.area_method??null,notes:body.notes??null,status:"draft"};assessments.push(a);return success(a,201);
    }
    if(parts[0]==="assessments"&&parts[2]==="findings"){
      const a=getA(parts[1]);if(!a)return missing();
      if(method==="GET")return success(findings.filter(f=>f.assessment_id===a.id));
      if(a.status==="validated")return fail("Avaliação finalizada",409);
      const f={id:uid(),assessment_id:a.id,field_name:body.field_name,proposed_text:body.proposed_text,source:body.source,support:body.support,validation_status:"pending",validated_text:null,reviewed_by:null,reviewed_at:null};findings.push(f);return success(f,201);
    }
    if(parts[0]==="findings"&&parts[2]==="review"&&method==="POST"){
      const f=findings.find(x=>x.id===parts[1]);if(!f)return missing();
      if(getA(f.assessment_id)?.status==="validated"||f.validation_status!=="pending")return fail("Revisão não permitida",409);
      f.validation_status=body.decision;f.validated_text=body.decision==="confirmed"?f.proposed_text:body.decision==="corrected"?body.corrected_text:null;f.reviewed_at=now();f.reviewed_by=body.reviewer;return success(f);
    }
    if(parts[0]==="assessments"&&parts[2]==="finalize"&&method==="POST"){
      const a=getA(parts[1]);if(!a)return missing();
      const related=findings.filter(f=>f.assessment_id===a.id);
      if(!related.length||related.some(f=>f.validation_status==="pending"))return fail("Revise todos os achados antes de finalizar",422);
      a.status="validated";return success(a);
    }
    if(parts[0]==="assessments"&&parts[2]==="photos"){
      const a=getA(parts[1]);if(!a)return missing();
      if(method==="GET")return success(photos.filter(p=>p.assessment_id===a.id));
      return fail("O GitHub Pages não armazena fotografias. Use apenas a demonstração dos campos clínicos.",503);
    }
    if(parts[0]==="assessments"&&parts[2]==="history"){
      const a=getA(parts[1]);if(!a)return missing();
      if(method==="GET")return success(histories.filter(h=>h.assessment_id===a.id));
      if(a.status==="validated")return fail("Avaliação finalizada",409);
      if(!body.human_confirmed)return fail("Confirmação humana necessária",422);
      const data={...body};delete data.human_confirmed;delete data.reporter;delete data.recorder_id;
      if(!Object.values(data).some(v=>v!==null&&v!==""))return fail("Anamnese vazia",422);
      const h={id:uid(),assessment_id:a.id,revision:histories.filter(x=>x.assessment_id===a.id).length+1,recorded_at:now(),recorder_id:body.recorder_id,reporter:body.reporter,data,alerts:clinicalWarnings(body),clinical_validation:false};
      histories.push(h);return success(h,201);
    }
    if(parts[0]==="assessments"&&parts[2]==="previous-history"){
      const a=getA(parts[1]);if(!a)return missing();
      const older=assessments.filter(x=>x.lesion_id===a.lesion_id&&x.status==="validated"&&x.captured_at<a.captured_at).sort((x,y)=>y.captured_at.localeCompare(x.captured_at));
      for(const candidate of older){const h=histories.filter(x=>x.assessment_id===candidate.id).at(-1);if(h)return success({source_assessment_id:candidate.id,source_captured_at:candidate.captured_at,revision:h.revision,data:h.data,warning:"Apenas referência histórica; não confirmada na avaliação atual."});}
      return success({source_assessment_id:null,data:null,warning:"Sem histórico anterior"});
    }
    if(parts[0]==="assessments"&&parts[2]==="interventions"){
      const a=getA(parts[1]);if(!a)return missing();
      if(method==="GET")return success(interventions.filter(i=>i.assessment_id===a.id));
      if(a.status==="validated")return fail("Avaliação finalizada",409);
      if(body.status==="performed"&&!body.performed_at)return fail("Informe data/hora da execução",422);
      const i={id:uid(),assessment_id:a.id,type:body.type,status:body.status,description:body.description,performed_at:body.performed_at??null,recorder_id:body.recorder_id,recorded_at:now(),notes:body.notes??null};interventions.push(i);return success(i,201);
    }
    if(parts[0]==="assessments"&&parts[2]==="clinical-context"){
      const a=getA(parts[1]);return a?success(context(a)):missing();
    }
    if(parts[0]==="assessments"&&parts[2]==="evidence-readiness"){
      const a=getA(parts[1]);return a?success({context:context(a),sources:[],evidence_verified:false,reasoning_executed:false,differential_diagnoses:[],suggested_interventions:[],message:"Simulação sem análise científica ativa."}):missing();
    }
    if(parts[0]==="lesions"&&parts[2]==="interventions")return success(interventions.filter(i=>assessments.some(a=>a.id===i.assessment_id&&a.lesion_id===parts[1])));
    if(parts[0]==="lesions"&&parts[2]==="clinical-timeline"){
      const ass=assessments.filter(a=>a.lesion_id===parts[1]);
      return success(ass.map(a=>({assessment_id:a.id,captured_at:a.captured_at,assessment_status:a.status,history:histories.filter(h=>h.assessment_id===a.id).at(-1)||null,interventions:interventions.filter(i=>i.assessment_id===a.id),clinical_validation:false})));
    }
    if(parts[0]==="lesions"&&parts[2]==="trend"){
      const ass=assessments.filter(a=>a.lesion_id===parts[1]&&a.status==="validated").sort((a,b)=>a.captured_at.localeCompare(b.captured_at));
      const baseline=ass.find(a=>a.area_cm2>0)?.area_cm2;
      return success(ass.map(a=>({assessment_id:a.id,captured_at:a.captured_at,area_cm2:a.area_cm2,change_from_baseline_percent:baseline&&a.area_cm2!=null?Math.round((a.area_cm2-baseline)/baseline*10000)/100:null})));
    }
    if(path==="/evidence/catalog")return success({sources,content_verified:false,note:"Catálogo somente ilustrativo"});
    if(path==="/evidence/documents")return method==="GET"?success(documents):fail("Envio de PDF indisponível no GitHub Pages",503);
    if(path==="/evidence/passages"){
      if(method==="GET")return success(passages);
      return fail("Cadastro de referências desabilitado na demonstração estática",503);
    }
    if(path==="/evidence/search")return success({query:url.searchParams.get("q")||"",matches:[],retrieval_method:"local_lexical_v1",reasoning_executed:false,recommendations_enabled:false,message:"RAG desabilitado nesta demonstração"});
    if(parts[0]==="evidence"&&parts[1]==="assessments"&&parts[3]==="candidates")return success({assessment_id:parts[2],search_topics_from_explicit_reported_data:[],matches:[],clinical_applicability_validated:false,reasoning_executed:false,recommendations_enabled:false,message:"IA desabilitada na demo"});
    if(path==="/assessments/reasoning/status")return success({enabled:false,semantic_reviewer_enabled:false,synthetic_only:true,clinical_validation:false,therapeutic_recommendations_enabled:false});
    if(path.startsWith("/photos/")||path.includes("/analyze-image")||path.includes("/reasoning-draft")||path.includes("/audit-differential"))return fail("Recurso não executado no GitHub Pages. Este é um frontend de demonstração com dados fictícios.",503);
    return fail("Operação não suportada na demonstração estática: "+path,404);
  }
  window.fetch=(input,opts)=>Promise.resolve().then(()=>route(typeof input==="string"?input:input.url,opts));
  window.FERIDAS_DEMO=true;
})();
