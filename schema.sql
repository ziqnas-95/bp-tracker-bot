create table public.bp_readings (
  id           uuid primary key default gen_random_uuid(),
  user_id      bigint      not null,          -- Telegram user ID
  systolic     smallint    not null check (systolic  between 50 and 300),
  diastolic    smallint    not null check (diastolic between 30 and 200),
  pulse        smallint    not null check (pulse     between 20 and 250),
  category     text        not null check (category    in ('green','yellow','orange','red')),
  time_of_day  text        not null check (time_of_day in ('morning','evening')),
  created_at   timestamptz not null default now(),

  constraint systolic_gt_diastolic check (systolic > diastolic)
);

-- Speeds up /recent and /del_recent
create index bp_readings_user_created_idx
  on public.bp_readings (user_id, created_at desc);

-- Block all public access; the bot's service_role key bypasses this
alter table public.bp_readings enable row level security;


create table public.processed_updates (
  update_id  bigint primary key,
  processed_at timestamptz not null default now()
);

create table public.processed_updates_dev
  (like public.processed_updates including all);

alter table public.processed_updates enable row level security;
alter table public.processed_updates_dev enable row level security;


create table public.users (
  id           uuid primary key default gen_random_uuid(),
  telegram_id  bigint not null unique,
  display_name text,
  joined_at    timestamptz not null default now(),
  is_active    boolean not null default true
);

create table public.users_dev (like public.users including all);

alter table public.users enable row level security;
alter table public.users_dev enable row level security;

create index users_telegram_id_idx on public.users (telegram_id);
create index users_dev_telegram_id_idx on public.users_dev (telegram_id);

-- Seed yourself as the owner in BOTH tables, so dev testing also works
insert into public.users (telegram_id, display_name) values (762425917, 'owner');
insert into public.users_dev (telegram_id, display_name) values (762425917, 'owner');