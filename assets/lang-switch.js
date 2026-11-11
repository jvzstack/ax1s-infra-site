/* Onthoudt de taalkeuze van de NL/EN-wissel (gebruikt door de standaard-Engelse homepage). */
document.addEventListener('click', function (e) {
  var a = e.target.closest && e.target.closest('.lang-switch');
  if (!a) return;
  try { localStorage.setItem('axLang', a.getAttribute('hreflang') === 'en' ? 'en' : 'nl'); } catch (err) {}
}, true);
