import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen


class DataError(Exception):
    pass


class Conflict(DataError):
    pass


TABLES = {'deportes', 'usuarios', 'perfiles', 'favoritos', 'reportes'}
BOOLS = {'activo'}
SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS deportes (
 id TEXT PRIMARY KEY, nombre TEXT NOT NULL, descripcion TEXT NOT NULL,
 objetivo TEXT NOT NULL, costo REAL, moneda TEXT NOT NULL DEFAULT 'BOB',
 periodo TEXT NOT NULL DEFAULT 'mes', minutos INTEGER NOT NULL,
 equipamiento TEXT NOT NULL, consejos TEXT NOT NULL, alimentacion TEXT NOT NULL,
 condiciones TEXT NOT NULL, espacio TEXT NOT NULL, dificultad TEXT NOT NULL,
 beneficios TEXT NOT NULL, imagen TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1,
 CHECK(costo IS NULL OR costo >= 0), CHECK(minutos BETWEEN 10 AND 240)
);
CREATE TABLE IF NOT EXISTS usuarios (
 id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, nombre TEXT NOT NULL,
 password_hash TEXT NOT NULL, rol TEXT NOT NULL DEFAULT 'usuario', creado TEXT NOT NULL,
 CHECK(rol IN ('usuario','admin'))
);
CREATE TABLE IF NOT EXISTS perfiles (
 id TEXT PRIMARY KEY REFERENCES usuarios(id) ON DELETE CASCADE,
 edad INTEGER NOT NULL, peso REAL, altura REAL, sexo TEXT NOT NULL,
 experiencia TEXT NOT NULL, objetivo TEXT NOT NULL, presupuesto REAL NOT NULL,
 dias INTEGER NOT NULL, minutos INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS favoritos (
 id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
 deporte_id TEXT NOT NULL REFERENCES deportes(id) ON DELETE RESTRICT,
 UNIQUE(usuario_id, deporte_id)
);
CREATE TABLE IF NOT EXISTS reportes (
 id TEXT PRIMARY KEY, deporte_id TEXT NOT NULL REFERENCES deportes(id) ON DELETE RESTRICT,
 usuario_id TEXT REFERENCES usuarios(id) ON DELETE SET NULL, campo TEXT NOT NULL,
 descripcion TEXT NOT NULL, estado TEXT NOT NULL DEFAULT 'pendiente', creado TEXT NOT NULL,
 CHECK(estado IN ('pendiente','resuelto','descartado'))
);
'''


class Store:
    def __init__(self, config):
        self.url = config['SUPABASE_URL'].rstrip('/')
        self.key = config['SUPABASE_SECRET_KEY']
        self.remote = config['DATA_BACKEND'] == 'supabase'
        self.path = config['DATABASE']
        self.new_local = not Path(self.path).exists()
        if self.remote and (not self.url.startswith('https://') or not self.key):
            raise RuntimeError('El modo supabase requiere URL HTTPS y clave del servidor.')
        if not self.remote:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
            with self.connection() as conn:
                conn.executescript(SCHEMA)

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def request(self, path, method='GET', data=None, content_type='application/json'):
        headers = {'apikey': self.key, 'Content-Type': content_type,
                   'Prefer': 'return=representation'}
        if not self.key.startswith('sb_secret_'):
            headers['Authorization'] = 'Bearer ' + self.key
        payload = data if isinstance(data, bytes) else (
            json.dumps(data).encode('utf-8') if data is not None else None)
        req = Request(self.url + path, data=payload, headers=headers, method=method)
        try:
            with urlopen(req, timeout=15) as res:
                body = res.read()
            return json.loads(body) if body else None
        except HTTPError as exc:
            if exc.code == 409:
                raise Conflict('El registro ya existe o tiene referencias asociadas.') from None
            raise DataError('No se pudo completar la operación en Supabase. Revisa la estructura y la conexión.') from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise DataError('No se pudo conectar con la base de datos. Intenta nuevamente.') from None

    def query(self, table, method='GET', filters=None, data=None):
        if table not in TABLES:
            raise ValueError('Tabla no permitida')
        filters = filters or {}
        if self.remote:
            params = {k: 'eq.' + (str(v).lower() if isinstance(v, bool) else str(v)) for k, v in filters.items()}
            if method == 'GET':
                params.update({'select': '*', 'order': 'id.asc', 'limit': '500'})
                rows = []
                for offset in range(0, 100000, 500):
                    params['offset'] = str(offset)
                    batch = self.request('/rest/v1/sportsinfo_' + table + '?' + urlencode(params), method)
                    if not isinstance(batch, list):
                        raise DataError('La base de datos devolvió un formato inesperado.')
                    rows.extend(batch)
                    if len(batch) < 500:
                        return rows
                raise DataError('La consulta es demasiado grande; limita los resultados.')
            rows = self.request('/rest/v1/sportsinfo_' + table + '?' + urlencode(params), method, data)
            if not isinstance(rows, list):
                raise DataError('La base de datos devolvió un formato inesperado.')
            return rows
        try:
            with self.connection() as conn:
                columns = {r['name'] for r in conn.execute('PRAGMA table_info(' + table + ')')}
                if not set(filters).issubset(columns) or (data and not set(data).issubset(columns)):
                    raise ValueError('Campo no permitido')
                where = (' WHERE ' + ' AND '.join(k + '=?' for k in filters)) if filters else ''
                values = list(filters.values())
                if method == 'GET':
                    result = [dict(r) for r in conn.execute('SELECT * FROM ' + table + where + ' ORDER BY id', values)]
                elif method == 'POST':
                    keys = list(data)
                    conn.execute('INSERT INTO ' + table + ' (' + ','.join(keys) + ') VALUES (' + ','.join('?' for _ in keys) + ')', list(data.values()))
                    result = [dict(data)]
                elif method == 'PATCH':
                    conn.execute('UPDATE ' + table + ' SET ' + ','.join(k + '=?' for k in data) + where, list(data.values()) + values)
                    result = [dict(r) for r in conn.execute('SELECT * FROM ' + table + where, values)]
                elif method == 'DELETE':
                    result = [dict(r) for r in conn.execute('SELECT * FROM ' + table + where, values)]
                    conn.execute('DELETE FROM ' + table + where, values)
                else:
                    raise ValueError('Método no permitido')
            return result
        except sqlite3.IntegrityError:
            raise Conflict('El registro ya existe o tiene referencias asociadas.') from None
        except sqlite3.Error:
            raise DataError('No se pudo completar la operación en la base local.') from None

    def all(self, table, **filters):
        return self.query(table, filters=filters)

    def get(self, table, identifier):
        rows = self.all(table, id=identifier)
        return rows[0] if rows else None

    def add(self, table, row):
        return self.query(table, 'POST', data=row)[0]

    def update(self, table, identifier, changes):
        result = self.query(table, 'PATCH', {'id': identifier}, changes)
        if not result:
            raise DataError('El registro ya no existe.')
        return result[0]

    def delete(self, table, identifier):
        return self.query(table, 'DELETE', {'id': identifier})

    def upload(self, bucket, name, content):
        self.request('/storage/v1/object/' + quote(bucket, safe='') + '/' + quote(name, safe='/'), 'POST', content, 'image/jpeg')
        return self.url + '/storage/v1/object/public/' + quote(bucket, safe='') + '/' + quote(name, safe='/')
