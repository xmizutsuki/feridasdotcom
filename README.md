# feridasdotcom

Prontuário longitudinal de lesões e suporte à segunda opinião clínica (em desenvolvimento).

> **Estado:** protótipo técnico não validado clinicamente. Não utilizar para decisões assistenciais nem inserir dados reais de pacientes até concluir segurança, governança e validação.

A primeira entrega implementará cadastro de pacientes pseudonimizados, lesões, avaliações, achados revisáveis, auditabilidade e testes.

Documentação e instruções serão adicionadas na branch de implementação.


## Demonstração web pelo GitHub Pages

Foi adicionada uma interface de demonstração totalmente estática em `docs/index.html`. A publicação automática é feita pela Action `.github/workflows/deploy-pages.yml` a cada alteração relevante na branch `main`.

**Primeira ativação (exige administrador no GitHub):** abra [Settings → Pages](https://github.com/xmizutsuki/feridasdotcom/settings/pages) e, em **Build and deployment → Source**, selecione **GitHub Actions**. Depois, na aba [Actions](https://github.com/xmizutsuki/feridasdotcom/actions/workflows/deploy-pages.yml), execute novamente **Publish Feridas.com Demo (GitHub Pages)** usando *Run workflow* (branch `main`).

Quando o workflow concluir com sucesso, a demo deverá ficar em `https://xmizutsuki.github.io/feridasdotcom/`.

**Limitação:** GitHub Pages publica apenas HTML/CSS/JS. Não executa a API FastAPI, não guarda avaliações, não oferece autenticação de usuários, banco de dados ou IA. Os dados nesta demo são inventados e não há armazenamento. O backend completo permanece na branch `feat/clinical-core-mvp` no PR #1 e requer uma hospedagem de aplicação separada, segurança e governança antes de uso real.
