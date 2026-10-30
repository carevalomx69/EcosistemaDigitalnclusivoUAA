"""Aviso de privacidad, consentimiento y progreso por grupo."""
import sqlite3
from datetime import datetime

import pytest

from app import create_app, db
from app.aviso import VERSION_AVISO
from app.models import Grupo, Modulo, ProgresoSeccion, SeccionModulo, Usuario
from conftest import token_csrf


def crear(app, correo, aceptado=False, rol='estudiante'):
    with app.app_context():
        u = Usuario(nombre='Persona', apellidos='Prueba', correo=correo, rol=rol)
        u.establecer_contrasena('clave-de-prueba-3')
        if aceptado:
            u.aviso_aceptado_en, u.aviso_version = datetime.utcnow(), VERSION_AVISO
        db.session.add(u)
        db.session.commit()


def entrar(client, correo, clave='clave-de-prueba-3'):
    client.post('/login', data={'correo': correo, 'contrasena': clave, 'csrf_token': token_csrf(client)})


def test_aviso_es_publico_y_se_enlaza_desde_pie_y_login(client):
    r = client.get('/privacidad')
    assert r.status_code == 200 and 'Aviso de privacidad' in r.get_data(as_text=True)
    assert '/privacidad' in client.get('/login').get_data(as_text=True)
    assert '/privacidad' in client.get('/accesibilidad').get_data(as_text=True)


def test_borrador_se_muestra_hasta_que_se_apaga(client, monkeypatch):
    assert 'borrador de trabajo' in client.get('/privacidad').get_data(as_text=True)
    monkeypatch.setenv('AVISO_BORRADOR', '0')
    assert 'borrador de trabajo' not in client.get('/privacidad').get_data(as_text=True)


def test_datos_del_aviso_vienen_del_entorno(client, monkeypatch):
    monkeypatch.setenv('AVISO_CONTACTO', 'privacidad@ejemplo.test')
    assert 'privacidad@ejemplo.test' in client.get('/privacidad').get_data(as_text=True)


def test_sin_aceptar_se_redirige_a_la_pantalla_de_aceptacion(client, app):
    crear(app, 'nuevo@demo.example')
    entrar(client, 'nuevo@demo.example')
    for ruta in ('/', '/modulo', '/perfil'):
        r = client.get(ruta)
        assert r.status_code == 302 and '/aviso/aceptar' in r.headers['Location']
    # la propia pantalla, el aviso y la salida siguen disponibles
    for ruta in ('/aviso/aceptar', '/privacidad', '/accesibilidad'):
        assert client.get(ruta).status_code == 200
    assert client.get('/salir').status_code == 302


def test_no_se_puede_continuar_sin_marcar_la_aceptacion(client, app):
    crear(app, 'nuevo@demo.example')
    entrar(client, 'nuevo@demo.example')
    r = client.post('/aviso/aceptar', data={'csrf_token': token_csrf(client, '/aviso/aceptar')})
    assert r.status_code == 200 and 'necesitas aceptar' in r.get_data(as_text=True)
    with app.app_context():
        assert Usuario.query.filter_by(correo='nuevo@demo.example').one().aviso_aceptado_en is None


@pytest.mark.parametrize('investigacion', [True, False])
def test_aceptar_guarda_version_fecha_y_consentimiento(client, app, investigacion):
    crear(app, 'nuevo@demo.example')
    entrar(client, 'nuevo@demo.example')
    datos = {'acepto_aviso': '1', 'csrf_token': token_csrf(client, '/aviso/aceptar')}
    if investigacion:
        datos['consiente_investigacion'] = '1'
    r = client.post('/aviso/aceptar?next=/modulo', data=datos)
    assert r.status_code == 302 and r.headers['Location'].endswith('/modulo')
    with app.app_context():
        u = Usuario.query.filter_by(correo='nuevo@demo.example').one()
        assert u.aviso_version == VERSION_AVISO and u.aviso_aceptado_en is not None
        assert u.consiente_investigacion is investigacion
    assert client.get('/perfil').status_code == 200


def test_next_externo_se_ignora(client, app):
    crear(app, 'nuevo@demo.example')
    entrar(client, 'nuevo@demo.example')
    r = client.post('/aviso/aceptar?next=https://malo.example/',
                    data={'acepto_aviso': '1', 'csrf_token': token_csrf(client, '/aviso/aceptar')})
    assert r.status_code == 302 and 'malo.example' not in r.headers['Location']


def test_aceptar_exige_token_csrf(client, app):
    crear(app, 'nuevo@demo.example')
    entrar(client, 'nuevo@demo.example')
    client.post('/aviso/aceptar', data={'acepto_aviso': '1'})
    with app.app_context():
        assert Usuario.query.filter_by(correo='nuevo@demo.example').one().aviso_aceptado_en is None


def test_nueva_version_del_aviso_pide_aceptar_de_nuevo(client, app, monkeypatch):
    crear(app, 'viejo@demo.example', aceptado=True)
    entrar(client, 'viejo@demo.example')
    assert client.get('/perfil').status_code == 200
    monkeypatch.setattr('app.aviso.VERSION_AVISO', 'otra-version')
    monkeypatch.setattr('app.routes.VERSION_AVISO', 'otra-version')
    r = client.get('/perfil')
    assert r.status_code == 302 and '/aviso/aceptar' in r.headers['Location']


def test_registro_exige_aceptar_y_guarda_consentimiento(client, app):
    datos = {'nombre': 'Ana', 'apellidos': 'Lopez', 'correo': 'ana@demo.example', 'carrera': 'otra',
             'contrasena': 'una-clave-larga-1', 'confirmar_contrasena': 'una-clave-larga-1'}
    r = client.post('/registro', data={**datos, 'csrf_token': token_csrf(client, '/registro')})
    assert r.status_code == 200 and 'aviso de privacidad' in r.get_data(as_text=True)
    with app.app_context():
        assert Usuario.query.filter_by(correo='ana@demo.example').count() == 0
    r = client.post('/registro', data={**datos, 'acepto_aviso': '1', 'consiente_investigacion': '1',
                                       'csrf_token': token_csrf(client, '/registro')})
    assert r.status_code == 302
    with app.app_context():
        u = Usuario.query.filter_by(correo='ana@demo.example').one()
        assert u.aviso_version == VERSION_AVISO and u.consiente_investigacion is True
    assert client.get('/modulo').status_code == 200  # no pide aceptar otra vez


def test_el_perfil_permite_retirar_el_consentimiento(client, app):
    crear(app, 'ana@demo.example', aceptado=True)
    with app.app_context():
        Usuario.query.filter_by(correo='ana@demo.example').one().consiente_investigacion = True
        db.session.commit()
    entrar(client, 'ana@demo.example')
    client.post('/perfil', data={'csrf_token': token_csrf(client, '/perfil')})
    with app.app_context():
        assert Usuario.query.filter_by(correo='ana@demo.example').one().consiente_investigacion is False


# ── Actualización de una base de datos anterior ──────────────────────────
def test_base_anterior_recibe_las_columnas_nuevas_sin_perder_datos(tmp_path):
    ruta = tmp_path / 'vieja.db'
    con = sqlite3.connect(ruta)
    con.executescript("""
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre VARCHAR(100) NOT NULL, apellidos VARCHAR(100) NOT NULL,
          correo VARCHAR(150) UNIQUE NOT NULL, contrasena_hash VARCHAR(256) NOT NULL, rol VARCHAR(20), carrera VARCHAR(100),
          activo BOOLEAN, creado DATETIME, grupo_id INTEGER, pref_tamano_texto VARCHAR(20), pref_contraste VARCHAR(20),
          pref_velocidad_audio FLOAT, pref_densidad VARCHAR(20), pref_formatos VARCHAR(100));
        INSERT INTO usuarios (nombre, apellidos, correo, contrasena_hash, rol) VALUES ('Vieja','Cuenta','v@demo.example','x','docente');
    """)
    con.commit()
    con.close()
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta}'})
    with app.app_context():
        u = Usuario.query.filter_by(correo='v@demo.example').one()
        assert u.aviso_aceptado_en is None and u.consiente_investigacion is False
    # arrancar de nuevo con la base ya actualizada no falla
    create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{ruta}'})


# ── Progreso por grupo ───────────────────────────────────────────────────
def test_progreso_de_grupo_usa_secciones_completadas(app):
    with app.app_context():
        m = Modulo(titulo='M', activo=True)
        db.session.add(m)
        db.session.flush()
        secs = [SeccionModulo(modulo_id=m.id, orden=n, titulo=f'S{n}') for n in range(1, 5)]
        db.session.add_all(secs)
        g = Grupo(nombre='G1', carrera='otra')
        db.session.add(g)
        db.session.flush()
        a = Usuario(nombre='A', apellidos='A', correo='a@x.test', contrasena_hash='x', grupo_id=g.id)
        b = Usuario(nombre='B', apellidos='B', correo='b@x.test', contrasena_hash='x', grupo_id=g.id)
        db.session.add_all([a, b])
        db.session.flush()
        assert g.progreso_promedio == 0
        # A completa 4 de 4 y B 0 de 4: promedio 50 %
        db.session.add_all(ProgresoSeccion(usuario_id=a.id, seccion_id=s.id) for s in secs)
        db.session.commit()
        assert g.progreso_promedio == 50
        # B completa 2 de 4: (4 + 2) / 8 = 75 %
        db.session.add_all(ProgresoSeccion(usuario_id=b.id, seccion_id=s.id) for s in secs[:2])
        db.session.commit()
        assert g.progreso_promedio == 75


def test_progreso_de_grupo_sin_estudiantes_o_sin_modulo_es_cero(app):
    with app.app_context():
        g = Grupo(nombre='Vacío', carrera='otra')
        db.session.add(g)
        db.session.commit()
        assert g.progreso_promedio == 0
        db.session.add(Modulo(titulo='M', activo=True))
        db.session.commit()
        assert g.progreso_promedio == 0


def test_variable_vacia_se_trata_como_pendiente(client, monkeypatch):
    monkeypatch.setenv('AVISO_CONTACTO', '')
    assert 'por definir antes del piloto' in client.get('/privacidad').get_data(as_text=True)
