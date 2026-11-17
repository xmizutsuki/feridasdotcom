"use strict";
/* Local bibliographic research. No patient data sent outside this application. */
async function renderEvidenceLibrary(parent,assessmentId){
  if(!parent?.isConnected)return;
  const section=document.createElement("section");
  section.className="clinical-section";
  section.id="evidence-library";
  section.innerHTML='<div class="panel-header"><h2>Biblioteca científica</h2><span class="tiny">Catálogo local · experimental</span></div><p class="muted">Consultando fontes...</p>';
  parent.append(section);
  try{
    const catalog=await api("/evidence/catalog");
    if(!section.isConnected)return;
    section.innerHTML='<div class="panel-header"><h2>Biblioteca científica</h2><span class="tiny">Pesquisa de trechos registrados</span></div>'+
      '<p class="muted">Fontes oficiais identificadas. Trechos precisam ser conferidos no documento original e sua recuperação não valida condutas.</p>'+
      '<div class="assessment-card"><strong>Fontes cadastradas</strong><ul>'+catalog.sources.map(s=>
        '<li><a href="'+escapeHtml(s.url)+'" target="_blank" rel="noopener noreferrer">'+escapeHtml(s.title)+'</a> · '+escapeHtml(s.edition)+
        ' · catálogo (sem evidência clínica verificada)</li>').join("")+'</ul></div>'+
      '<div class="assessment-card"><h3>Pesquisar trechos</h3><form id="evidence-search"><div class="form-group"><label for="evidence-query">Termos para busca local</label><input id="evidence-query" name="query" maxlength="180" minlength="2" required placeholder="Ex.: offloading, infection, compression"></div><button class="secondary-btn" type="submit">Pesquisar</button></form><div id="evidence-results" aria-live="polite"></div></div>'+
      '<div class="assessment-card"><h3>Trechos candidatos para esta avaliação</h3><p class="tiny">Busca orientada exclusivamente por informações relatadas na anamnese atual, sem inferir diagnóstico.</p><button class="secondary-btn" type="button" id="evidence-candidates">Consultar candidatos</button><div id="candidate-results" aria-live="polite"></div></div>'+
      '<button class="secondary-btn" type="button" id="add-evidence">Registrar trecho conferido</button>'+
      '<p class="tiny">Este módulo não produz diagnóstico diferencial nem recomenda tratamento. A correspondência lexical não implica indicação para a lesão avaliada.</p>';
    $("evidence-search")?.addEventListener("submit",async e=>{
      e.preventDefault();
      const output=$("evidence-results");output.textContent="Pesquisando...";
      try {
        const q=String(new FormData(e.currentTarget).get("query")||"").trim();
        const results=await api("/evidence/search?q="+encodeURIComponent(q));
        output.innerHTML=results.matches.length?results.matches.map(m=>
          '<div class="assessment-card"><strong>'+escapeHtml(m.publisher_title)+'</strong><p>'+escapeHtml(m.passage.excerpt)+'</p>'+
          '<p class="tiny">Localização: '+escapeHtml(m.passage.source_location)+' · Conferido por: '+escapeHtml(m.passage.reviewed_by)+
          ' · Termos em comum: '+m.lexical_score+'</p><a href="'+escapeHtml(m.publisher_url)+'" target="_blank" rel="noopener noreferrer">Abrir documento da editora</a>'+
          '<p class="tiny">Não é uma recomendação para o caso; confira o texto original e a aplicabilidade.</p></div>').join("") :
          '<p class="muted">Nenhum trecho cadastrado corresponde aos termos. Não interpretar ausência de resultados como ausência de evidência científica.</p>';
      }catch(e){output.textContent=e.message;}
    });
    $("evidence-candidates")?.addEventListener("click",async()=>{
      const output=$("candidate-results");output.textContent="Procurando trechos candidatos...";
      try {
        const result=await api("/evidence/assessments/"+encodeURIComponent(assessmentId)+"/candidates");
        const topics=result.search_topics_from_explicit_reported_data;
        output.innerHTML='<p class="tiny">Temas de busca: '+(topics.length?topics.map(escapeHtml).join(", "):"nenhum tema inferível de dados explícitos")+'</p>'+
          (result.matches.length?result.matches.map(m=>
            '<div class="assessment-card"><strong>'+escapeHtml(m.publisher_title)+'</strong><p>'+escapeHtml(m.passage.excerpt)+'</p>'+
            '<p class="tiny">Localização registrada: '+escapeHtml(m.passage.source_location)+'</p>'+
            '<a href="'+escapeHtml(m.publisher_url)+'" target="_blank" rel="noopener noreferrer">Abrir fonte</a></div>').join(""):
            '<p class="muted">Sem trechos correspondentes cadastrados. Isso não significa ausência de evidência ou ausência de risco.</p>')+
          '<p class="tiny">Aplicabilidade clínica não validada. Nenhuma conduta foi gerada.</p>';
      }catch(e){output.textContent=e.message;}
    });
    $("add-evidence")?.addEventListener("click",()=>openEvidenceForm(catalog.sources));
  }catch(e){section.textContent="Biblioteca indisponível: "+e.message;}
}
function openEvidenceForm(sources){
  const fields='<p class="tiny">Registre apenas pequenos trechos cuja localização você conferiu pessoalmente no documento original. Não invente referências nem transcreva materiais extensos protegidos por direitos autorais.</p>'+
    '<div class="form-group"><label for="src-doc">Fonte oficial</label><select id="src-doc" name="catalog_source_id">'+
      sources.map(s=>'<option value="'+escapeHtml(s.id)+'">'+escapeHtml(s.title)+'</option>').join("")+'</select></div>'+
    field("source_location","Localização exata: seção/página/recomendação","text",true,'maxlength="160" placeholder="Ex.: página 12, recomendação 3"')+
    '<div class="form-group"><label for="src-excerpt">Trecho curto do original</label><textarea id="src-excerpt" name="excerpt" minlength="20" maxlength="350" required placeholder="Texto curto, literalmente conferido"></textarea></div>'+
    '<div class="form-group"><label for="src-language">Idioma</label><select id="src-language" name="language"><option value="en">Inglês</option><option value="pt">Português</option><option value="es">Espanhol</option></select></div>'+
    '<div class="form-group"><label for="src-topic">Tópico (tags separadas por vírgulas)</label><input id="src-topic" name="topic_tags" required placeholder="Ex.: diabetic_foot, offloading"></div>'+
    '<div class="form-group"><label for="src-note">Limitações e população de aplicação (opcional)</label><textarea id="src-note" name="applicability_notes" maxlength="600"></textarea></div>'+
    field("reviewed_by","Identificação fictícia de quem conferiu","text",true,'maxlength="100" placeholder="REVISOR-TESTE"')+
    '<label class="clinical-confirm"><input type="checkbox" name="confirmation" required> Eu conferi o trecho no documento original e sua localização. Não afirmo que ele seja aplicável ao paciente.</label>';
  modal("Registrar trecho científico",fields,fd=>{
    const topicTags=String(fd.get("topic_tags")||"").split(",").map(s=>s.trim()).filter(Boolean);
    return api("/evidence/passages",{method:"POST",body:JSON.stringify({
      catalog_source_id:fd.get("catalog_source_id"),source_location:fd.get("source_location"),
      excerpt:fd.get("excerpt"),language:fd.get("language"),topic_tags:topicTags,
      applicability_notes:fd.get("applicability_notes")||null,reviewed_by:fd.get("reviewed_by"),
      confirmation:fd.get("confirmation")==="on"?"verified_in_original_document":""
    })});
  });
}
