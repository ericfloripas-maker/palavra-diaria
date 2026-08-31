# Palavra Diária — protótipo

Estrutura do projeto:

```
palavra-diaria/
├── index.html          → devocional do dia (lê do JSON)
├── temas.html            → devocionais agrupados por tema
├── arquivo.html          → devocionais agrupados por ano e mês
├── sobre.html             → página institucional
├── contato.html           → página de contato
├── devocionais.json     → catálogo com todos os devocionais
├── css/style.css        → estilos (paleta, tipografia, layout)
├── js/main.js            → lê o catálogo, monta index.html e controla o áudio
├── js/temas.js            → monta temas.html
├── js/arquivo.js          → monta arquivo.html
├── js/config.js           → link do formulário de inscrição (usado em todas as páginas)
├── audio/                → arquivos .mp3, um por devocional
├── textos/                → onde soltar novos .odt/.docx pra importar
├── textos/publicados/     → arquivo dos .odt já importados (não é reprocessado)
├── importar_devocionais.py
├── google-apps-script/    → scripts do Google (e-mail automático, card social)
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

A partir de agora, toda vez que você quiser atualizar o site publicado, é
sempre a mesma sequência de 3 comandos no terminal (dentro da pasta do
projeto):
```
git add -A
git commit -m "uma mensagem curta descrevendo o que mudou"
git push
```

### Domínio próprio

O site também está publicado no domínio próprio:

**https://devocionalpalavradiaria.com.br/**

O endereço antigo (`https://ericfloripas-maker.github.io/palavra-diaria/`)
continua funcionando normalmente — o GitHub nunca desliga ele, mesmo com
um domínio próprio configurado. Mas o domínio próprio é o endereço "de
verdade" a partir de agora, e é ele que está configurado no `SITE_URL`
dos scripts do Google (Parte 3 abaixo).

Se um dia trocar de domínio de novo, os lugares que precisam ser
atualizados juntos são: `SITE_URL` em cada arquivo dentro de
`google-apps-script/`, e este README.

### Parte 2 — Criar o formulário de inscrição

1. Acesse [forms.google.com](https://forms.google.com) e crie um formulário novo.
2. Adicione uma pergunta chamada exatamente **E-mail**, tipo "Resposta curta",
   marcada como obrigatória.
3. Na aba **Respostas** do formulário, clique no ícone verde do Sheets para
   criar uma planilha vinculada — é nela que os e-mails vão se acumular.
4. Clique em **Enviar** (canto superior direito) → ícone de link → copie o
   link do formulário.
5. Abra `js/config.js` no projeto e cole esse link no lugar de
   `GOOGLE_FORM_URL`. Salve e publique de novo (Parte 1) — o botão
   "Inscreva-se" do site inteiro já passa a abrir o formulário de verdade.

### Parte 3 — Automatizar o envio do devocional por e-mail

1. Abra a planilha criada no passo 2.3 → **Extensões → Apps Script**.
2. Apague o conteúdo padrão e cole o conteúdo de
   `google-apps-script/enviar_devocionais.gs` (está nesta pasta do projeto).
   Ele já vem com `SITE_URL` apontando pro domínio próprio — só precisa
   trocar se o domínio mudar de novo no futuro.
3. Salve (ícone de disquete). Na barra de funções no topo do editor, escolha
   `testarEnvioParaMim` e clique em ▶ Executar. Na primeira vez, o Google
   vai pedir permissão — autorize (é o script pedindo para poder enviar
   e-mail em seu nome). Se aparecer aviso de "app não verificada", clique
   em Configurações avançadas → Acessar (nome do projeto) → Permitir; é
   normal, é o seu próprio script. Confira sua caixa de entrada (e o spam):
   deve chegar um e-mail de teste com o devocional do dia.
4. Se o teste funcionou, escolha `configurarGatilhoDiario` na mesma barra
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

### Parte 4 (opcional) — Gerar o card do dia pra Instagram/Facebook

Isso NÃO publica sozinho nas redes — publicar de verdade sem clique
nenhum exigiria a API da Meta, que usa tokens que expiram e regras que
mudam sem aviso. Em vez disso, todo dia você recebe por e-mail a imagem
já pronta (no estilo do site) e a legenda já escrita — só falta você
baixar e colar no Instagram/Facebook.

1. Crie uma apresentação nova no Google Slides, com **1 slide só**, no
   tamanho personalizado 10 × 10 polegadas (**Arquivo → Configurar
   página → Personalizado**).
2. Monte o layout do card nesse slide, com 4 caixas de texto contendo
   **exatamente** este conteúdo:
   - `{{TITULO}}`
   - `{{VERSICULO}}`
   - `{{REFERENCIA}}`
   - `{{TAG}}`

   O script troca esses textos pelo conteúdo de cada dia automaticamente.
3. Copie o ID da apresentação — é o trecho longo de letras/números na
   URL, entre `/d/` e `/edit`.
4. No mesmo projeto de Apps Script da Parte 3, clique no **+** ao lado de
   "Arquivos" → **Script**, dê um nome, e cole o conteúdo de
   `google-apps-script/gerar_card_social.gs`.
5. No topo do novo arquivo, troque `TEMPLATE_SLIDE_ID` pelo ID copiado
   no passo 3.
6. Rode `testarCardParaMim` uma vez e confira se o e-mail chegou com a
   imagem certa.
7. Rode `configurarGatilhoCardDiario` uma única vez pra ativar o envio
   automático diário.

## Adicionar vários devocionais de uma vez (importador automático)

1. Salve os arquivos `.odt` (ou `.docx`) dos devocionais dentro da pasta
   `textos/`, com o nome começando pela data:
   ```
   AAAA-MM-DD-titulo-em-poucas-palavras.odt
   ```
   Exemplo: `2026-08-11-como-um-sono-como-a-relva.odt`

   Só a data no início é obrigatória para o script — é dali que ele lê
   a data do devocional. O resto do nome (o "slug") é livre; o ideal é
   que combine com o nome do arquivo de áudio correspondente.

   Também é possível incluir a referência bíblica abreviada no meio do
   nome, se preferir — o importador reconhece esse formato também, mas
   ele é só decorativo, o script sempre pega a referência de verdade de
   dentro do texto do documento, nunca do nome do arquivo:
   ```
   AAAA-MM-DD-Livro_Capitulo_Versiculo-titulo-em-poucas-palavras.odt
   ```
   Exemplo: `2026-08-17-Lv_3_16-entregando-o-nosso-melhor.odt`

   Dentro do documento, um parágrafo por linha, nesta ordem:
   ```
   TÍTULO DO DEVOCIONAL
   Texto do versículo, terminando com a referência entre parênteses (Livro C:V)
   (um ou mais parágrafos de reflexão)
   Oração: texto da oração
   ```
   Se o nome do arquivo não tiver a data no início (`AAAA-MM-DD-...`), o
   importador também aceita o formato mais antigo: primeira linha do
   documento sendo a data por extenso (`DD/MM/AAAA`), segunda linha a
   referência bíblica sozinha, terceira linha o texto do versículo.
2. No terminal do VS Code (**Terminal → New Terminal**), rode:
   ```
   py importar_devocionais.py
   ```
   (em alguns computadores o comando certo é `python` em vez de `py` —
   tente o outro se esse não for reconhecido. Nunca clique no botão ▶
   "Run" do editor pra isso — ele tenta rodar com configurações erradas;
   sempre digite o comando direto no terminal.)
3. O script lê todos os arquivos novos da pasta `textos/`, adiciona cada um
   ao `devocionais.json` e mostra um resumo no final. Rodar de novo não
   duplica nada — arquivos já importados são ignorados automaticamente.
4. Quando o documento já vem com um título de verdade na primeira linha,
   o importador usa ele direto, sem precisar de revisão. Só nos casos em
   que ele não conseguiu identificar um título (marcados com
   `needsTitleReview: true` no `devocionais.json`) é que vale abrir o
   arquivo e escrever um título de verdade à mão.
5. Coloque os áudios em `audio/`, com o nome que aparece no campo `"audio"`
   de cada entrada (o script já monta esse nome a partir da data e do slug
   do título — geralmente bate com o nome do arquivo de áudio original,
   sem a parte da referência bíblica no meio).
6. Depois de conferir tudo, envie pro GitHub:
   ```
   git add -A
   git commit -m "adicionar novos devocionais"
   git push
   ```

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
  novo pro mais antigo (até 5), e todos aparecem na página Arquivo,
  agrupados por ano e mês.
- Clicar em um item de "Devocionais Recentes" ou do Arquivo abre esse dia
  específico (via `?data=AAAA-MM-DD` na URL), sem precisar de outra página.

## Áudio

Coloque o `.mp3` de cada devocional dentro de `audio/`, com o mesmo nome
que você usou no campo `"audio"` daquele item do JSON. Convenção sugerida:
`audio/AAAA-MM-DD-titulo-em-poucas-palavras.mp3`.

O player (play/pause, tempo, barra de progresso clicável, mudo, velocidade)
já funciona de verdade a partir desse arquivo — não precisa mexer no
`main.js` para isso.

Se o áudio original estiver em `.wav` ou outro formato, precisa converter
pra `.mp3` antes (o site só toca mp3). Se precisar de ajuda com isso, é só
pedir.

## Onde mexer em cada coisa

- **Cores e fontes** → topo de `css/style.css`, no bloco `:root { ... }`.
- **Conteúdo dos devocionais** → só em `devocionais.json`, nunca em `index.html`.
- **Layout/estrutura da página** → `index.html`, `temas.html`, `arquivo.html`,
  `sobre.html`, `contato.html` (os `id`s marcam onde o JavaScript insere o
  conteúdo dinâmico).
- **Link do formulário de inscrição** → `js/config.js`, um lugar só, usado
  em todas as páginas.

## Próximos passos naturais

- Criar uma página "ver todos os devocionais por tema/ano" mais robusta,
  se o catálogo crescer muito.
- Considerar automação total de publicação em redes sociais via API da
  Meta, se o processo manual (Parte 4) virar gargalo.