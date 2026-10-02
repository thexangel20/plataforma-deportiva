import html
import re
from io import BytesIO
from decimal import Decimal
from unittest.mock import patch

import pytest
from PIL import Image
from werkzeug.datastructures import MultiDict
from werkzeug.security import generate_password_hash

from sportsinfo import create_app
from sportsinfo.calculations import budget, wear, shopping, plan, number, CATEGORIES
from sportsinfo.store import DataError, Conflict, Store


@pytest.fixture
def app(tmp_path):
    return create_app({'TESTING': True, 'SECRET_KEY': 'test-secret', 'DATA_BACKEND': 'local',
                       'DATABASE': str(tmp_path / 'test.sqlite3'), 'UPLOAD_FOLDER': str(tmp_path / 'uploads')})


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, path, data=None, **kwargs):
    client.get('/ingresar')
    with client.session_transaction() as state:
        token = state['csrf']
    payload = data.copy() if isinstance(data, MultiDict) else MultiDict((key, value) for key, value in (data or {}).items())
    payload['csrf'] = token
    return client.post(path, data=payload, **kwargs)


def user(app, client, identifier='one', admin=False):
    store = app.extensions['store']
    store.add('usuarios', dict(id=identifier, nombre='Persona ' + identifier, email=identifier + '@example.com',
              password_hash=generate_password_hash('test-password-123'), rol='admin' if admin else 'usuario',
              creado='2026-10-02T00:00:00+00:00'))
    with client.session_transaction() as state:
        state['user_id'] = identifier
    return identifier


def picture():
    output = BytesIO()
    Image.new('RGB', (40, 40), 'green').save(output, 'PNG')
    output.seek(0)
    return output


def sport_form():
    return dict(nombre='Deporte de prueba', descripcion='Descripción de la disciplina.', objetivo='salud',
                costo='150', minutos='45', espacio='exterior', dificultad='basica', equipamiento='Balón.',
                consejos='Comenzar de forma progresiva.', alimentacion='Alimentación variada.',
                condiciones='Un espacio despejado.', beneficios='Coordinación y resistencia.')


@pytest.mark.parametrize('path', ['/', '/deportes/futbol', '/registro', '/ingresar', '/comparar',
    '/herramientas', '/herramientas/presupuesto', '/herramientas/desgaste', '/herramientas/plan',
    '/herramientas/compras', '/deportes/futbol/reportar', '/catalogo/resultados'])
def test_public_pages(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers['X-Content-Type-Options'] == 'nosniff'


def test_catalog_filters_and_details(app, client):
    response = client.get('/catalogo/resultados?q=FUTBOL&costo=bajo').get_json()
    assert response['count'] == 1
    assert 'Fútbol' in response['html']
    assert 'data-pick="futbol"' in response['html']
    assert client.get('/catalogo/resultados?q=tenis&costo=bajo').get_json()['count'] == 0
    assert client.get('/catalogo/resultados?costo=otro').status_code == 400
    detail = client.get('/deportes/futbol').get_data(as_text=True)
    for word in ['Tu primer paso', 'El lugar adecuado', 'Alimentación e hidratación', 'Lo que necesitas']:
        assert word in detail
    app.extensions['store'].update('deportes', 'futbol', {'costo': None})
    assert 'Por confirmar' in client.get('/deportes/futbol').get_data(as_text=True)
    assert client.get('/catalogo/resultados?q=futbol&costo=bajo').get_json()['count'] == 0


def test_auth_persistence_and_public_role(app, client):
    assert client.post('/registro', data={'nombre': 'X'}).status_code == 400
    response = post(client, '/registro', dict(nombre='Ana', email='ANA@example.com', password='my-password-123',
                    confirmacion='my-password-123', rol='admin'))
    assert response.status_code == 302
    stored = app.extensions['store'].all('usuarios', email='ana@example.com')[0]
    assert stored['rol'] == 'usuario'
    assert stored['password_hash'] != 'my-password-123'
    assert post(client, '/ingresar', {'email': 'ana@example.com', 'password': 'wrong'}).status_code == 400
    assert post(client, '/ingresar', {'email': 'ana@example.com', 'password': 'my-password-123'}).status_code == 302
    assert client.get('/admin').status_code == 403
    assert post(client, '/favoritos/futbol/agregar').status_code == 302
    post(client, '/salir')
    assert client.get('/favoritos').status_code == 302
    post(client, '/ingresar', {'email': 'ana@example.com', 'password': 'my-password-123'})
    assert 'Fútbol' in client.get('/favoritos').get_data(as_text=True)
    assert post(client, '/registro', dict(nombre='Ana', email='ana@example.com', password='my-password-123', confirmacion='my-password-123')).status_code == 400


def test_favorites_are_private_and_survive_inactivity(app, client):
    user(app, client)
    post(client, '/favoritos/futbol/agregar')
    post(client, '/favoritos/futbol/agregar')
    assert len(app.extensions['store'].all('favoritos')) == 1
    other = app.test_client()
    user(app, other, 'two')
    assert 'Aquí empieza tu lista' in other.get('/favoritos').get_data(as_text=True)
    post(other, '/favoritos/futbol/quitar')
    assert len(app.extensions['store'].all('favoritos')) == 1
    app.extensions['store'].update('deportes', 'futbol', {'activo': False})
    assert 'No disponible' in client.get('/favoritos').get_data(as_text=True)
    assert post(client, '/favoritos/futbol/agregar').status_code == 404
    post(client, '/favoritos/futbol/quitar')
    assert not app.extensions['store'].all('favoritos')


def test_profile_and_recommendation(app, client):
    user(app, client)
    assert client.get('/recomendaciones').status_code == 302
    payload = dict(edad='22', peso='70', altura='175', sexo='no_indicar', experiencia='principiante',
                   objetivo='social', presupuesto='200', dias='3', minutos='60', id='someone-else')
    assert post(client, '/perfil', payload).status_code == 302
    assert app.extensions['store'].get('perfiles', 'one')['objetivo'] == 'social'
    assert app.extensions['store'].get('perfiles', 'someone-else') is None
    response = client.get('/recomendaciones')
    assert response.status_code == 200
    assert 'Coincide con tu objetivo' in response.get_data(as_text=True)
    other = app.test_client()
    user(app, other, 'two')
    assert other.get('/recomendaciones').status_code == 302
    assert post(client, '/perfil', {**payload, 'presupuesto': 'NaN'}).status_code == 400
    assert app.extensions['store'].get('perfiles', 'one')['presupuesto'] == 200


def test_comparison_and_snapshot_pdf(app, client):
    assert client.get('/comparar?deporte=futbol').status_code == 400
    assert client.get('/comparar?deporte=futbol&deporte=futbol').status_code == 400
    assert client.get('/comparar?preseleccion=futbol').status_code == 200
    response = client.get('/comparar?deporte=futbol&deporte=tenis')
    assert response.status_code == 200
    snapshot = html.unescape(re.search(r'name="snapshot" value="([^"]+)"', response.get_data(as_text=True)).group(1))
    app.extensions['store'].update('deportes', 'futbol', {'costo': 999})
    pdf = post(client, '/comparar/pdf', {'snapshot': snapshot})
    assert pdf.status_code == 200
    assert pdf.data.startswith(b'%PDF-') and len(pdf.data) > 1000
    assert 'attachment' in pdf.headers['Content-Disposition']
    assert post(client, '/comparar/pdf', {'snapshot': snapshot + 'bad'}).status_code == 302


def test_admin_create_edit_activate_delete_and_image(app, client):
    assert client.get('/admin').status_code == 302
    user(app, client, admin=True)
    assert client.get('/admin').status_code == 200
    assert client.get('/admin/deportes/nuevo').status_code == 200
    payload = sport_form()
    response = post(client, '/admin/deportes/nuevo', {**payload, 'imagen': (picture(), 'image.png')})
    assert response.status_code == 302
    created = [s for s in app.extensions['store'].all('deportes') if s['nombre'] == payload['nombre']][0]
    assert client.get(created['imagen']).status_code == 200
    assert post(client, f'/admin/deportes/{created["id"]}/editar', {**payload, 'costo': '-2'}).status_code == 400
    assert app.extensions['store'].get('deportes', created['id'])['costo'] == 150
    assert post(client, f'/admin/deportes/{created["id"]}/editar', {**payload, 'nombre': 'Nombre actualizado'}).status_code == 302
    assert post(client, f'/admin/deportes/{created["id"]}/estado', {'activo': '0'}).status_code == 302
    assert 'Nombre actualizado' not in app.test_client().get('/').get_data(as_text=True)
    assert post(client, f'/admin/deportes/{created["id"]}/estado', {'activo': 'other'}).status_code == 400
    post(client, f'/admin/deportes/{created["id"]}/estado', {'activo': '1'})
    assert post(client, f'/admin/deportes/{created["id"]}/eliminar', {'confirmacion': 'wrong'}).status_code == 302
    assert app.extensions['store'].get('deportes', created['id']) is not None
    post(client, f'/admin/deportes/{created["id"]}/eliminar', {'confirmacion': created['id']})
    assert app.extensions['store'].get('deportes', created['id']) is None


def test_reports_authorization_and_restricted_delete(app, client):
    assert post(client, '/deportes/futbol/reportar', {'campo': 'costos', 'descripcion': ' '}).status_code == 400
    assert post(client, '/deportes/futbol/reportar', {'campo': 'costos', 'descripcion': '<script>alert(1)</script>'}).status_code == 302
    report = app.extensions['store'].all('reportes')[0]
    assert post(client, '/admin/reportes/' + report['id'], {'estado': 'resuelto'}).status_code == 302
    user(app, client, admin=True)
    body = client.get('/admin').get_data(as_text=True)
    assert '<script>alert(1)</script>' not in body
    assert '&lt;script&gt;' in body
    post(client, '/admin/deportes/futbol/eliminar', {'confirmacion': 'futbol'})
    assert app.extensions['store'].get('deportes', 'futbol') is not None
    assert post(client, '/admin/reportes/' + report['id'], {'estado': 'resuelto'}).status_code == 302
    assert app.extensions['store'].get('reportes', report['id'])['estado'] == 'resuelto'
    assert app.extensions['store'].get('deportes', 'futbol')['costo'] == 120


def test_reject_fake_image_and_invalid_csrf(app, client):
    user(app, client, admin=True)
    assert post(client, '/admin/deportes/nuevo', {**sport_form(), 'imagen': (BytesIO(b'not image'), 'image.jpg')}).status_code == 400
    assert len(app.extensions['store'].all('deportes')) == 5
    assert client.post('/salir', data={'csrf': 'ñ-token'}).status_code == 400


def test_budget_exact_decimal_and_form(client):
    data = {'meses': '3', 'deporte': 'futbol'}
    for key in CATEGORIES:
        data[key] = '0'
        data[key + '_tipo'] = 'unico'
    data.update(cuotas='100.10', cuotas_tipo='mensual', equipo='250.25')
    result = budget(data)
    assert result['total'] == Decimal('550.55')
    assert sum(line['total'] for line in result['lines']) == result['total']
    assert post(client, '/herramientas/presupuesto', data).status_code == 200
    assert post(client, '/herramientas/presupuesto', {**data, 'meses': '0'}).status_code == 400


@pytest.mark.parametrize('bad', ['NaN', 'Infinity', '-1', 'abc', '1e999999', None])
def test_invalid_numbers(bad):
    with pytest.raises(ValueError):
        number(bad, 'Valor')


def test_wear_and_shopping(client):
    data = {'implemento': 'Zapatillas', 'antiguedad': '4', 'vida': '12', 'referencia': '3', 'frecuencia': '6'}
    assert wear(data)['remaining'] == 2
    assert wear({**data, 'antiguedad': '7'})['expired']
    assert post(client, '/herramientas/desgaste', data).status_code == 200
    assert post(client, '/herramientas/desgaste', {**data, 'frecuencia': '0'}).status_code == 400
    data = dict(implemento='Raqueta', nuevo='100', usado='120', estado='bueno', proteccion='no')
    assert shopping(data)['saving'] == -20
    assert 'no ofrece ahorro' in shopping(data)['recommendation']
    assert 'protección' in shopping({**data, 'proteccion': 'si'})['recommendation']
    assert post(client, '/herramientas/compras', data).status_code == 200


def test_plan_limits_and_rest(client):
    form = MultiDict([('nivel','principiante'),('objetivo','salud'),('minutos','20'),('deporte','futbol')])
    for day in range(7):
        form.add('dias', str(day))
    result = plan(form, {'nombre': 'Fútbol'})
    assert result['total'] <= 7 * 20
    assert sum(r['active'] for r in result['rows']) == 3
    assert all(r['minutes'] <= 20 for r in result['rows'])
    assert post(client, '/herramientas/plan', form).status_code == 200
    form.setlist('dias', [])
    assert post(client, '/herramientas/plan', form).status_code == 400


def test_remote_contract_no_silent_fallback(tmp_path):
    config = dict(DATA_BACKEND='supabase', SUPABASE_URL='https://example.supabase.co',
                  SUPABASE_SECRET_KEY='sb_secret_test', DATABASE=str(tmp_path / 'no.sqlite'))
    store = Store(config)
    with patch.object(store, 'request', return_value=[{'id':'futbol'}]) as call:
        assert store.all('deportes', activo=True)[0]['id'] == 'futbol'
        assert 'activo=eq.true' in call.call_args.args[0]
        assert 'sportsinfo_deportes' in call.call_args.args[0]
    with patch.object(store, 'request', side_effect=DataError('offline')):
        with pytest.raises(DataError):
            store.all('deportes')
    assert not (tmp_path / 'no.sqlite').exists()


def test_service_error_is_visible(app, client):
    with patch.object(app.extensions['store'], 'all', side_effect=DataError('No disponible')):
        assert client.get('/').status_code == 503


def test_rate_limit_and_logout(app, client):
    for _ in range(10):
        assert post(client, '/ingresar', {'email':'missing@example.com','password':'bad'}).status_code == 400
    assert post(client, '/ingresar', {'email':'missing@example.com','password':'bad'}).status_code == 429


def test_local_store_survives_app_restart(app, client):
    user(app, client)
    post(client, '/favoritos/tenis/agregar')
    restarted = create_app({'TESTING':True, 'DATA_BACKEND':'local', 'DATABASE':app.config['DATABASE']})
    assert len(restarted.extensions['store'].all('favoritos', usuario_id='one')) == 1


def test_deleted_seed_does_not_return_on_restart(app):
    app.extensions['store'].delete('deportes', 'futbol')
    restarted = create_app({'TESTING':True, 'DATA_BACKEND':'local', 'DATABASE':app.config['DATABASE']})
    assert restarted.extensions['store'].get('deportes', 'futbol') is None


def test_pdf_supports_long_descriptions(app):
    from sportsinfo.pdf import render_pdf
    from sportsinfo.routes import FIELDS, sport_cost
    sports = app.extensions['store'].all('deportes')[:3]
    for sport in sports:
        sport['equipamiento'] = 'Equipamiento deportivo para practicar. ' * 75
        sport['condiciones'] = 'Espacio e instalaciones adecuadas. ' * 85
    result = render_pdf({'sports': sports, 'created': '2026-10-02'}, FIELDS, sport_cost)
    assert result.startswith(b'%PDF-') and len(result) > 3000


def test_normal_user_cannot_write_admin_routes(app, client):
    user(app, client)
    assert post(client, '/admin/deportes/nuevo', sport_form()).status_code == 403
    assert post(client, '/admin/deportes/futbol/editar', sport_form()).status_code == 403
    assert post(client, '/admin/deportes/futbol/estado', {'activo':'0'}).status_code == 403
    assert post(client, '/admin/deportes/futbol/eliminar', {'confirmacion':'futbol'}).status_code == 403
    assert app.extensions['store'].get('deportes','futbol')['activo']
