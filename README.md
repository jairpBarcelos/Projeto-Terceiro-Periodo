# SAADI - Sistema de Acompanhamento da Educação Inclusiva

<p align="center">
	<img src="img/icons8-two-hands-48%20(1).png" alt="Logo SAADI" width="96">
</p>

O SAADI é uma plataforma web para organizar informações escolares de alunos com deficiência e apoiar o trabalho de equipes pedagógicas, psicopedagógicas e administrativas.

O projeto centraliza cadastros, acompanha encaminhamentos, registra relatórios e facilita a tomada de decisão na rotina escolar, contribuindo para um atendimento mais organizado e inclusivo.

## Sumário

- [Problema](#problema)
- [Proposta](#proposta)
- [Funcionalidades](#funcionalidades)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar](#como-executar)
- [Acessibilidade](#acessibilidade)
- [Licença](#licença)

## Problema

Muitas instituições ainda lidam com informações dispersas, processos manuais e pouca visibilidade sobre o histórico dos alunos que precisam de acompanhamento especializado. Isso dificulta a comunicação entre setores e reduz a eficiência no planejamento das ações pedagógicas.

## Proposta

O SAADI reduz essa fragmentação por meio de uma interface simples, padronizada e focada na gestão de dados escolares. A plataforma apoia o registro e a consulta de informações essenciais para o acompanhamento dos alunos ao longo do ano letivo.

## Funcionalidades

- Autenticação de acesso para perfis institucionais.
- Menus separados por área de atuação.
- Cadastro, atualização, listagem e exclusão de alunos, usuários e unidades.
- Controle de encaminhamentos e relatórios.
- Área específica para psicopedagogia e secretaria escolar.

## Estrutura do repositório

- `index.html`: página inicial de acesso.
- `css/`: estilos globais e específicos de cada módulo.
- `img/`: imagens e ícones do sistema.
- `pages/auth/`: telas de autenticação.
- `pages/menus/administrador/`: área administrativa.
- `pages/menus/psicopedagogo/`: área do psicopedagogo.
- `pages/menus/secretaria/`: área da secretaria escolar.
- `scripts/`: scripts JavaScript da aplicação.

## Como executar

Como o projeto é composto por páginas HTML, CSS e JavaScript, ele pode ser aberto em qualquer servidor estático local. A forma mais simples é usar uma extensão como Live Server no VS Code ou servir a pasta com qualquer servidor web local.

## Banco de dados (PostgreSQL)

O projeto inclui um bootstrap de banco para facilitar o setup em qualquer PC.

1. Copie `.env.example` para `.env` e ajuste os dados de conexão.
2. Garanta que o PostgreSQL esteja ativo.
3. Rode o script:

```bash
python scripts/bootstrap_db.py
```

O script:

- Cria o banco configurado em `PGDATABASE` (se nao existir).
- Aplica o schema em `db/schema.sql`.
- Aplica dados iniciais em `db/seed.sql`.

## Acessibilidade

- Algumas páginas já incluem integração com VLibras.
- A navegação foi pensada para manter uma estrutura simples e consistente.

## Licença

Este projeto está sob a licença definida em [LICENSE](LICENSE).