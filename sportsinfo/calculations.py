from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


GOALS = {'salud': 'Bienestar', 'resistencia': 'Resistencia', 'social': 'Conocer personas', 'coordinacion': 'Coordinación'}
LEVELS = {'principiante': 'Principiante', 'intermedio': 'Intermedio', 'avanzado': 'Avanzado'}
CATEGORIES = {'inscripcion': 'Inscripción', 'cuotas': 'Cuotas', 'instalaciones': 'Instalaciones',
              'equipo': 'Equipamiento', 'ropa': 'Ropa', 'transporte': 'Transporte',
              'alimentacion': 'Alimentación', 'otros': 'Otros gastos'}


def number(value, label, minimum=0, maximum=100000, integer=False):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or not minimum <= result <= maximum:
            raise ValueError
        if integer and result != int(result):
            raise ValueError
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{label}: ingresa un valor válido entre {minimum} y {maximum}.') from None
    return int(result) if integer else result


def choice(value, allowed, label):
    if value not in allowed:
        raise ValueError(f'Selecciona una opción válida para {label}.')
    return value


def money(value):
    return Decimal(value).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def budget(form):
    months = number(form.get('meses'), 'Meses', 1, 60, True)
    lines = []
    for key, label in CATEGORIES.items():
        value = money(number(form.get(key, '0') or '0', label))
        period = choice(form.get(key + '_tipo'), ['unico', 'mensual'], 'frecuencia de ' + label)
        lines.append({'label': label, 'amount': value, 'period': period,
                      'total': value * (months if period == 'mensual' else 1)})
    monthly = sum((r['amount'] for r in lines if r['period'] == 'mensual'), Decimal(0))
    once = sum((r['amount'] for r in lines if r['period'] == 'unico'), Decimal(0))
    return {'months': months, 'lines': lines, 'monthly': monthly, 'once': once,
            'total': once + monthly * months}


def wear(form):
    age = number(form.get('antiguedad'), 'Antigüedad en meses', 0, 1200)
    baseline = number(form.get('vida'), 'Vida útil de referencia en meses', 1, 1200)
    reference = number(form.get('referencia'), 'Usos semanales de referencia', 1, 21)
    frequency = number(form.get('frecuencia'), 'Usos por semana', 1, 21)
    life = baseline * reference / frequency
    remaining = max(Decimal(0), life - age)
    return {'life': round(life, 1), 'remaining': round(remaining, 1),
            'percent': round(min(Decimal(100), age / life * 100)),
            'expired': remaining == 0,
            'assumption': f'Referencia: {baseline} meses con {reference} usos por semana. Se supone un desgaste proporcional al uso y una frecuencia constante.'}


def shopping(form):
    new = money(number(form.get('nuevo'), 'Precio nuevo', 1))
    used = money(number(form.get('usado'), 'Precio usado'))
    state = choice(form.get('estado'), ['excelente', 'bueno', 'desgastado'], 'estado')
    safety = choice(form.get('proteccion'), ['si', 'no'], 'equipo de protección')
    saving = new - used
    if safety == 'si':
        recommendation = 'Prioriza un artículo de protección nuevo con certificación y garantía; el precio no permite comprobar daños ocultos.'
    elif state == 'desgastado':
        recommendation = 'El desgaste puede reducir la duración. Prioriza la opción nueva o solicita una revisión antes de comprar.'
    elif saving <= 0:
        recommendation = 'La opción usada no ofrece ahorro. Compara la garantía y las condiciones de la opción nueva.'
    elif saving / new < Decimal('.2'):
        recommendation = 'El ahorro es menor al 20%. La garantía y duración de un artículo nuevo pueden compensar la diferencia.'
    else:
        recommendation = 'La opción usada ofrece ahorro. Revisa su funcionamiento, ajuste y estado real antes de decidir.'
    return {'new': new, 'used': used, 'saving': saving,
            'percent': round(saving / new * 100, 1), 'recommendation': recommendation}


def plan(form, sport):
    level = choice(form.get('nivel'), LEVELS, 'nivel')
    goal = choice(form.get('objetivo'), GOALS, 'objetivo')
    days = form.getlist('dias')
    if not days or len(set(days)) != len(days) or any(d not in '0123456' or len(d) != 1 for d in days):
        raise ValueError('Selecciona al menos un día válido sin duplicados.')
    minutes = number(form.get('minutos'), 'Minutos por sesión', 15, 180, True)
    selected = sorted(map(int, days))
    cap = {'principiante': 3, 'intermedio': 4, 'avanzado': 5}[level]
    selected = selected[:cap]
    duration = min(minutes, {'principiante': 40, 'intermedio': 60, 'avanzado': 90}[level])
    focus = {'salud': 'Técnica a ritmo cómodo', 'resistencia': 'Trabajo de resistencia progresivo',
             'social': 'Ejercicios y juego en grupo', 'coordinacion': 'Ejercicios de precisión y control'}[goal]
    rows = []
    for i, name in enumerate(['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']):
        active = i in selected
        rows.append({'day': name, 'active': active, 'minutes': duration if active else 0,
                     'activity': focus if active else 'Descanso',
                     'detail': f'5 min de calentamiento · {duration - 10} min de práctica · 5 min de vuelta a la calma' if active else 'Recuperación y actividades cotidianas.'})
    return {'rows': rows, 'total': duration * len(selected), 'sport': sport['nombre'],
            'note': f'Plan orientativo para nivel {level}. Máximo {cap} sesiones semanales y descansos reservados. Ajusta la carga a tu respuesta personal.'}


def recommendations(sports, profile):
    result = []
    for sport in sports:
        points, reasons = 0, []
        if profile['objetivo'] in sport['objetivo'].split(','):
            points += 4
            reasons.append('Coincide con tu objetivo de ' + GOALS[profile['objetivo']].lower())
        if sport['costo'] is not None and sport['moneda'] == 'BOB' and sport['periodo'] == 'mes' and sport['costo'] <= profile['presupuesto']:
            points += 3
            reasons.append('Su costo mensual orientativo entra en tu presupuesto')
        if sport['minutos'] <= profile['minutos']:
            points += 2
            reasons.append('La duración habitual cabe en el tiempo que tienes por sesión')
        expected = {'principiante': 'basica', 'intermedio': 'intermedia', 'avanzado': 'alta'}[profile['experiencia']]
        if sport['dificultad'] == expected:
            points += 2
            reasons.append('La dificultad de entrada coincide con tu experiencia')
        if points:
            result.append({'sport': sport, 'points': points, 'reasons': reasons})
    return sorted(result, key=lambda item: (-item['points'], item['sport']['nombre']))[:3]
