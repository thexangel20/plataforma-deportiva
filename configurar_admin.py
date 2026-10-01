from getpass import getpass
from pathlib import Path

from dotenv import set_key
from werkzeug.security import generate_password_hash


def configurar():
    ruta = Path(__file__).resolve().parent / '.env'
    usuario = input('Usuario administrador [axel]: ').strip() or 'axel'
    contrasena = getpass('Contraseña (mínimo 12 caracteres): ')
    if len(contrasena) < 12:
        raise SystemExit('La contraseña debe tener al menos 12 caracteres.')
    if contrasena != getpass('Repite la contraseña: '):
        raise SystemExit('Las contraseñas no coinciden.')
    set_key(str(ruta), 'ADMIN_USUARIO', usuario)
    set_key(str(ruta), 'ADMIN_PASSWORD_HASH', generate_password_hash(contrasena))
    print('Administrador configurado. Reinicia Flask si estaba ejecutándose.')


if __name__ == '__main__':
    configurar()
