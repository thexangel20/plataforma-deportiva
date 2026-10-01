import io
import unittest
from unittest.mock import patch

from PIL import Image
from werkzeug.security import generate_password_hash

from app import app
from app.deportes import descartar_imagen, preparar_imagen
from app.servicios import ErrorDatos, consultar, solicitar


class PruebasHistorias(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hash = generate_password_hash('prueba-administrador')

    def setUp(self):
        self.configuracion = patch.dict(app.config, {
            'TESTING': True, 'SECRET_KEY': 'clave-de-pruebas',
            'SUPABASE_URL': '', 'SUPABASE_SECRET_KEY': '',
            'ADMIN_USUARIO': 'axel', 'ADMIN_PASSWORD_HASH': self.hash,
        })
        self.configuracion.start()
        self.addCleanup(self.configuracion.stop)
        self.cliente = app.test_client()
        self.deporte = {
            'identificador': 'futbol', 'nombre': 'Fútbol',
            'costo_estimado': None, 'moneda': 'BOB', 'periodo_costo': '',
            'equipamiento': '', 'tiempo_practica': '', 'alimentacion': '',
            'recomendaciones': '', 'condiciones': '', 'imagen_ruta': None,
        }

    def csrf(self, administrador=False):
        with self.cliente.session_transaction() as sesion:
            sesion['csrf'] = 'token-prueba'
            if administrador:
                sesion['administrador'] = True
        return 'token-prueba'

    def conectar(self):
        app.config.update(SUPABASE_URL='https://prueba.supabase.co',
                          SUPABASE_SECRET_KEY='sb_secret_prueba')

    def formulario(self):
        return {'csrf': self.csrf(True), 'nombre': 'Fútbol actualizado',
                'moneda': 'BOB', 'costo_estimado': '80.50',
                'periodo_costo': 'Por mes', 'equipamiento': 'Balón'}

    def test_paginas_publicas_y_formulario(self):
        for ruta in ('/', '/deportes/futbol', '/deportes/futbol/reportar', '/admin/ingresar'):
            self.assertEqual(self.cliente.get(ruta).status_code, 200)
        self.assertIn(b'<form', self.cliente.get('/deportes/futbol/reportar').data)
        self.assertEqual(self.cliente.get('/deportes/inexistente').status_code, 404)

    def test_rutas_administrativas_protegidas(self):
        for ruta in ('/admin/reportes', '/admin/deportes', '/admin/deportes/futbol/editar'):
            self.assertEqual(self.cliente.get(ruta).status_code, 302)
        for ruta in ('/admin/reportes/1/revisar', '/admin/deportes/futbol/editar', '/admin/salir'):
            self.assertEqual(self.cliente.post(ruta).status_code, 302)

    def test_csrf_y_validacion_reporte(self):
        with patch('app.reportes.consultar') as consulta:
            self.assertEqual(self.cliente.post('/deportes/futbol/reportar').status_code, 400)
            for campo, descripcion in [('Otro', ' '), ('Inventado', 'Error'), ('Otro', 'a' * 1001)]:
                respuesta = self.cliente.post('/deportes/futbol/reportar', data={
                    'csrf': self.csrf(), 'campo': campo, 'descripcion': descripcion})
                self.assertEqual(respuesta.status_code, 400)
            consulta.assert_not_called()

    def test_guardar_reporte_y_redirigir(self):
        with patch('app.reportes.consultar', return_value=[{'id': 1}]) as consulta:
            respuesta = self.cliente.post('/deportes/futbol/reportar', data={
                'csrf': self.csrf(), 'campo': 'Costos', 'descripcion': 'Cambió el precio'})
            self.assertEqual(respuesta.status_code, 302)
            self.assertEqual(consulta.call_args.kwargs['datos']['estado'], 'pendiente')
            self.assertIn('enviado correctamente', self.cliente.get(respuesta.location).text)

    def test_error_guardado_conserva_y_escapa_descripcion(self):
        with patch('app.reportes.consultar', side_effect=ErrorDatos('Error de conexión')):
            respuesta = self.cliente.post('/deportes/futbol/reportar', data={
                'csrf': self.csrf(), 'campo': 'Otro', 'descripcion': '<script>alert(1)</script>'})
            self.assertEqual(respuesta.status_code, 503)
            self.assertIn('&lt;script&gt;', respuesta.text)
            self.assertNotIn('<script>', respuesta.text)

    def test_ingreso_y_salida(self):
        self.assertEqual(self.cliente.post('/admin/ingresar', data={
            'csrf': self.csrf(), 'usuario': 'axel', 'contrasena': 'incorrecta'}).status_code, 401)
        respuesta = self.cliente.post('/admin/ingresar', data={
            'csrf': self.csrf(), 'usuario': 'axel', 'contrasena': 'prueba-administrador'})
        self.assertEqual(respuesta.status_code, 302)
        with self.cliente.session_transaction() as sesion:
            self.assertTrue(sesion['administrador'])
            token = sesion['csrf']
            self.assertNotEqual(token, 'token-prueba')
        self.assertEqual(self.cliente.post('/admin/salir', data={'csrf': token}).status_code, 302)
        self.assertEqual(self.cliente.get('/admin/reportes').status_code, 302)

    def test_listado_paginado_y_revision(self):
        self.csrf(True)
        reporte = {'id': 1, 'deporte': 'futbol', 'campo_observado': 'Costos',
                   'descripcion': 'Error', 'estado': 'pendiente', 'fecha_creacion': '2026-10-01'}
        with patch('app.reportes.consultar', return_value=[reporte] * 51) as consulta:
            respuesta = self.cliente.get('/admin/reportes?estado=todos&pagina=2')
            self.assertEqual(respuesta.status_code, 200)
            self.assertIn('Siguiente', respuesta.text)
            self.assertEqual(consulta.call_args.kwargs['parametros']['offset'], 50)
            self.assertNotIn('estado', consulta.call_args.kwargs['parametros'])
        with patch('app.reportes.consultar', return_value=[reporte]) as consulta:
            self.assertEqual(self.cliente.post('/admin/reportes/1/revisar', data={'csrf': 'token-prueba'}).status_code, 302)
            self.assertEqual(consulta.call_args.kwargs['datos']['estado'], 'revisado')
        self.assertEqual(self.cliente.get('/admin/reportes?estado=incorrecto').status_code, 400)

    def test_edicion_guarda_y_consulta_publica(self):
        self.conectar()
        formulario = self.formulario()
        with patch('app.deportes.consultar', side_effect=[[self.deporte], [self.deporte]]) as consulta:
            respuesta = self.cliente.post('/admin/deportes/futbol/editar', data=formulario)
            self.assertEqual(respuesta.status_code, 302)
            datos = consulta.call_args.kwargs['datos']
            self.assertEqual(datos['costo_estimado'], '80.50')
            self.assertNotIn('imagen_ruta', datos)
        actualizado = self.deporte | datos
        with patch('app.deportes.consultar', return_value=[actualizado]):
            self.assertIn('Fútbol actualizado', self.cliente.get(respuesta.location).text)
        with patch('app.routes.consultar', return_value=[actualizado]):
            self.assertIn('80.50', self.cliente.get('/').text)

    def test_costos_invalidos_no_se_guardan(self):
        self.conectar()
        for costo in ('-1', 'NaN', 'Infinity', '1.234', '100000000', 'abc'):
            formulario = self.formulario() | {'costo_estimado': costo}
            with patch('app.deportes.consultar', return_value=[self.deporte]) as consulta:
                respuesta = self.cliente.post('/admin/deportes/futbol/editar', data=formulario)
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(consulta.call_count, 1)

    def test_edicion_rechaza_csrf_y_deporte_inexistente(self):
        self.conectar()
        formulario = self.formulario()
        with patch('app.deportes.consultar', return_value=[self.deporte]) as consulta:
            self.assertEqual(self.cliente.post('/admin/deportes/futbol/editar', data=formulario | {'csrf': 'falso'}).status_code, 400)
            consulta.assert_not_called()
        with patch('app.deportes.consultar', return_value=[]):
            self.assertEqual(self.cliente.get('/admin/deportes/no-existe/editar').status_code, 404)

    def test_imagen_valida_e_invalida(self):
        imagen = io.BytesIO()
        Image.new('RGB', (10, 10)).save(imagen, format='PNG')
        imagen.seek(0)
        self.assertTrue(preparar_imagen(imagen).startswith(b'\xff\xd8'))
        with self.assertRaises(ValueError):
            preparar_imagen(io.BytesIO(b'<html>archivo falso</html>'))
        with self.assertRaises(ValueError):
            preparar_imagen(io.BytesIO(b'a' * (5 * 1024 * 1024 + 1)))

    def test_reemplazo_imagen_y_limpieza_si_falla_guardado(self):
        self.conectar()
        formulario = self.formulario()
        imagen = io.BytesIO()
        Image.new('RGB', (10, 10)).save(imagen, format='PNG')
        imagen.seek(0)
        with patch('app.deportes.consultar', side_effect=[[self.deporte], ErrorDatos('Error de guardado')]), patch('app.deportes.subir_imagen', return_value='deportes/nueva.jpg'), patch('app.deportes.descartar_imagen') as limpiar:
            respuesta = self.cliente.post('/admin/deportes/futbol/editar', data=formulario | {'imagen': (imagen, 'imagen.png')})
            self.assertEqual(respuesta.status_code, 503)
            limpiar.assert_called_once_with('deportes/nueva.jpg', 'futbol')
            self.assertIn('Fútbol actualizado', respuesta.text)

    def test_falta_configuracion_no_simula_guardado(self):
        self.csrf(True)
        self.assertEqual(self.cliente.get('/admin/deportes').status_code, 503)
        self.assertEqual(self.cliente.get('/admin/reportes').status_code, 503)
        self.assertEqual(self.cliente.get('/admin/deportes/futbol/editar').status_code, 503)


    def test_imagen_reemplazada_se_guarda(self):
        self.conectar()
        formulario = self.formulario()
        imagen = io.BytesIO()
        Image.new('RGB', (10, 10)).save(imagen, format='PNG')
        imagen.seek(0)
        with patch('app.deportes.consultar', side_effect=[[self.deporte], [self.deporte]]) as consulta, patch('app.deportes.subir_imagen', return_value='deportes/nueva.jpg'):
            respuesta = self.cliente.post('/admin/deportes/futbol/editar', data=formulario | {'imagen': (imagen, 'imagen.png')})
            self.assertEqual(respuesta.status_code, 302)
            self.assertEqual(consulta.call_args.kwargs['datos']['imagen_ruta'], 'deportes/nueva.jpg')

    def test_limpieza_no_borra_imagen_que_si_se_guardo(self):
        with patch('app.deportes.consultar', return_value=[{'imagen_ruta': 'deportes/nueva.jpg'}]), patch('app.deportes.solicitar') as solicitud:
            descartar_imagen('deportes/nueva.jpg', 'futbol')
            solicitud.assert_not_called()
        with patch('app.deportes.consultar', return_value=[{'imagen_ruta': 'deportes/anterior.jpg'}]), patch('app.deportes.solicitar') as solicitud:
            descartar_imagen('deportes/nueva.jpg', 'futbol')
            self.assertEqual(solicitud.call_args.args[1], 'DELETE')

    def test_transporte_supabase_claves_y_errores(self):
        self.conectar()
        with patch('app.servicios.urlopen') as abrir:
            abrir.return_value.__enter__.return_value.read.return_value = b'[]'
            self.assertEqual(consultar('reportes_hu4'), [])
            solicitud = abrir.call_args.args[0]
            self.assertEqual(solicitud.get_header('Apikey'), 'sb_secret_prueba')
            self.assertIsNone(solicitud.get_header('Authorization'))
            app.config['SUPABASE_SECRET_KEY'] = 'jwt-service-role'
            consultar('reportes_hu4')
            self.assertEqual(abrir.call_args.args[0].get_header('Authorization'), 'Bearer jwt-service-role')
        with patch('app.servicios.urlopen', side_effect=TimeoutError):
            with self.assertRaises(ErrorDatos):
                solicitar('/rest/v1/reportes_hu4')


    def test_reporte_conserva_texto_si_falla_consulta_inicial(self):
        with patch('app.deportes.obtener_deporte', side_effect=ErrorDatos('Conexión interrumpida')), patch('app.reportes.consultar') as guardar:
            respuesta = self.cliente.post('/deportes/futbol/reportar', data={
                'csrf': self.csrf(), 'campo': 'Costos',
                'descripcion': 'Texto que no debo perder'})
            self.assertEqual(respuesta.status_code, 503)
            self.assertIn('Texto que no debo perder', respuesta.text)
            self.assertIn('<form', respuesta.text)
            guardar.assert_not_called()

    def test_edicion_conserva_datos_si_falla_consulta_inicial(self):
        self.conectar()
        formulario = self.formulario()
        with patch('app.deportes.consultar', side_effect=ErrorDatos('Conexión interrumpida')) as consulta:
            respuesta = self.cliente.post('/admin/deportes/futbol/editar', data=formulario)
            self.assertEqual(respuesta.status_code, 503)
            self.assertIn('Fútbol actualizado', respuesta.text)
            self.assertIn('80.50', respuesta.text)
            self.assertIn('Balón', respuesta.text)
            self.assertEqual(consulta.call_count, 1)

    def test_imagen_respeta_orientacion_de_camara(self):
        original = Image.new('RGB', (20, 10))
        metadatos = Image.Exif()
        metadatos[274] = 6
        archivo = io.BytesIO()
        original.save(archivo, format='JPEG', exif=metadatos)
        archivo.seek(0)
        resultado = preparar_imagen(archivo)
        with Image.open(io.BytesIO(resultado)) as imagen:
            self.assertEqual(imagen.size, (10, 20))


if __name__ == '__main__':
    unittest.main()
