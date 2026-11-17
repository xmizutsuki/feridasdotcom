# Feridas.com

Aplicativo experimental de acompanhamento longitudinal de feridas e suporte à revisão profissional. **Não validado para cuidado de pacientes nem para armazenamento de dados reais.**

## Experimente a interface real (modo demonstração)

**[Abrir Feridas.com — demonstração no GitHub Pages](https://xmizutsuki.github.io/feridasdotcom/)**

O site do GitHub Pages reutiliza o **frontend real** desenvolvido na branch `feat/clinical-core-mvp`: mesmo layout, navegação, revisão de achados, anamnese, intervenções, linha do tempo e painéis de referências. Um adaptador de API (`docs/demo-api.js`) injeta casos inteiramente fictícios e permite exercitar parte dos formulários e revisões **apenas em memória**. Os dados são perdidos ao recarregar a página.

**Não é o aplicativo completo:** GitHub Pages não executa FastAPI, banco de dados, autenticação real, criptografia de fotos, upload de PDF/fotos nem modelos de IA. Esses recursos exigem backend hospedado separadamente, segurança institucional e validação clínica. O ambiente de demonstração não envia dados ao servidor, salvo a navegação voluntária para sites externos de diretrizes.

**Para publicar:** abra [Settings → Pages](https://github.com/xmizutsuki/feridasdotcom/settings/pages) e selecione **GitHub Actions** como origem. O workflow `.github/workflows/deploy-pages.yml` publica a pasta `docs/` automaticamente; `.github/workflows/demo-check.yml` verifica sintaxe dos arquivos JavaScript e exercita os fluxos sintéticos. A execução de cada workflow pode ser conferida em [Actions](https://github.com/xmizutsuki/feridasdotcom/actions).

## Backend e desenvolvimento

A implementação da API e dos módulos clínicos experimentais está na branch `feat/clinical-core-mvp` e no [Pull Request #1](https://github.com/xmizutsuki/feridasdotcom/pull/1), mantido em rascunho. Leia as instruções e limites de segurança no README da própria branch.

**Não use este software para decisões assistenciais nem forneça dados de pacientes reais.**
