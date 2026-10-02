begin;

create table if not exists public.sportsinfo_deportes (
 id text primary key,
 nombre text not null check (char_length(nombre) between 2 and 100),
 descripcion text not null,
 objetivo text not null,
 costo numeric(12,2) check (costo is null or costo >= 0),
 moneda text not null default 'BOB',
 periodo text not null default 'mes',
 minutos integer not null check (minutos between 10 and 240),
 equipamiento text not null,
 consejos text not null,
 alimentacion text not null,
 condiciones text not null,
 espacio text not null check (espacio in ('interior','exterior','ambos')),
 dificultad text not null check (dificultad in ('basica','intermedia','alta')),
 beneficios text not null,
 imagen text not null,
 activo boolean not null default true
);

create table if not exists public.sportsinfo_usuarios (
 id text primary key,
 email text unique not null check (email = lower(email)),
 nombre text not null,
 password_hash text not null,
 rol text not null default 'usuario' check (rol in ('usuario','admin')),
 creado timestamptz not null
);

create table if not exists public.sportsinfo_perfiles (
 id text primary key references public.sportsinfo_usuarios(id) on delete cascade,
 edad integer not null check (edad between 13 and 100),
 peso numeric check (peso is null or peso between 20 and 350),
 altura numeric check (altura is null or altura between 80 and 250),
 sexo text not null check (sexo in ('no_indicar','femenino','masculino','otro')),
 experiencia text not null check (experiencia in ('principiante','intermedio','avanzado')),
 objetivo text not null check (objetivo in ('salud','resistencia','social','coordinacion')),
 presupuesto numeric not null check (presupuesto between 0 and 100000),
 dias integer not null check (dias between 1 and 7),
 minutos integer not null check (minutos between 15 and 240)
);

create table if not exists public.sportsinfo_favoritos (
 id text primary key,
 usuario_id text not null references public.sportsinfo_usuarios(id) on delete cascade,
 deporte_id text not null references public.sportsinfo_deportes(id) on delete restrict,
 unique(usuario_id, deporte_id)
);

create table if not exists public.sportsinfo_reportes (
 id text primary key,
 deporte_id text not null references public.sportsinfo_deportes(id) on delete restrict,
 usuario_id text references public.sportsinfo_usuarios(id) on delete set null,
 campo text not null check (campo in ('costos','equipamiento','alimentacion','condiciones','otro')),
 descripcion text not null check (char_length(descripcion) between 10 and 1000),
 estado text not null default 'pendiente' check (estado in ('pendiente','resuelto','descartado')),
 creado timestamptz not null
);

create index if not exists sportsinfo_favoritos_deporte_idx on public.sportsinfo_favoritos(deporte_id);
create index if not exists sportsinfo_reportes_deporte_idx on public.sportsinfo_reportes(deporte_id);
create index if not exists sportsinfo_reportes_estado_idx on public.sportsinfo_reportes(estado,creado);
create index if not exists sportsinfo_deportes_activos_idx on public.sportsinfo_deportes(activo,nombre);

alter table public.sportsinfo_deportes enable row level security;
alter table public.sportsinfo_usuarios enable row level security;
alter table public.sportsinfo_perfiles enable row level security;
alter table public.sportsinfo_favoritos enable row level security;
alter table public.sportsinfo_reportes enable row level security;

revoke all on public.sportsinfo_deportes, public.sportsinfo_usuarios, public.sportsinfo_perfiles,
 public.sportsinfo_favoritos, public.sportsinfo_reportes from anon, authenticated;
grant select, insert, update, delete on public.sportsinfo_deportes, public.sportsinfo_usuarios,
 public.sportsinfo_perfiles, public.sportsinfo_favoritos, public.sportsinfo_reportes to service_role;

insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('sportsinfo-imagenes','sportsinfo-imagenes',true,5242880,array['image/jpeg','image/png','image/webp'])
on conflict(id) do nothing;

commit;
