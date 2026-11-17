"use strict";
/* PDF evidence ingestion interface. Only synthetic/licensed PDFs; no medical advice. */
async function renderDocumentEvidence(parent,catalogSources){
 if(!parent?.isConnected)return;
 const section=document.createElement("section");
 section.className="clinical-section";
 section.id="pdf-document-review";
 parent.append(section);
 const docs=await api("/evidence/documents");
 if(!section.isConnected)return;
 let html='<div class="panel-header"><h2>Documentos PDF e citações</h2><span class="tiny">Conferência textual por página</span></div>'+
 '<p class="muted">Envie apenas PDFs de teste ou documentos cujo processamento seja autorizado. O sistema confere a presença literal do trecho no PDF carregado; não verifica se a fonte é autêntica nem se o conteúdo se aplica a um paciente.</p>'+
 '<form id="evidence-pdf-upload" class="assessment-card">'+
 '<div class="form-group"><label for="pdf-source">Fonte do catálogo</label><select id="pdf-source" name="source_id">'+catalogSources.map(s=>'<option value="'+escapeHtml(s.id)+'">'+escapeHtml(s.title)+'</option>').join("")+'</select></div>'+
 '<div class="form-group"><label for="pdf-edition">Edição/versão do arquivo</label><input id="pdf-edition" name="edition_label" maxlength="100" required placeholder="Ex.: documento sintético de teste"></div>'+
 '<div class="form-group"><label for="pdf-file">PDF autorizado (até 6 MB e 100 páginas)</label><input id="pdf-file" type="file" name="file" accept="application/pdf,.pdf" required></div>'+
 '<button class="secondary-btn" type="submit">Adicionar PDF criptografado</button></form>';
 if(docs.length){
   html+='<div class="assessment-card"><h3>Conferir trecho no original</h3>'+
   '<form id="pdf-quote-check"><div class="form-group"><label for="pdf-document">Documento carregado</label><select id="pdf-document" name="document_id">'+docs.map(d=>'<option value="'+escapeHtml(d.id)+'">'+escapeHtml(d.edition_label)+' · '+escapeHtml(d.source_id)+'</option>').join("")+'</select></div>'+
   '<div class="form-group"><label for="pdf-page">Página física do PDF (a partir de 1)</label><input type="number" id="pdf-page" name="page_number" min="1" max="100" required></div>'+
   '<div class="form-group"><label for="pdf-excerpt">Citação literal</label><textarea id="pdf-excerpt" name="excerpt" minlength="20" maxlength="500" required placeholder="Copie um trecho curto exatamente como aparece no texto extraído"></textarea></div>'+
   '<div class="form-group"><label for="pdf-checker">Identificação do verificador (fictícia)</label><input id="pdf-checker" name="checked_by" maxlength="100" required></div>'+
   '<button class="secondary-btn" type="submit">Verificar correspondência na página</button></form>'+
   '<p class="tiny">O texto precisa estar extraível. PDFs digitalizados sem texto ainda exigem conferência manual; sem OCR automático nesta etapa.</p></div>';
 } else html+='<p class="tiny">Nenhum documento enviado. A biblioteca ainda não possui citações verificadas contra páginas de PDF.</p>';
 html+='<div id="pdf-action-result" aria-live="polite"></div>';
 section.innerHTML=html;
 $("evidence-pdf-upload")?.addEventListener("submit",async e=>{
   e.preventDefault();const fd=new FormData(e.currentTarget);
   const source=String(fd.get("source_id")||"");const edition=String(fd.get("edition_label")||"");
   const file=fd.get("file");const payload=new FormData();payload.append("file",file);
   try{
     const result=await api("/evidence/documents?source_id="+encodeURIComponent(source)+"&edition_label="+encodeURIComponent(edition),{method:"POST",body:payload});
     notice("PDF de teste cadastrado com "+result.page_count+" página(s). O conteúdo e a autenticidade ainda não foram validados.");
     await renderDocumentEvidence(parent,catalogSources);
     section.remove();
   }catch(error){$("pdf-action-result").textContent=error.message;}
 });
 $("pdf-quote-check")?.addEventListener("submit",async e=>{
   e.preventDefault();const fd=new FormData(e.currentTarget);const id=String(fd.get("document_id"));
   try{
     const result=await api("/evidence/documents/"+encodeURIComponent(id)+"/verify-quote",{method:"POST",body:JSON.stringify({
       page_number:Number(fd.get("page_number")),excerpt:String(fd.get("excerpt")),
       checked_by:String(fd.get("checked_by"))
     })});
     $("pdf-action-result").textContent="Correspondência textual encontrada na página "+result.page_number+". Referência "+result.id+". Não significa adequação clínica.";
   }catch(error){$("pdf-action-result").textContent=error.message;}
 });
}
