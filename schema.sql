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