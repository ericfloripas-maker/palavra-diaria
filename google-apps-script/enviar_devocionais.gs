/**
 * Palavra Diária — envio automático de e-mail
 *
 * Como configurar (uma vez só):
 *   1. Crie um Google Forms com um campo "E-mail" e ligue as respostas
 *      a uma planilha do Google Sheets (Respostas → criar planilha).
 *   2. Abra essa planilha → Extensões → Apps Script.
 *   3. Apague o conteúdo padrão e cole este arquivo inteiro.
 *   4. Troque o valor de SITE_URL abaixo pelo endereço real do seu site
 *      publicado (ex: https://seu-usuario.github.io/palavra-diaria/).
 *   5. Rode a função configurarGatilhoDiario() uma única vez (veja o
 *      passo a passo completo no README.md, seção "Publicar e automatizar").
 *
 * A partir daí, todo dia no horário definido, o script sozinho:
 *   - Busca o devocional do dia no devocionais.json do site publicado
 *   - Manda um e-mail resumido pra cada inscrito da planilha
 *   - Não manda duas vezes o mesmo devocional, mesmo se o gatilho rodar
 *     mais de uma vez no mesmo dia
 */

// TROQUE AQUI pelo endereço real do site depois de publicar no GitHub Pages
const SITE_URL = 'https://SEU-USUARIO.github.io/palavra-diaria/';

// Nome da coluna de e-mail que o Google Forms cria na planilha
const COLUNA_EMAIL = 'E-mail';

// Horário do envio diário (0 a 23, horário de Brasília)
const HORA_ENVIO = 7;


function enviarDevocionalDoDia() {
  const entry = buscarDevocionalDeHoje();
  if (!entry) {
    Logger.log('Nenhum devocional encontrado para hoje. Nada foi enviado.');
    return;
  }

  const jaEnviadoHoje = PropertiesService.getScriptProperties().getProperty('ultimoEnviado');
  const hojeStr = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyy-MM-dd');
  if (jaEnviadoHoje === `${hojeStr}:${entry.slug}`) {
    Logger.log('Este devocional já foi enviado hoje. Pulando envio duplicado.');
    return;
  }

  const emails = listarInscritos();
  if (emails.length === 0) {
    Logger.log('Nenhum inscrito na planilha ainda.');
    return;
  }

  const assunto = `Palavra Diária: ${entry.title}`;
  const corpo = montarCorpoEmail(entry);

  emails.forEach(email => {
    try {
      MailApp.sendEmail({
        to: email,
        subject: assunto,
        htmlBody: corpo,
      });
    } catch (erro) {
      Logger.log(`Falha ao enviar para ${email}: ${erro}`);
    }
  });

  PropertiesService.getScriptProperties().setProperty('ultimoEnviado', `${hojeStr}:${entry.slug}`);
  Logger.log(`Enviado "${entry.title}" para ${emails.length} inscrito(s).`);
}


function buscarDevocionalDeHoje() {
  const resposta = UrlFetchApp.fetch(SITE_URL + 'devocionais.json', { muteHttpExceptions: true });
  if (resposta.getResponseCode() !== 200) {
    Logger.log('Não foi possível acessar devocionais.json: ' + resposta.getResponseCode());
    return null;
  }
  const entries = JSON.parse(resposta.getContentText());
  const hojeStr = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'yyyy-MM-dd');

  const ordenado = entries.slice().sort((a, b) => (a.date < b.date ? 1 : -1));
  const exato = ordenado.find(e => e.date === hojeStr);
  if (exato) return exato;
  return ordenado.find(e => e.date <= hojeStr) || null;
}


function listarInscritos() {
  const planilha = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  const dados = planilha.getDataRange().getValues();
  const cabecalho = dados[0];
  const colEmail = cabecalho.indexOf(COLUNA_EMAIL);
  if (colEmail === -1) {
    Logger.log(`Coluna "${COLUNA_EMAIL}" não encontrada. Colunas disponíveis: ${cabecalho.join(', ')}`);
    return [];
  }
  return dados
    .slice(1)
    .map(row => row[colEmail])
    .filter(email => typeof email === 'string' && email.includes('@'));
}


function montarCorpoEmail(entry) {
  const link = `${SITE_URL}index.html?data=${entry.date}`;
  const primeiroParagrafo = (entry.reflection && entry.reflection[0]) || '';

  return `
    <div style="font-family: Georgia, serif; max-width: 560px; margin: 0 auto; color: #2B2E27;">
      <p style="font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #6B6E64;">
        Palavra Diária
      </p>
      <h1 style="font-size: 22px; margin: 6px 0 14px;">${entry.title}</h1>
      <p style="font-style: italic; color: #4A5A3D; margin-bottom: 18px;">
        "${entry.verseText}" – ${entry.verseRef}
      </p>
      <p style="line-height: 1.6;">${primeiroParagrafo}</p>
      <p style="margin-top: 24px;">
        <a href="${link}" style="background: #4A5A3D; color: #F7F4EE; padding: 10px 20px;
           border-radius: 20px; text-decoration: none; font-family: sans-serif; font-size: 14px;">
          Ler devocional completo →
        </a>
      </p>
      <p style="margin-top: 32px; font-size: 12px; color: #6B6E64;">
        Você recebeu este e-mail porque se inscreveu em Palavra Diária.
      </p>
    </div>
  `;
}


/**
 * Rode esta função UMA ÚNICA VEZ para ligar o envio automático diário.
 * Depois disso, enviarDevocionalDoDia() roda sozinha todo dia, sem
 * precisar abrir a planilha nem o editor de novo.
 */
function configurarGatilhoDiario() {
  // remove gatilhos antigos desta função, pra não duplicar o envio
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'enviarDevocionalDoDia')
    .forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger('enviarDevocionalDoDia')
    .timeBased()
    .everyDays(1)
    .atHour(HORA_ENVIO)
    .inTimezone('America/Sao_Paulo')
    .create();

  Logger.log(`Gatilho diário configurado para as ${HORA_ENVIO}h (horário de Brasília).`);
}


/**
 * Função de teste: manda o devocional de hoje só pro seu próprio e-mail,
 * pra conferir se está tudo certo antes de ativar pra valer.
 */
function testarEnvioParaMim() {
  const entry = buscarDevocionalDeHoje();
  if (!entry) {
    Logger.log('Nenhum devocional encontrado para hoje.');
    return;
  }
  MailApp.sendEmail({
    to: Session.getActiveUser().getEmail(),
    subject: `[TESTE] Palavra Diária: ${entry.title}`,
    htmlBody: montarCorpoEmail(entry),
  });
  Logger.log('E-mail de teste enviado para ' + Session.getActiveUser().getEmail());
}
