# Guia para o TI — Habilitar Service Principal no Power BI (UMOE OS)

**Solicitante:** Andrei Elastico (Diretoria Agrícola)
**Objetivo:** Permitir que uma automação leia dados do Power BI **sem depender do login de um usuário** (hoje a automação funciona, mas usa o login pessoal e exige re-autenticação periódica).

> O app já existe, está habilitado e autentica. **Não é preciso criar nada.** Falta apenas (1) ligar uma configuração de tenant e (2) dar acesso de leitura aos 2 workspaces.

---

## Dados do Service Principal (já criado)
| Item | Valor |
|---|---|
| Nome (Enterprise App) | **UMOE-OS-BI-Agent** |
| Application (client) ID | `2097df94-2d5f-4381-ab0e-1388d37456a8` |
| Tenant (Directory) ID | `aca5c8c2-df2c-4cda-91c1-23eb0017d8cd` |
| Status | accountEnabled = True (verificado) |

---

## Pré-requisito de permissão
Quem executa este guia precisa ter o papel **Administrador do Fabric** (ou **Administrador do Power BI**, ou **Administrador Global** do Microsoft 365). O solicitante é admin de **capacidade**, que **não** dá acesso a estas telas.

---

## PARTE 1 — Habilitar entidades de serviço no tenant (uma vez)

1. Acesse **https://app.powerbi.com**
2. Canto superior direito → **⚙️ (Configurações)** → **Portal de administração**
3. Menu esquerdo → **Configurações do locatário** (Tenant settings)
4. No campo de busca, digite: **entidades de serviço** (ou "service principals")
5. Abra a configuração **"Permitir que entidades de serviço usem APIs do Power BI"**
   (em inglês: *Allow service principals to use Power BI APIs*, na seção **Developer settings**)
6. Mude para **Habilitado** (Enabled)
7. Em **"Aplicar a"**, escolha **uma** das opções:
   - **Toda a organização** (mais simples), **ou**
   - **Grupos de segurança específicos** → neste caso, **adicione o app `UMOE-OS-BI-Agent` a esse grupo de segurança** (no Entra ID / Azure AD). Sem isso, o SP continua sem acesso mesmo após o passo 2.
8. Clique em **Aplicar**
9. **Aguarde até ~15 minutos** para a configuração propagar

> ⚠️ Observação de segurança: esta configuração permite que *service principals* usem as APIs de leitura do Power BI. O acesso a **dados específicos** continua controlado workspace a workspace (Parte 2). Não expõe nada além do que for explicitamente compartilhado.

---

## PARTE 2 — Dar acesso de leitura aos 2 workspaces (após propagar)

Para **cada** workspace abaixo:

1. **https://app.powerbi.com** → menu esquerdo **Áreas de trabalho** → abra o workspace
2. No topo, **Gerenciar acesso** (ou ⋯ → Gerenciar acesso)
3. **+ Adicionar pessoas ou grupos**
4. Digite **`UMOE-OS-BI-Agent`** → o app deve **aparecer** na lista (se não aparecer, a Parte 1 ainda não propagou)
5. Selecione o app → função **Membro** (Member) — *Viewer/Visualizador também serve se preferirem mínimo privilégio, desde que permita executeQueries*
6. **Adicionar** → confirme que o app ficou listado

| Workspace | ID |
|---|---|
| **Projetos Agrícola PREMIUM** | `662a06b5-5579-4af6-b66a-7ac191a96674` |
| **Projetos Manutenção PREMIUM** | `954ecb3e-1daf-4a98-8801-39f2026da2d8` |

---

## Como validar (rápido)
Após concluir, o SP deve **enxergar os 2 workspaces** via API. O solicitante consegue confirmar rodando um teste do lado dele (a automação passa a listar os workspaces em vez de "0").

Sinais de sucesso:
- No passo 4 da Parte 2, o `UMOE-OS-BI-Agent` **aparece** na busca (prova que a Parte 1 propagou).
- O app fica **listado** no "Gerenciar acesso" de cada workspace como Membro.

---

## Resumo do que muda
- **Não** cria app novo, **não** mexe em senhas, **não** expõe dados novos.
- Apenas: liga a config de tenant + compartilha leitura de 2 workspaces com um app já existente.
- Resultado: a automação da Diretoria roda 100% sozinha, sem depender de login pessoal.

Dúvidas técnicas: o solicitante pode validar o acesso imediatamente após a configuração.
