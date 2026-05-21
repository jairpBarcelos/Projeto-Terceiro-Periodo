# Guia de Integração Frontend + Backend - SAADI

Este guia descreve os padrões técnicos de comunicação entre a interface (Frontend HTML/Vanilla JS) e o servidor (Backend Flask + PostgreSQL) do sistema SAADI, com foco em segurança, padronização de dados e tratamento automatizado de sessões.

---

## 🔒 1. Modelo de Segurança de Autenticação

O SAADI utiliza **Cookies HttpOnly** para armazenar e trafegar os tokens JWT (`access_token_cookie` e `refresh_token_cookie`). 

### Por que HttpOnly?
- **Imunidade contra XSS:** O token não fica legível no JavaScript do navegador (`localStorage` ou `document.cookie`). Se um script malicioso for injetado, ele não conseguirá roubar as credenciais do usuário.
- **Transmissão Automática:** O navegador anexa automaticamente os cookies nas requisições destinadas ao mesmo domínio, desde que configuradas corretamente.

---

## 🛠️ 2. O Cliente de API Global (`apiClient.js`)

Para simplificar e blindar as requisições no Frontend, o projeto conta com o `apiClient.js`, localizado em `frontend/js/apiClient.js` e acessível nas páginas HTML via:

```html
<!-- Importar antes de qualquer script que realize requisições HTTP -->
<script src="/scripts/apiClient.js"></script>
```

### O que o `apiClient.js` faz automaticamente?
1. **Configuração CORS e Credentials:** Garante que toda requisição de API envie a instrução `credentials: 'same-origin'` (essencial para que o cookie HttpOnly seja anexado).
2. **Resolução de URL:** Adiciona automaticamente a origem correta para as chamadas `/api/*`.
3. **Intercepção de Erros de Sessão (401/Expired):** Caso a sessão expire durante uma chamada comum, o client tenta fazer o refresh de forma silenciosa chamando `/api/auth/refresh`. Se falhar, redireciona o usuário para a página de login automaticamente.
4. **Header de JSON:** Adiciona `Content-Type: application/json` e `Accept: application/json` por padrão sempre que houver payload.

---

## 🚀 3. Exemplos Práticos de Uso

### A. Login e Inicialização de Sessão
Ao fazer o login com sucesso, o backend injeta os cookies e responde com os dados básicos do usuário para controle de UX.

```javascript
// O login é feito enviando as credenciais normais
const resposta = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, senha })
});

const resultado = await resposta.json();

if (!resposta.ok) {
  throw new Error(resultado.message || 'Falha na autenticação.');
}

// O token está seguro no cookie HttpOnly gerenciado pelo navegador!
// Guardamos informações públicas do perfil apenas para renderização na tela (UX)
localStorage.setItem('saadi_user', JSON.stringify(resultado.data.user));

// Redireciona de acordo com a URL fornecida pelo backend
window.location.href = resultado.data.redirect_url;
```

### B. Listagem com Filtros e Paginação (GET)
Exemplo extraído do fluxo de triagens ou encaminhamentos:

```javascript
// A chamada é simples! O apiClient trata os cookies sob o capô.
try {
  const response = await fetch('/api/encaminhamentos?status=aberto&limit=10&page=1');
  const result = await response.json();
  
  if (response.ok) {
    const encaminhamentos = result.data.items;
    renderizarTabela(encaminhamentos);
  } else {
    exibirAlerta(result.message || 'Erro ao carregar dados.');
  }
} catch (error) {
  console.error('Falha de rede:', error);
}
```

### C. Cadastro com Envio de Payload (POST)
Exemplo de encaminhamento de aluno para atendimento psicopedagógico:

```javascript
const payload = {
  aluno_id: 12,
  motivo: "Apresenta dificuldades acentuadas na leitura e escrita rápida.",
  observacoes: "Foi conversado com a família previamente.",
  urgente: true
};

try {
  const response = await fetch('/api/encaminhamentos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  
  const result = await response.json();
  
  if (response.status === 201) {
    exibirToast('Encaminhamento realizado com sucesso!');
    fecharModal();
  } else {
    exibirMensagemErro(result.message);
  }
} catch (error) {
  exibirToast('Erro de conexão com o servidor.');
}
```

### D. Logout Seguro (POST)
Limpa os cookies seguros no backend e limpa o estado de UX no frontend.

```javascript
try {
  await fetch('/api/auth/logout', { method: 'POST' });
} catch (err) {
  console.warn('Erro ao notificar logout no servidor:', err);
} finally {
  localStorage.removeItem('saadi_user');
  window.location.href = '/index.html';
}
```

---

## ⚠️ 4. Boas Práticas Cruciais

1. **Nunca use Headers Manuais de Bearer Token:**
   * Evite fazer: `headers: { 'Authorization': 'Bearer ' + token }`. 
   * Deixe que o navegador utilize os **Cookies**.
2. **Utilize o `apiClient.js`:**
   * Ele protege as chamadas e evita duplicações de código de intercepção e tratamento de expiração de token.
3. **Validação de Formulários:**
   * Valide no HTML/JS antes de disparar o fetch para economizar requisições e prover feedbacks imediatos (ex: obrigatoriedade de campos, formato de e-mail, etc.).
