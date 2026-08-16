/**
 * Configuração compartilhada do site.
 *
 * Depois de criar o Google Forms de inscrição, cole o link dele aqui.
 * Esse mesmo link é usado automaticamente no botão "Inscreva-se" do
 * cabeçalho e na caixinha de inscrição da página inicial, em todas
 * as páginas do site — só precisa trocar em um lugar.
 */
const GOOGLE_FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSeacGZEKT4TJ6ObPqmbSBzqZ5hdX1EbtSg5WLT6Bv-EKPpIYQ/viewform?usp=publish-editor';

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-subscribe-link]').forEach(el => {
    el.href = GOOGLE_FORM_URL;
    el.target = '_blank';
    el.rel = 'noopener';
  });
});
