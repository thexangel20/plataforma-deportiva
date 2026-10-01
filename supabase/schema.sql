-- Esquema requerido por la HU21 - Comparar deportes.
-- Ejecutar en el SQL Editor de Supabase antes de conectar el entorno real.

create table if not exists public.deportes (
    id text primary key,
    nombre text not null unique,
    icono text not null default '🏅',
    descripcion text not null default '',
    objetivo text not null default '',
    costo numeric(10, 2) not null check (costo >= 0),
    moneda text not null default 'Bs.',
    duracion_minutos integer not null check (duracion_minutos > 0),
    equipamiento jsonb not null default '[]'::jsonb,
    recomendaciones jsonb not null default '[]'::jsonb,
    imagen_url text,
    activo boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

insert into public.deportes (
    id, nombre, icono, descripcion, objetivo, costo, duracion_minutos,
    equipamiento, recomendaciones
)
values
(
    'futbol', 'Fútbol', '⚽',
    'Deporte colectivo de alta intensidad y coordinación.',
    'Resistencia y trabajo en equipo', 150, 90,
    '["Balón", "Zapatillas deportivas", "Camiseta"]'::jsonb,
    '["Realizar calentamiento antes de entrenar.", "Mantener una buena hidratación."]'::jsonb
),
(
    'baloncesto', 'Baloncesto', '🏀',
    'Disciplina dinámica que combina velocidad, precisión y estrategia.',
    'Agilidad y coordinación', 120, 90,
    '["Balón de baloncesto", "Zapatillas deportivas", "Ropa cómoda"]'::jsonb,
    '["Practicar lanzamientos y desplazamientos.", "Usar calzado con buen soporte."]'::jsonb
),
(
    'natacion', 'Natación', '🏊',
    'Actividad de bajo impacto que ejercita todo el cuerpo.',
    'Resistencia y bienestar físico', 200, 60,
    '["Traje de baño", "Gafas de natación", "Gorro de natación"]'::jsonb,
    '["Comenzar con una intensidad progresiva.", "Respetar las normas de seguridad de la piscina."]'::jsonb
),
(
    'tenis', 'Tenis', '🎾',
    'Deporte individual que desarrolla precisión, velocidad y estrategia.',
    'Coordinación y concentración', 300, 120,
    '["Raqueta", "Pelotas de tenis", "Zapatillas de cancha"]'::jsonb,
    '["Practicar la técnica con supervisión.", "Realizar pausas de recuperación durante la sesión."]'::jsonb
)
on conflict (id) do update set
    nombre = excluded.nombre,
    icono = excluded.icono,
    descripcion = excluded.descripcion,
    objetivo = excluded.objetivo,
    costo = excluded.costo,
    duracion_minutos = excluded.duracion_minutos,
    equipamiento = excluded.equipamiento,
    recomendaciones = excluded.recomendaciones,
    updated_at = now();
