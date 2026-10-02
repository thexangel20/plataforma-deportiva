import argparse
import getpass
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from werkzeug.security import generate_password_hash

from sportsinfo import create_app
from sportsinfo.seed import sports
from sportsinfo.store import Store, DataError


def main():
    parser = argparse.ArgumentParser(description='Administración local de SportsInfo')
    sub = parser.add_subparsers(dest='command', required=True)
    admin = sub.add_parser('create-admin')
    admin.add_argument('--email', required=True)
    admin.add_argument('--nombre', default='Administrador')
    admin.add_argument('--generar', action='store_true')
    sub.add_parser('seed')
    sub.add_parser('check')
    sub.add_parser('migrate-local')
    args = parser.parse_args()
    app = create_app()
    store = app.extensions['store']
    if args.command == 'create-admin':
        email = args.email.strip().lower()
        if len(email) > 254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise ValueError('Correo no válido')
        if store.all('usuarios', email=email):
            raise ValueError('El correo ya existe. No se modifica su cuenta ni su rol.')
        password = secrets.token_urlsafe(18) if args.generar else getpass.getpass('Contraseña (10–128 caracteres): ')
        if not 10 <= len(password) <= 128:
            raise ValueError('La contraseña debe tener entre 10 y 128 caracteres')
        if not args.generar and password != getpass.getpass('Repite la contraseña: '):
            raise ValueError('Las contraseñas no coinciden')
        store.add('usuarios', dict(id=uuid4().hex, email=email, nombre=args.nombre,
                  password_hash=generate_password_hash(password), rol='admin',
                  creado=datetime.now(timezone.utc).isoformat()))
        if args.generar:
            path = Path(app.instance_path) / 'ACCESO_ADMIN_LOCAL.txt'
            with path.open('a', encoding='utf-8') as stream:
                stream.write(f'\nSportsInfo ({app.config["DATA_BACKEND"]})\nCorreo: {email}\nContraseña: {password}\n')
            print('Cuenta creada. Credenciales guardadas en:', path)
        else:
            print('Cuenta administrativa creada.')
    elif args.command == 'seed':
        count = 0
        for row in sports():
            if not store.get('deportes', row['id']):
                store.add('deportes', row)
                count += 1
        print('Deportes de ejemplo agregados:', count)
    elif args.command == 'check':
        for table in ('deportes', 'usuarios', 'perfiles', 'favoritos', 'reportes'):
            print(table + ':', len(store.all(table)), 'registros')
        print('Modo:', app.config['DATA_BACKEND'])
    elif args.command == 'migrate-local':
        if not store.remote:
            raise ValueError('Configura DATA_BACKEND=supabase antes de migrar.')
        config = dict(app.config)
        config['DATA_BACKEND'] = 'local'
        local = Store(config)
        for table in ('deportes', 'usuarios', 'perfiles', 'favoritos', 'reportes'):
            added = 0
            for row in local.all(table):
                if store.get(table, row['id']):
                    continue
                if table == 'deportes':
                    row['activo'] = bool(row['activo'])
                    if row['imagen'].startswith('/imagenes/'):
                        filename = row['imagen'].rsplit('/', 1)[-1]
                        if not re.fullmatch(r'[a-f0-9]{32}\.jpg', filename):
                            raise ValueError('Ruta de imagen local inválida')
                        content = (Path(app.config['UPLOAD_FOLDER']) / filename).read_bytes()
                        row['imagen'] = store.upload(app.config['SUPABASE_BUCKET'], filename, content)
                store.add(table, row)
                added += 1
            print(table + ':', added, 'copiados; los identificadores existentes se conservaron.')


if __name__ == '__main__':
    try:
        main()
    except (ValueError, DataError, OSError) as error:
        raise SystemExit(str(error)) from None
