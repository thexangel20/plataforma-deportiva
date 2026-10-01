alter table public.deportes_axel
    add column if not exists espacio_practica text
        check (espacio_practica in ('interior', 'exterior', 'ambos')),
    add column if not exists instalaciones_especiales text
        check (instalaciones_especiales in ('si', 'no')),
    add column if not exists requiere_companeros text
        check (requiere_companeros in ('si', 'no'));
