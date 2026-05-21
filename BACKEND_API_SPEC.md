# Especificação Completa da API Backend - SAADI

Este documento serve como a **Especificação de Referência Técnica** para a API REST do sistema SAADI. Ele detalha a segurança de autenticação, o tratamento de erros padronizado, a arquitetura multi-tenant de isolamento escolar e todos os endpoints ativos.

---

## 🔒 1. Arquitetura de Segurança e Autenticação

A API do SAADI opera de forma **Cookie-Based** para sessões web, utilizando **Tokens JWT seguros**. 

### Cookies Seguros
Ao realizar o login, o servidor injeta os seguintes cookies no navegador do cliente:
*   `access_token_cookie`: Token JWT de curta duração para autorizar requisições normais de API.
*   `refresh_token_cookie`: Token JWT de longa duração para renovação automática de sessão.

Ambos os cookies possuem as flags:
*   `HttpOnly`: Impede leitura via Javascript, mitigando ataques de roubo de sessão por XSS.
*   `Secure`: Exige tráfego via HTTPS em produção.
*   `SameSite=Lax`: Protege contra ataques de CSRF (Cross-Site Request Forgery).

### Cabeçalhos Requeridos para API Clientes (ex: Scripts)
Embora o navegador envie os cookies automaticamente, requisições diretas de API também podem enviar o token JWT através do cabeçalho de autorização padrão:
```http
Authorization: Bearer {JWT_TOKEN}
```

---

## 🏢 2. Arquitetura Multi-Tenant (Isolamento Escolar)

O sistema SAADI implementa um **isolamento de dados multi-tenant estrito no nível do banco de dados**, baseado no vínculo dos usuários e alunos com as unidades escolares (`unidade_id`).

### Regras de Negócio Multi-Tenant:
1.  **Perfil Administrador (`administrador`):** Tem visão centralizada. Pode ler, cadastrar e alterar dados de todas as escolas do sistema (`unidade_id` é opcional ou omitido).
2.  **Perfis da Secretaria (`secretaria`) e Psicopedagogia (`psicopedagogo`):** Têm acesso restrito à sua respectiva escola. O backend extrai a claim `unidade_id` inserida no JWT do usuário logado e injeta esse filtro silenciosamente em todas as consultas SQL (SELECT, INSERT, UPDATE, DELETE).
3.  **Encaminhamentos:** Um encaminhamento feito pela secretaria de uma escola só aparecerá no painel de psicopedagogos que pertençam à **mesma escola**, garantindo que não haja vazamento de dados de alunos entre unidades escolares distintas.

---

## ⚠️ 3. Padrão de Resposta de Erros

A API responde de forma padronizada a falhas em formato JSON:

```json
{
  "status": "error",
  "message": "Mensagem descritiva do erro legível para o usuário.",
  "code": "CODIGO_DO_ERRO",
  "details": null
}
```

### Códigos de Erro Comuns:
*   `VALIDATION_ERROR` (HTTP 400): Dados de entrada inválidos ou falha de esquema.
*   `UNAUTHORIZED` (HTTP 401): Token JWT ausente, inválido ou expirado.
*   `FORBIDDEN` (HTTP 403): Tentativa de acesso a recurso de outro tenant ou perfil insuficiente.
*   `NOT_FOUND` (HTTP 404): Registro não encontrado.
*   `CONFLICT` (HTTP 409): CPF ou Matrícula já cadastrados no banco.
*   `INTERNAL_SERVER_ERROR` (HTTP 500): Falha inesperada no servidor.

---

## 🌐 4. Catálogo de Endpoints e Blueprints

---

### 🔑 4.1. Módulo de Autenticação (`/api/auth`)

#### **POST /api/auth/login**
Valida credenciais e injeta cookies de sessão seguros.
*   **Payload (JSON):**
    ```json
    {
      "email": "psico@escola.edu.br",
      "senha": "SenhaSegura123"
    }
    ```
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Autenticado com sucesso.",
      "data": {
        "user": {
          "id": 5,
          "nome_completo": "Ana Paula Silva",
          "perfil": "psicopedagogo",
          "unidade_id": 2
        },
        "redirect_url": "/pages/menus/psicopedagogo/painelPsicopedagogo.html"
      }
    }
    ```

#### **POST /api/auth/logout**
Limpa os cookies de sessão segura do navegador.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Logout realizado com sucesso."
    }
    ```

#### **POST /api/auth/refresh**
Gera um novo `access_token` a partir do `refresh_token` armazenado em cookie.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Sessão renovada."
    }
    ```

---

### 🏫 4.2. Módulo Administrativo: Unidades (`/api/admin/unidades`)

#### **GET /api/admin/unidades**
Lista as unidades escolares com paginação e busca.
*   **Query Params:** `page`, `limit`, `busca`
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "items": [
          {
            "id": 2,
            "nome": "E.M. Inclusiva Jardim",
            "cnpj": "12.345.678/0002-00",
            "cidade": "Belo Horizonte",
            "estado": "MG",
            "status": "ativa"
          }
        ],
        "total": 1,
        "pagina": 1,
        "limite": 20,
        "totalPaginas": 1
      }
    }
    ```

#### **POST /api/admin/unidades**
Cadastra uma nova unidade. (Apenas Admin)
*   **Payload (JSON):**
    ```json
    {
      "nome": "E.M. Inclusiva Jardim",
      "cnpj": "12.345.678/0002-00",
      "cidade": "Belo Horizonte",
      "estado": "MG"
    }
    ```
*   **Resposta de Sucesso (201 Created):**
    ```json
    {
      "status": "success",
      "message": "Unidade criada com sucesso.",
      "data": { "id": 2 }
    }
    ```

---

### 👥 4.3. Módulo Administrativo: Usuários (`/api/admin/usuarios`)

#### **GET /api/admin/usuarios**
Lista usuários do sistema com filtros avançados.
*   **Query Params:** `page`, `limit`, `busca`, `perfil`, `unidade_id`
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "items": [
          {
            "id": 5,
            "nome_completo": "Ana Paula Silva",
            "email": "psico@escola.edu.br",
            "perfil_nome": "psicopedagogo",
            "unidade_id": 2,
            "status": "ativo"
          }
        ],
        "total": 1,
        "pagina": 1,
        "limite": 10
      }
    }
    ```

#### **POST /api/admin/usuarios**
Cria um novo usuário administrativo ou escolar.
*   **Payload (JSON):**
    ```json
    {
      "nome_completo": "Ana Paula Silva",
      "email": "psico@escola.edu.br",
      "perfil": "psicopedagogo",
      "unidade_id": 2,
      "senha": "SenhaSuperSegura"
    }
    ```

#### **DELETE /api/admin/usuarios/<id>**
Exclui permanentemente um usuário.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Usuário deletado com sucesso."
    }
    ```

---

### 📊 4.4. Módulo de Estatísticas & Auditoria (`/api/admin`)

#### **GET /api/admin/dashboard**
Retorna as contagens globais para o Painel do Administrador.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "totalUnidades": 14,
        "usuariosAtivos": 32,
        "configuracoesPendentes": 2,
        "alertaSeguranca": 0
      }
    }
    ```

#### **GET /api/admin/atividades-recentes**
Retorna as últimas auditorias do banco de dados (ex: login, exclusões).
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "items": [
          {
            "data": "2026-05-21T13:45:00Z",
            "nomeUsuario": "Ana Paula Silva",
            "acao": "Cadastro de Triagem",
            "entidade": "Pedro Rocha",
            "status": "Sucesso"
          }
        ]
      }
    }
    ```

#### **GET /api/admin/status-sistema**
Fornece métricas de integridade de banco de dados PostgreSQL e armazenamento.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "bancoDados": { "status": "OK", "descricao": "Conexão ativa e estável" },
        "armazenamento": { "percentualUso": 12, "descricao": "Espaço suficiente" }
      }
    }
    ```

---

### 🎓 4.5. Módulo de Alunos (`/api/alunos`)

#### **GET /api/alunos**
Retorna alunos com base na escola logada (ou centralizados se admin).
*   **Query Params:** `page`, `limit`, `q`, `unidade_id`, `status`
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "items": [
          {
            "id": 12,
            "nome": "Pedro Rocha",
            "cpf": "123.456.789-00",
            "matricula": "MAT2026-004",
            "serie": "3º Ano A",
            "status": "ativo",
            "unidade_id": 2
          }
        ],
        "total": 1,
        "pagina": 1,
        "limite": 20
      }
    }
    ```

#### **POST /api/alunos**
Cadastra um novo aluno. Valida CPFs repetidos.
*   **Payload (JSON):**
    ```json
    {
      "nome": "Pedro Rocha",
      "cpf": "123.456.789-00",
      "matricula": "MAT2026-004",
      "serie": "3º Ano A",
      "unidade_id": 2
    }
    ```

#### **DELETE /api/alunos/<id>**
Exclusão lógica do aluno (Soft Delete), mudando o status para `inativo`.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "message": "Aluno removido com sucesso (soft delete)."
    }
    ```

#### **GET /api/alunos/historico/<id>**
Retorna a linha do tempo (timeline) completa de eventos psicopedagógicos e pedagógicos do aluno.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "historico": [
          {
            "tipo": "encaminhamento",
            "data": "2026-05-20T10:00:00Z",
            "descricao": "Encaminhado pela secretaria para atendimento Psicopedagógico.",
            "autor": "Mariana Souza (Secretária)"
          },
          {
            "tipo": "triagem",
            "data": "2026-05-21T11:30:00Z",
            "descricao": "Entrevista de triagem realizada com o aluno.",
            "autor": "Ana Paula Silva (Psicopedagoga)"
          }
        ]
      }
    }
    ```

---

### 📩 4.6. Módulo de Encaminhamentos (`/api/encaminhamentos`)
Utilizado pela Secretaria para enviar alunos à Psicopedagogia e receber retornos.

#### **GET /api/encaminhamentos/dashboard**
Traz dados rápidos do andamento dos encaminhamentos na unidade logada.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "total": 10,
        "abertos": 3,
        "em_atendimento": 5,
        "resolvidos": 2
      }
    }
    ```

#### **GET /api/encaminhamentos**
Lista os encaminhamentos. Aplica o filtro de tenant escolar de forma estrita.
*   **Query Params:** `status`, `q`, `page`, `limit`
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "items": [
          {
            "id": 1,
            "aluno": { "id": 12, "nome": "Pedro Rocha" },
            "solicitante": { "id": 4, "nome_completo": "Mariana Souza" },
            "motivo": "Dificuldades de aprendizado e concentração.",
            "status": "aberto",
            "data_criacao": "2026-05-21T10:30:00Z"
          }
        ]
      }
    }
    ```

#### **POST /api/encaminhamentos**
Cadastra um encaminhamento direcionado ao psicopedagogo.
*   **Payload (JSON):**
    ```json
    {
      "aluno_id": 12,
      "motivo": "Indícios fortes de dislexia ou dificuldades de letramento rápido.",
      "observacoes": "Família está ciente e concorda.",
      "urgente": true
    }
    ```

#### **POST /api/encaminhamentos/<id>/retorno**
Registrado pelo Psicopedagogo ao dar um fechamento ou parecer sobre a triagem. Atualiza o status para `resolvido`.
*   **Payload (JSON):**
    ```json
    {
      "parecer_tecnico": "O aluno Pedro Rocha passará a ser acompanhado individualmente às terças-feiras no contraturno escolar.",
      "data_retorno": "2026-05-21"
    }
    ```

---

### 📝 4.7. Módulo de Triagens & Evoluções (`/api/triagens`)

#### **GET /api/triagens/alunos-select**
Lista os alunos ativos vinculados à escola, ideal para preencher dropdowns/selects de modais.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "alunos": [
          { "id": 12, "nome": "Pedro Rocha" }
        ]
      }
    }
    ```

#### **POST /api/triagens**
Cadastra uma ficha de triagem ou registro de evolução técnica.
*   **Payload (JSON):**
    ```json
    {
      "aluno_id": 12,
      "motivo_triagem": "Falta de foco nas avaliações regulares.",
      "data_registro": "2026-05-21",
      "encaminhado_por": "Secretária Mariana",
      "observacoes_gerais": "Apresenta nervosismo leve.",
      "status": "aguardando_entrevista"
    }
    ```

---

### 📘 4.8. Módulo de Planos de Acompanhamento (`/api/planos`)

#### **POST /api/planos**
Emite um Plano de Acompanhamento Especializado.
*   **Payload (JSON):**
    ```json
    {
      "aluno_id": 12,
      "objetivos": "Aumentar a compreensão leitora e atenção sustentada.",
      "metodologia": "Uso de recursos visuais táteis e leituras assistidas.",
      "frequencia_semanal": 2,
      "status": "ativo"
    }
    ```

---

### 📁 4.9. Módulo de Relatórios Técnicos e Pareceres (`/api/relatorios`)

#### **POST /api/relatorios**
Registra um laudo, parecer pedagógico ou relatório conclusivo de acompanhamento.
*   **Payload (JSON):**
    ```json
    {
      "aluno_id": 12,
      "titulo": "Parecer Clínico Trimestral - Pedro Rocha",
      "conteudo": "Pedro demonstrou evolução satisfatória na identificação de grafemas simples.",
      "status": "finalizado"
    }
    ```

---

### 🎯 4.10. Painel Geral do Psicopedagogo (`/api/psicopedagogo`)

#### **GET /api/psicopedagogo/dashboard**
Provê todos os indicadores numéricos unificados exigidos no dashboard do psicopedagogo.
*   **Resposta (200 OK):**
    ```json
    {
      "status": "success",
      "data": {
        "casos_ativos": 5,
        "triagens_pendentes": 2,
        "planos_ativos": 3,
        "atendimentos_hoje": 1,
        "encaminhamentos_abertos": 3
      }
    }
    ```
