-- =====================================================================
-- 001_init.sql  -  Personalized Travel Itinerary Planner
-- =====================================================================

-- ---------- TABLES ----------

create table public.profiles (
  id             uuid primary key references auth.users(id) on delete cascade,
  display_name   text,
  home_currency  text not null default 'INR',
  preferences    jsonb not null default '{}'::jsonb,
  created_at     timestamptz not null default now()
);

create table public.trips (
  id             uuid primary key default gen_random_uuid(),
  owner_id       uuid not null references public.profiles(id) on delete cascade,
  title          text not null,
  destination    text not null,
  start_date     date not null,
  end_date       date not null,
  budget         numeric(12,2) check (budget is null or budget >= 0),
  currency       text not null default 'INR',
  group_size     int  not null default 1 check (group_size between 1 and 50),
  travel_style   text not null default 'balanced'
                 check (travel_style in ('relaxed','balanced','packed')),
  interests      text[] not null default '{}',
  notes          text,
  status         text not null default 'ready'
                 check (status in ('generating','ready','failed')),
  error_message  text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint trips_dates_valid check (end_date >= start_date),
  constraint trips_max_14_days check (end_date - start_date <= 13)
);

-- The owner lives in trips.owner_id. This table holds invited people only.
create table public.trip_members (
  trip_id     uuid not null references public.trips(id) on delete cascade,
  user_id     uuid not null references public.profiles(id) on delete cascade,
  role        text not null default 'viewer' check (role in ('editor','viewer')),
  created_at  timestamptz not null default now(),
  primary key (trip_id, user_id)
);

create table public.itinerary_days (
  id              uuid primary key default gen_random_uuid(),
  trip_id         uuid not null references public.trips(id) on delete cascade,
  day_number      int  not null check (day_number >= 1),
  date            date,
  summary         text,
  estimated_cost  numeric(12,2) not null default 0,
  unique (trip_id, day_number)
);

create table public.activities (
  id              uuid primary key default gen_random_uuid(),
  day_id          uuid not null references public.itinerary_days(id) on delete cascade,
  position        int  not null default 0,
  start_time      time,
  end_time        time,
  type            text not null default 'attraction'
                  check (type in ('attraction','meal','stay','transport','other')),
  title           text not null,
  description     text,
  location_name   text,
  lat             double precision,
  lng             double precision,
  estimated_cost  numeric(12,2) not null default 0,
  notes           text,
  created_at      timestamptz not null default now()
);

create table public.generation_logs (
  id              uuid primary key default gen_random_uuid(),
  trip_id         uuid not null references public.trips(id) on delete cascade,
  prompt_version  text,
  model           text,
  tokens_used     int,
  latency_ms      int,
  success         boolean not null default false,
  error           text,
  created_at      timestamptz not null default now()
);

-- ---------- INDEXES ----------

create index idx_trips_owner        on public.trips(owner_id);
create index idx_members_user       on public.trip_members(user_id);
create index idx_days_trip          on public.itinerary_days(trip_id);
create index idx_activities_day     on public.activities(day_id, position);
create index idx_logs_trip          on public.generation_logs(trip_id);

-- ---------- updated_at TRIGGER ----------

create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger trips_set_updated_at
  before update on public.trips
  for each row execute function public.set_updated_at();

-- ---------- AUTO-CREATE PROFILE ON SIGNUP ----------

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- ACCESS HELPER FUNCTIONS ----------
-- SECURITY DEFINER lets policies check other tables without recursion.

create or replace function public.is_trip_owner(p_trip_id uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.trips
    where id = p_trip_id and owner_id = auth.uid()
  );
$$;

create or replace function public.has_trip_access(p_trip_id uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.trips t
    where t.id = p_trip_id
      and (t.owner_id = auth.uid()
           or exists (select 1 from public.trip_members m
                      where m.trip_id = t.id and m.user_id = auth.uid()))
  );
$$;

create or replace function public.can_edit_trip(p_trip_id uuid)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (
    select 1 from public.trips t
    where t.id = p_trip_id
      and (t.owner_id = auth.uid()
           or exists (select 1 from public.trip_members m
                      where m.trip_id = t.id and m.user_id = auth.uid()
                        and m.role = 'editor'))
  );
$$;

create or replace function public.day_trip_id(p_day_id uuid)
returns uuid language sql stable security definer set search_path = public as $$
  select trip_id from public.itinerary_days where id = p_day_id;
$$;

-- Only signed-in users may call the helpers
revoke execute on function public.is_trip_owner(uuid)   from public, anon;
revoke execute on function public.has_trip_access(uuid) from public, anon;
revoke execute on function public.can_edit_trip(uuid)   from public, anon;
revoke execute on function public.day_trip_id(uuid)     from public, anon;
grant  execute on function public.is_trip_owner(uuid)   to authenticated;
grant  execute on function public.has_trip_access(uuid) to authenticated;
grant  execute on function public.can_edit_trip(uuid)   to authenticated;
grant  execute on function public.day_trip_id(uuid)     to authenticated;

-- ---------- ROW LEVEL SECURITY ----------

alter table public.profiles        enable row level security;
alter table public.trips           enable row level security;
alter table public.trip_members    enable row level security;
alter table public.itinerary_days  enable row level security;
alter table public.activities      enable row level security;
alter table public.generation_logs enable row level security;

-- profiles: each user sees and edits only their own
create policy profiles_select on public.profiles for select to authenticated
  using ((select auth.uid()) = id);
create policy profiles_update on public.profiles for update to authenticated
  using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

-- trips: owner and members read; only the owner creates, updates, deletes
create policy trips_select on public.trips for select to authenticated
  using (owner_id = (select auth.uid()) or public.has_trip_access(id));
create policy trips_insert on public.trips for insert to authenticated
  with check (owner_id = (select auth.uid()));
create policy trips_update on public.trips for update to authenticated
  using (owner_id = (select auth.uid())) with check (owner_id = (select auth.uid()));
create policy trips_delete on public.trips for delete to authenticated
  using (owner_id = (select auth.uid()));

-- trip_members: the owner manages; a member can see and remove their own row
create policy members_select on public.trip_members for select to authenticated
  using (user_id = (select auth.uid()) or public.is_trip_owner(trip_id));
create policy members_insert on public.trip_members for insert to authenticated
  with check (public.is_trip_owner(trip_id));
create policy members_update on public.trip_members for update to authenticated
  using (public.is_trip_owner(trip_id)) with check (public.is_trip_owner(trip_id));
create policy members_delete on public.trip_members for delete to authenticated
  using (user_id = (select auth.uid()) or public.is_trip_owner(trip_id));

-- itinerary_days: readable by anyone with access, editable by owner and editors
create policy days_select on public.itinerary_days for select to authenticated
  using (public.has_trip_access(trip_id));
create policy days_insert on public.itinerary_days for insert to authenticated
  with check (public.can_edit_trip(trip_id));
create policy days_update on public.itinerary_days for update to authenticated
  using (public.can_edit_trip(trip_id)) with check (public.can_edit_trip(trip_id));
create policy days_delete on public.itinerary_days for delete to authenticated
  using (public.can_edit_trip(trip_id));

-- activities: access is inherited from the trip through the day
create policy activities_select on public.activities for select to authenticated
  using (public.has_trip_access(public.day_trip_id(day_id)));
create policy activities_insert on public.activities for insert to authenticated
  with check (public.can_edit_trip(public.day_trip_id(day_id)));
create policy activities_update on public.activities for update to authenticated
  using (public.can_edit_trip(public.day_trip_id(day_id)))
  with check (public.can_edit_trip(public.day_trip_id(day_id)));
create policy activities_delete on public.activities for delete to authenticated
  using (public.can_edit_trip(public.day_trip_id(day_id)));

-- generation_logs: append-only for people who can edit the trip
create policy logs_select on public.generation_logs for select to authenticated
  using (public.has_trip_access(trip_id));
create policy logs_insert on public.generation_logs for insert to authenticated
  with check (public.can_edit_trip(trip_id));