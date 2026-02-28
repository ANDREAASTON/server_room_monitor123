-- ============================================================
-- 1. TELEMETRY TABLE
-- ============================================================
create table if not exists public.telemetry (
    id           uuid        primary key default gen_random_uuid(),
    created_at   timestamptz not null    default now(),
    device_id    text        not null,
    temperature_c numeric,
    humidity_pct  numeric,
    gas_alert    boolean     not null,
    grid_present boolean     not null,
    power_source text        not null check (power_source in ('GRID','BACKUP')),
    alarm_active boolean     not null
);

-- ============================================================
-- 2. INDEXES
-- ============================================================
create index if not exists idx_telemetry_created_at
    on public.telemetry (created_at desc);

create index if not exists idx_telemetry_device_id
    on public.telemetry (device_id);

-- ============================================================
-- 3. ROW LEVEL SECURITY
-- ============================================================
alter table public.telemetry enable row level security;

-- Authenticated users (dashboard) can SELECT rows
create policy "Authenticated users can read telemetry"
    on public.telemetry
    for select
    to authenticated
    using (true);

-- Inserts are performed by the Pi using the service role key.
-- The service role bypasses RLS automatically — no insert policy needed.
-- For defence-in-depth you may also add:
create policy "Service role insert only"
    on public.telemetry
    for insert
    to service_role
    with check (true);

-- Deny all mutations from anon / authenticated roles
create policy "No updates"
    on public.telemetry
    for update
    to authenticated, anon
    using (false);

create policy "No deletes"
    on public.telemetry
    for delete
    to authenticated, anon
    using (false);

-- ============================================================
-- 4. SUPABASE AUTH — no SQL needed
--    Go to Authentication > Settings in the Supabase dashboard:
--    - Enable "Email" provider
--    - Disable "Confirm email" for quick testing (re-enable in production)
--    - Invite users via Authentication > Users > Invite User
-- ============================================================
