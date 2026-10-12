import os
import subprocess
import sys
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def sembrar(tmp_path, *args, **env_extra):
    bd = tmp_path / 'prueba.db'
    env = {k: v for k, v in os.environ.items()
           if k not in ('APP_ENV', 'DEMO_PASSWORD', 'SECRET_KEY')}
    env.update({'DATABASE_URL': f'sqlite:///{bd}'}, **env_extra)
    r = subprocess.run([sys.executable, str(RAIZ / 'seed.py'), *args],
                       cwd=RAIZ, env=env, capture_output=True, text=True)
    return bd, r


def contar_usuarios(bd):
    if not bd.exists():
        return 0
    con = sqlite3.connect(bd)
    try:
        return con.execute('select count(*) from usuarios').fetchone()[0]
    finally:
        con.close()


def test_seed_no_borra_datos_existentes(tmp_path):
    bd, r1 = sembrar(tmp_path)
    assert r1.returncode == 0, r1.stderr
    total = contar_usuarios(bd)
    assert total == 7
    con = sqlite3.connect(bd)
    con.execute("update usuarios set nombre='Cambiado' where correo='alumno@demo.example'")
    con.commit(); con.close()
    _, r2 = sembrar(tmp_path)
    assert 'ya tiene datos' in r2.stdout
    con = sqlite3.connect(bd)
    nombre = con.execute("select nombre from usuarios where correo='alumno@demo.example'").fetchone()[0]
    con.close()
    assert nombre == 'Cambiado'  # no se volvió a sembrar


def test_seed_reset_reinicia_la_base(tmp_path):
    bd, _ = sembrar(tmp_path)
    con = sqlite3.connect(bd)
    con.execute("update usuarios set nombre='Cambiado' where correo='alumno@demo.example'")
    con.commit(); con.close()
    sembrar(tmp_path, '--reset')
    con = sqlite3.connect(bd)
    nombre = con.execute("select nombre from usuarios where correo='alumno@demo.example'").fetchone()[0]
    con.close()
    assert nombre != 'Cambiado'


def test_seed_en_produccion_sin_contrasena_no_crea_usuarios(tmp_path):
    bd, r = sembrar(tmp_path, APP_ENV='production', SECRET_KEY='x' * 32)
    assert r.returncode == 0
    assert contar_usuarios(bd) == 0
    assert 'DEMO_PASSWORD' in r.stdout


def test_seed_usa_la_contrasena_de_entorno(tmp_path):
    from werkzeug.security import check_password_hash
    bd, r = sembrar(tmp_path, DEMO_PASSWORD='contrasena-de-prueba-xyz')
    con = sqlite3.connect(bd)
    h = con.execute("select contrasena_hash from usuarios where correo='docente@demo.example'").fetchone()[0]
    con.close()
    assert check_password_hash(h, 'contrasena-de-prueba-xyz')
    assert not check_password_hash(h, 'docente2025')
