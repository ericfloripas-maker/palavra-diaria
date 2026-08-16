# Palavra Diária — protótipo

Estrutura do projeto:

```
palavra-diaria/
├── index.html          → devocional do dia (lê do JSON)
├── temas.html            → devocionais agrupados por tema
├── arquivo.html          → devocionais agrupados por ano e mês
├── devocionais.json     → catálogo com todos os devocionais
├── css/style.css        → estilos (paleta, tipografia, layout)
├── js/main.js            → lê o catálogo, monta index.html e controla o áudio
├── js/temas.js            → monta temas.html
├── js/arquivo.js          → monta arquivo.html
├── audio/                → arquivos .mp3, um por devocional
├── textos/                → onde soltar novos .odt/.docx pra importar
├── textos/publicados/     → arquivo dos .odt já importados (não é reprocessado)
├── importar_devocionais.py
└── README.md
```

## Como abrir no VS Code

1. Extraia esta pasta em qualquer lugar do computador.
2. No VS Code: **Arquivo → Abrir Pasta...** e selecione `palavra-diaria`.
3. Instale a extensão **Live Server** (Ritwick Dey) se ainda não tiver.
4. Clique com o botão direito em `index.html` → **Open with Live Server**.
   (Precisa ser via Live Server, e não abrindo o arquivo direto no navegador,
   porque a página busca o `devocionais.json` — isso só funciona servido por
   http, não abrindo o arquivo local direto.)

## Publicar o site e automatizar a inscrição/envio (gratuito)

Isso é feito em três partes: publicar o site, criar o formulário de
inscrição, e ligar o envio automático de e-mail. Nenhuma delas custa nada.

### Parte 1 — Publicar o site no GitHub Pages

1. Crie uma conta gratuita em [github.com](https://github.com), se ainda não tiver.
2. Crie um repositório novo (botão verde "New"), por exemplo chamado `palavra-diaria`.
   Marque como **Public**.
3. No VS Code, com a pasta `palavra-diaria` aberta, use o painel **Source Control**
   (ícone de ramificação na lateral esquerda) para inicializar o Git e enviar
   os arquivos:
   - Clique em "Initialize Repository"
   - Escreva uma mensagem tipo "primeira versão" e clique no ✓ (Commit)
   - Clique em "Publish Branch" e escolha o repositório que você criou no GitHub
4. No site do GitHub, vá em **Settings → Pages**. Em "Branch", escolha `main`
   e a pasta `/ (root)`, depois **Save**.
5. Espere 1-2 minutos. Seu site fica no ar em:
   `https://SEU-USUARIO.github.io/palavra-diaria/`
   (troque `SEU-USUARIO` pelo seu nome de usuário do GitHub)

A partir de agora, toda vez que você quiser atualizar o site publicado,
repete só o passo 3 (Commit + Push, ou "Sync Changes" no VS Code).

### Parte 2 — Criar o formulário de inscrição

1. Acesse [forms.google.com](https://forms.google.com) e crie um formulário novo.
2. Adicione uma pergunta chamada exatamente **E-mail**, tipo "Resposta curta",
   marcada como obrigatória.
3. Na aba **Respostas** do formulário, clique no ícone verde do Sheets para
   criar uma planilha vinculada — é nela que os e-mails vão se acumular.
4. Clique em **Enviar** (canto superior direito) → ícone de link → copie o
   link do formulário.
5. Abra `js/config.js` no projeto e cole esse link no lugar de
   `'https://forms.gle/SEU-LINK-AQUI'`. Salve, publique de novo (Parte 1,
   passo 3) — o botão "Inscreva-se" do site já passa a abrir o formulário
   de verdade.

### Parte 3 — Automatizar o envio do devocional por e-mail

1. Abra a planilha criada no passo 2.3 → **Extensões → Apps Script**.
2. Apague o conteúdo padrão e cole o conteúdo de
   `google-apps-script/enviar_devocionais.gs` (está nesta pasta do projeto).
3. No topo do script, troque `SITE_URL` pelo endereço do seu site publicado
   na Parte 1 (com a barra `/` no final).
4. Salve (ícone de disquete). Na barra de funções no topo do editor, escolha
   `testarEnvioParaMim` e clique em ▶ Executar. Na primeira vez, o Google
   vai pedir permissão — autorize (é o script pedindo para poder enviar
   e-mail em seu nome). Confira sua caixa de entrada: deve chegar um
   e-mail de teste com o devocional do dia.
5. Se o teste funcionou, escolha `configurarGatilhoDiario` na mesma barra
   e clique em ▶ Executar uma única vez. Isso ativa o envio automático
   todo dia, sem precisar abrir a planilha de novo.

Pronto: a partir daqui, sempre que você publicar um devocional novo
(atualizando `devocionais.json` e o site no GitHub), o gatilho diário
manda automaticamente para todos os inscritos da planilha, sozinho.

**Detalhes que valem saber:**
- O limite de envio de uma conta Gmail comum é 100 e-mails/dia — dá folga
  grande pra uma lista começando do zero, mas se crescer muito além disso
  me avise que ajustamos a estratégia.
- O script nunca manda o mesmo devocional duas vezes no mesmo dia, mesmo
  que o gatilho rode mais de uma vez.
- Pra ver quem já está inscrito, é só abrir a planilha diretamente.


1. Salve os arquivos `.odt` (ou `.docx`) dos devocionais dentro da pasta `textos/`.
   Cada documento precisa seguir este formato — um parágrafo por linha, nesta ordem:
   ```
   DD/MM/AAAA
   Referência bíblica (ex: Salmos 90:5,6)
   Texto do versículo
   (um ou mais parágrafos de reflexão)
   Oração: texto da oração
   (opcional) Nome do autor, sozinho na última linha
   ```
2. No terminal do VS Code (**Terminal → New Terminal**), rode:
   ```
   python importar_devocionais.py
   ```
3. O script lê todos os arquivos novos da pasta `textos/`, adiciona cada um
   ao `devocionais.json` e mostra um resumo no final. Rodar de novo não
   duplica nada — arquivos já importados são ignorados automaticamente.
4. **Importante:** o script não sabe inventar um título editorial de
   verdade — ele usa um provisório tipo "Meditação em Salmos 90:5,6" e marca
   `needsTitleReview: true` na entrada. Abra o `devocionais.json`, procure
   por esse marcador e escreva o título de verdade antes de publicar (pode
   apagar o campo `needsTitleReview` depois de revisar, ou deixar — ele não
   afeta a página).
5. Coloque os áudios em `audio/`, com o nome que aparece no campo `"audio"`
   de cada entrada (o script já monta esse nome a partir da data e do slug).

## Adicionar um devocional manualmente (sem o importador)

Abra `devocionais.json` — é uma lista. Adicione um novo item (com vírgula
separando do anterior) com esses campos:

```json
{
  "date": "2026-08-16",
  "slug": "titulo-em-poucas-palavras",
  "title": "Título do Devocional",
  "verseRef": "Livro Capítulo:Versículo",
  "verseText": "Texto do versículo-chave.",
  "reflection": [
    "Primeiro parágrafo da reflexão.",
    "Segundo parágrafo."
  ],
  "prayer": "Texto da oração (ou remova este campo se não houver oração).",
  "author": "Nome do autor",
  "audio": "audio/2026-08-16-titulo-em-poucas-palavras.mp3",
  "tags": ["Tema1", "Tema2"],
  "relatedThemes": ["Tema3", "Tema4", "Tema5"]
}
```

Pode adicionar **vários de uma vez** — a página sempre escolhe sozinha:

- Se existir um devocional com a data de hoje, mostra ele.
- Se não existir nenhum com a data exata de hoje, mostra o mais recente
  cujo `date` já passou.
- Os demais aparecem automaticamente em "Devocionais Recentes", do mais
  novo pro mais antigo (até 5).
- Clicar em um item de "Devocionais Recentes" abre esse dia específico
  (via `?data=AAAA-MM-DD` na URL), sem precisar de outra página.

## Áudio

Coloque o `.mp3` de cada devocional dentro de `audio/`, com o mesmo nome
que você usou no campo `"audio"` daquele item do JSON. Convenção sugerida:
`audio/AAAA-MM-DD-titulo-em-poucas-palavras.mp3`.

O player (play/pause, tempo, barra de progresso clicável, mudo, velocidade)
já funciona de verdade a partir desse arquivo — não precisa mexer no
`main.js` para isso.

## Onde mexer em cada coisa

- **Cores e fontes** → topo de `css/style.css`, no bloco `:root { ... }`.
- **Conteúdo dos devocionais** → só em `devocionais.json`, nunca em `index.html`.
- **Layout/estrutura da página** → `index.html` (os `id`s marcam onde o
  JavaScript insere o conteúdo).

## Próximos passos naturais

- Ligar o formulário de e-mail a um serviço de verdade (Mailchimp, Resend, etc.).
- Criar uma página "ver todos os devocionais" listando o catálogo inteiro,
  não só os 5 mais recentes.
