-- Vibe Coder Tycoon — Supabase Schema
-- Run this in the Supabase SQL editor (Dashboard → SQL Editor → New query).
-- Also disable email confirmation in Auth → Settings for frictionless game login.

-- ──────────────────────────────────────────────
-- profiles
-- ──────────────────────────────────────────────
create table if not exists profiles (
  id                      uuid primary key references auth.users(id) on delete cascade,
  username                text unique not null,
  founder_name            text not null default '',
  country_region          text,
  background              text,
  personality             text,
  reputation              integer default 0,
  total_tokens_used       bigint default 0,
  total_projects_launched integer default 0,
  total_companies_created integer default 0,
  public_profile_enabled  boolean default false,
  created_at              timestamptz default now(),
  updated_at              timestamptz default now()
);

alter table profiles enable row level security;

create policy "Users can view their own profile"
  on profiles for select using (auth.uid() = id);

create policy "Users can insert their own profile"
  on profiles for insert with check (auth.uid() = id);

create policy "Users can update their own profile"
  on profiles for update using (auth.uid() = id);

-- Public profiles are visible to anyone (no email exposed)
create policy "Public profiles are readable"
  on profiles for select using (public_profile_enabled = true);

-- ──────────────────────────────────────────────
-- save_slots
-- ──────────────────────────────────────────────
create table if not exists save_slots (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id) on delete cascade,
  slot_name       text not null,
  game_version    text not null,
  client_version  text,
  save_data       jsonb not null,
  checksum        text,
  is_active       boolean default true,
  created_at      timestamptz default now(),
  updated_at      timestamptz default now(),
  last_played_at  timestamptz default now()
);

alter table save_slots enable row level security;

create policy "Users can manage their own save slots"
  on save_slots for all using (auth.uid() = user_id);

-- Auto-update updated_at on upsert
create or replace function update_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger save_slots_updated_at
  before update on save_slots
  for each row execute procedure update_updated_at();

-- ──────────────────────────────────────────────
-- game_runs
-- ──────────────────────────────────────────────
create table if not exists game_runs (
  id                  uuid primary key default gen_random_uuid(),
  user_id             uuid not null references auth.users(id) on delete cascade,
  save_slot_id        uuid references save_slots(id),
  started_at          timestamptz,
  completed_at        timestamptz,
  game_version        text,
  months_survived     integer,
  companies_created   integer,
  projects_launched   integer,
  projects_failed     integer,
  total_revenue       integer,
  total_users         integer,
  final_reputation    integer,
  final_burnout       integer,
  final_rank          text,
  summary             jsonb,
  created_at          timestamptz default now()
);

alter table game_runs enable row level security;

create policy "Users can manage their own game runs"
  on game_runs for all using (auth.uid() = user_id);

-- ──────────────────────────────────────────────
-- leaderboard_entries
-- ──────────────────────────────────────────────
create table if not exists leaderboard_entries (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id) on delete cascade,
  game_run_id  uuid references game_runs(id),
  category     text not null,
  score        numeric not null,
  display_name text not null,
  metadata     jsonb,
  created_at   timestamptz default now()
);

alter table leaderboard_entries enable row level security;

create policy "Users can insert their own leaderboard entries"
  on leaderboard_entries for insert with check (auth.uid() = user_id);

-- Leaderboard is publicly readable (display_name + score only — no private data)
create policy "Leaderboard entries are publicly readable"
  on leaderboard_entries for select using (true);

-- ──────────────────────────────────────────────
-- devices
-- ──────────────────────────────────────────────
create table if not exists devices (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  device_name   text,
  platform      text,
  last_seen_at  timestamptz default now(),
  created_at    timestamptz default now()
);

alter table devices enable row level security;

create policy "Users can manage their own devices"
  on devices for all using (auth.uid() = user_id);

-- ──────────────────────────────────────────────
-- sync_events
-- ──────────────────────────────────────────────
create table if not exists sync_events (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid references auth.users(id) on delete cascade,
  save_slot_id  uuid references save_slots(id),
  event_type    text not null,
  status        text not null,
  message       text,
  created_at    timestamptz default now()
);

alter table sync_events enable row level security;

create policy "Users can manage their own sync events"
  on sync_events for all using (auth.uid() = user_id);
