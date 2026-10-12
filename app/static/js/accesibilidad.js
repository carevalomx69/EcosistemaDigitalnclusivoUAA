/**
 * ECOSISTEMA DIGITAL EDUCATIVO INCLUSIVO — UAA
 * Módulo de accesibilidad dinámica
 * Aplica el perfil de preferencias del usuario al cargar la página
 * WCAG 2.2 nivel AA
 */

'use strict';

// ── ADAPTAR PERFIL AL CARGAR ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
  aplicarPreferencias();
  iniciarGlosarios();
  iniciarModales();
  iniciarAnunciosVivos();
});

/**
 * Lee las preferencias del usuario desde data-attributes del body
 * y aplica las clases CSS correspondientes
 * Las preferencias vienen del servidor via Jinja2
 */
function aplicarPreferencias() {
  var body = document.body;
  var prefs = body.dataset;

  // Tamaño de texto
  if (prefs.prefTexto === 'grande') body.classList.add('texto-grande');
  if (prefs.prefTexto === 'muy_grande') body.classList.add('texto-muy-grande');

  // Alto contraste
  if (prefs.prefContraste === 'alto') body.classList.add('modo-alto-contraste');

  // Velocidad de audio (se usa en el reproductor)
  if (prefs.prefVelocidadAudio) {
    window.PREF_VELOCIDAD_AUDIO = parseFloat(prefs.prefVelocidadAudio) || 1.0;
  }

  // Densidad reducida (menos elementos por pantalla)
  if (prefs.prefDensidad === 'reducida') body.classList.add('densidad-reducida');

  sincronizarBotonContraste();
}

// ── CONTROLES DE ACCESIBILIDAD EN CABECERA ──────────────────────────────
function alternarAltoContraste() {
  document.body.classList.toggle('modo-alto-contraste');
  var activo = document.body.classList.contains('modo-alto-contraste');
  sincronizarBotonContraste();
  anunciar(activo ? 'Modo alto contraste activado' : 'Modo alto contraste desactivado');
  guardarPreferencia({ contraste: activo ? 'alto' : 'normal' });
}

/** Refleja el estado del contraste en aria-pressed del botón de la cabecera. */
function sincronizarBotonContraste() {
  var boton = document.getElementById('btn-contraste');
  if (boton) {
    boton.setAttribute('aria-pressed',
      String(document.body.classList.contains('modo-alto-contraste')));
  }
}

function aumentarTexto() {
  var body = document.body;
  if (!body.classList.contains('texto-grande')) {
    body.classList.add('texto-grande');
    anunciar('Texto grande activado');
    guardarPreferencia({ texto: 'grande' });
  } else if (!body.classList.contains('texto-muy-grande')) {
    body.classList.add('texto-muy-grande');
    anunciar('Texto muy grande activado');
    guardarPreferencia({ texto: 'muy_grande' });
  }
}

function reducirTexto() {
  var body = document.body;
  if (body.classList.contains('texto-muy-grande')) {
    body.classList.remove('texto-muy-grande');
    anunciar('Tamaño de texto reducido');
    guardarPreferencia({ texto: 'grande' });
  } else if (body.classList.contains('texto-grande')) {
    body.classList.remove('texto-grande');
    anunciar('Tamaño de texto normal');
    guardarPreferencia({ texto: 'normal' });
  }
}

/**
 * Guarda el ajuste en el servidor (perfil del usuario) para que se conserve
 * al navegar y en próximas sesiones. Si falla, el ajuste sigue activo en la
 * página actual y se avisa de forma accesible.
 */
function guardarPreferencia(cambio) {
  var meta = document.querySelector('meta[name="csrf-token"]');
  if (!meta || !window.fetch) { return; }
  fetch('/preferencias', {
    method: 'POST',
    credentials: 'same-origin',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': meta.content
    },
    body: JSON.stringify(cambio)
  }).then(function (respuesta) {
    if (!respuesta.ok) { throw new Error('HTTP ' + respuesta.status); }
  }).catch(function () {
    anunciar('No se pudo guardar tu preferencia. Seguirá activa solo en esta página.');
  });
}

// ── REGIÓN LIVE PARA ANUNCIOS (WCAG 4.1.3) ──────────────────────────────
function iniciarAnunciosVivos() {
  if (!document.getElementById('anuncio-live')) {
    var div = document.createElement('div');
    div.id = 'anuncio-live';
    div.setAttribute('role', 'status');
    div.setAttribute('aria-live', 'polite');
    div.setAttribute('aria-atomic', 'true');
    div.className = 'oculto-visual';
    document.body.appendChild(div);
  }
}

function anunciar(mensaje) {
  var region = document.getElementById('anuncio-live');
  if (region) {
    region.textContent = '';
    setTimeout(function () { region.textContent = mensaje; }, 50);
  }
}

// ── GLOSARIO EXPANDIBLE — WCAG 3.1.3 ────────────────────────────────────
function iniciarGlosarios() {
  document.querySelectorAll('.glosario-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var expandido = this.getAttribute('aria-expanded') === 'true';
      var idDefinicion = this.getAttribute('aria-controls');
      var definicion = document.getElementById(idDefinicion);

      this.setAttribute('aria-expanded', String(!expandido));
      if (definicion) {
        definicion.classList.toggle('visible', !expandido);
      }
    });
  });
}

// ── MODALES ACCESIBLES — WCAG 2.1.2, 4.1.3 ──────────────────────────────
var ultimoFocoAnteModal = null;

function iniciarModales() {
  document.querySelectorAll('[data-abre-modal]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var idModal = this.getAttribute('data-abre-modal');
      abrirModal(idModal);
    });
  });

  document.querySelectorAll('[data-cierra-modal]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var idModal = this.getAttribute('data-cierra-modal');
      cerrarModal(idModal);
    });
  });

  // Cerrar al hacer clic en el overlay
  document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === this) {
        var modal = this.querySelector('[role="dialog"]');
        if (modal) cerrarModal(modal.id);
      }
    });
  });

  // Cerrar con Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      var abierto = document.querySelector('.modal-overlay:not(.modal-oculto)');
      if (abierto) {
        var modal = abierto.querySelector('[role="dialog"]');
        if (modal) cerrarModal(modal.id);
      }
    }
  });
}

function abrirModal(idModal) {
  var overlay = document.getElementById('overlay-' + idModal);
  if (!overlay) return;
  ultimoFocoAnteModal = document.activeElement;
  overlay.classList.remove('modal-oculto');
  overlay.removeAttribute('hidden');
  var primero = overlay.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (primero) primero.focus();
  document.body.style.overflow = 'hidden';
  atraparFocoEnModal(overlay);
}

function cerrarModal(idModal) {
  var overlay = document.getElementById('overlay-' + idModal);
  if (!overlay) return;
  overlay.classList.add('modal-oculto');
  overlay.setAttribute('hidden', '');
  document.body.style.overflow = '';
  if (ultimoFocoAnteModal) ultimoFocoAnteModal.focus();
}

function atraparFocoEnModal(overlay) {
  overlay.addEventListener('keydown', function trampa(e) {
    if (e.key !== 'Tab') return;
    var focuseables = Array.from(overlay.querySelectorAll(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ));
    if (focuseables.length === 0) return;
    var primero = focuseables[0];
    var ultimo  = focuseables[focuseables.length - 1];
    if (e.shiftKey) {
      if (document.activeElement === primero) { e.preventDefault(); ultimo.focus(); }
    } else {
      if (document.activeElement === ultimo) { e.preventDefault(); primero.focus(); }
    }
    if (overlay.classList.contains('modal-oculto')) overlay.removeEventListener('keydown', trampa);
  });
}

// ── REPRODUCTOR DE AUDIO ACCESIBLE ──────────────────────────────────────
function iniciarReproductorAudio(idAudio) {
  var audio = document.getElementById(idAudio);
  if (!audio) return;
  var vel = window.PREF_VELOCIDAD_AUDIO || 1.0;
  audio.playbackRate = vel;
}
