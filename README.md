# SAADI - Sistema de Acompanhamento da Educação Inclusiva

<p align="center">
	<img src="frontend/assets/icons8-two-hands-48%20(1).png" alt="Logo SAADI" width="96">
</p>

O SAADI é uma plataforma web premium para organizar informações escolares de alunos com deficiência e apoiar de forma integrada o trabalho de equipes pedagógicas, psicopedagógicas e administrativas.

O projeto centraliza cadastros de alunos, acompanha encaminhamentos de forma multi-tenant, registra relatórios técnicos, planos de atendimento especializados e facilita a tomada de decisão na rotina escolar, contribuindo para um atendimento mais organizado, seguro e inclusivo.

---

## 📌 Sumário

- [Problema](#problema)
- [Proposta](#proposta)
- [Funcionalidades e Módulos](#funcionalidades-e-módulos)
- [Tecnologias e Arquitetura](#tecnologias-e-arquitetura)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Guia de Execução Local](#guia-de-execução-local)
- [Acessibilidade WCAG 2.1 AA](#acessibilidade-wcag-21-aa)
- [Equipe e Licença](#equipe-e-licença)

---

## 🔍 Problema

Muitas instituições ainda lidam com informações dispersas, processos manuais e pouca visibilidade sobre o histórico dos alunos que precisam de acompanhamento especializado. A falta de isolamento seguro e de centralização dificulta a comunicação entre setores (Secretaria e Psicopedagogia) e reduz a eficiência no planejamento das ações pedagógicas inclusivas.

## 🎯 Proposta

O SAADI unifica essas pontas por meio de uma interface simples, responsiva e focada na gestão de dados escolares seguros. A plataforma apoia o registro, controle de acesso estrito baseados na escola logada (multi-tenant) e a consulta rápida ao histórico evolutivo de cada estudante ao longo do ano letivo.

---

## 🚀 Funcionalidades e Módulos

### 🏫 1. Área Administrativa (Central)
- Cadastro de Unidades Escolares (escolas parceiras do município).
- Cadastro e gerenciamento de perfis de acesso (`administrador`, `secretaria`, `psicopedagogo`).
- Painel de auditoria do sistema em tempo real.
- Relatórios consolidados de neurodiversidade e abrangência de atendimento.

### 📩 2. Secretaria Escolar (Local)
- Cadastro, edição e listagem de alunos da respectiva unidade.
- **Módulo de Encaminhamentos:** Solicitação de atendimento especializado para o Psicopedagogo daquela escola, descrevendo motivos e observações.
- Acompanhamento em tempo real do status do encaminhamento e recebimento de retornos técnicos direto do painel.

### 🧠 3. Psicopedagogia (Local)
- **Painel de Indicadores Unificados:** Casos ativos, triagens pendentes, planos de acompanhamento, atendimentos do dia e encaminhamentos em aberto.
- **Módulo de Triagem:** Ficha técnica de evolução e registro de entrevistas com o estudante.
- **Planos de Acompanhamento:** Elaboração de estratégias metodológicas de inclusão personalizada.
- **Relatórios Técnicos:** Emissão de laudos e pareceres clínicos pedagógicos.
- **Linha do Tempo (Timeline):** Consulta ao histórico integrado de ações aplicadas àquele aluno ao longo do tempo.

---

## 🛠️ Tecnologias e Arquitetura

O sistema foi estruturado seguindo os melhores padrões de engenharia:
- **Frontend:** HTML5 semântico, CSS3 (Vanilla para melhor fidelidade de design) e JavaScript ES6.
- **Backend:** Flask (Python 3.10+), SQLAlchemy (ORM), Flask-Migrate (controle de versionamento do banco).
- **Banco de Dados:** PostgreSQL para armazenamento persistente seguro.
- **Segurança:** Autenticação baseada em **Cookies HttpOnly** e controle multi-tenant estrito por `unidade_id` nos bastidores.

---

## 📂 Estrutura do Repositório

```
Projeto-Terceiro-Periodo/
├── backend/                  # Código-fonte Flask (Serviços e Rotas)
│   ├── routes/               # Blueprints e Handlers HTTP por Módulo
│   ├── services/             # Lógica de Negócio e Consultas SQLAlchemy
│   ├── models.py             # Mapeamento de Tabelas do Banco de Dados
│   └── security.py           # Decorators de autenticação JWT/HttpOnly
├── db/                       # Bootstrap do banco (SQL e seeds)
├── frontend/                 # Arquivos da interface Web
│   ├── css/                  # Estilos visuais modernos
│   ├── js/                   # Controladores dinâmicos e apiClient.js
│   └── pages/                # Estruturas HTML segregadas por perfil
├── schemas/                  # Contratos de validação de dados Pydantic
└── requirements.txt          # Dependências Python do projeto
```

---

## 💻 Guia de Execução Local

### 1. Clonar e Instalar Dependências
Instale os pacotes do backend listados no `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e ajuste as credenciais de acesso ao seu banco de dados PostgreSQL local:
```env
PGHOST=localhost
PGPORT=5432
PGDATABASE=saadi_db
PGUSER=postgres
PGPASSWORD=suasenha
SECRET_KEY=sua_chave_secreta_aqui
JWT_SECRET_KEY=sua_chave_secreta_jwt_aqui
```

### 3. Inicializar e Popular o Banco
O projeto possui um script inteligente para criar o banco de dados e aplicar o schema completo junto com dados fictícios para testes:
```bash
python scripts/bootstrap_db.py
```

Se desejar utilizar as migrações padrão do Flask-Migrate:
```bash
flask --app run db init
flask --app run db migrate -m "migracao inicial"
flask --app run db upgrade
```

### 4. Iniciar o Servidor
Execute a aplicação principal:
```bash
python run.py
```
O servidor estará ativo em `http://localhost:5000` (o frontend será servido automaticamente na rota raiz `/`).

---

## ♿ Acessibilidade WCAG 2.1 AA

O SAADI orgulha-se de ser um sistema **totalmente acessível**, desenvolvido sob as diretrizes de conformidade da **WCAG 2.1 Nível AA**:
- Navegação lógica e intuitiva 100% controlada via teclado (`Tab`, `Shift+Tab`, `Enter`, `Space`).
- Foco visual extremamente perceptível em cor ouro contrastante em todos os elementos selecionados.
- Tags de acessibilidade para leitores de tela (`aria-label`, `aria-live`, `aria-describedby`).
- Adaptabilidade responsiva (Reflow) com suporte a zoom de até 200% sem perda de dados.
- Correção de usabilidade para modais de formulário longos, garantindo rolagem nativa fluida em telas de menor resolução.

Para mais detalhes e guia de testes práticos, consulte o arquivo [ACESSIBILIDADE.md](ACESSIBILIDADE.md).

---

## 👥 Equipe e Licença

### Desenvolvedores:
- Jair Pereira Barcelos
- Lucas Fontan Fernandes

### Licença:
Este projeto está sob a licença de software definida no arquivo [LICENSE](LICENSE).