-- ASHA VoiceCare — Postgres/Supabase schema
-- Mirrors backend/app/db.py (SQLite). Run in the Supabase SQL editor, then set
-- DATABASE_URL and swap the store implementation in app/db.py.

create table if not exists beneficiaries (
    id          text primary key,
    name        text not null,
    village     text,
    household   text,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create table if not exists visits (
    id                 text primary key,
    beneficiary_id     text references beneficiaries(id) on delete set null,
    patient_name       text,
    visit_type         text not null check (visit_type in
        ('pregnancy_anc','newborn_hbnc','postnatal','immunization','family_planning','general')),
    weight_kg          numeric(5,2),
    bp                 text,
    anc_completed      boolean,
    ifa_provided       boolean,
    vaccination_status text check (vaccination_status in ('given','due','not_specified')),
    vaccines_due       text[] default '{}',
    next_visit_date    date,
    observations       text,
    transcript         text not null,
    extracted_json     jsonb not null,
    corrections_json   jsonb not null default '[]',
    danger_json        jsonb not null default '[]',
    status             text not null default 'draft' check (status in ('draft','confirmed')),
    language           text not null,
    extraction_method  text,
    created_at         timestamptz not null default now(),
    confirmed_at       timestamptz
);

create table if not exists danger_alerts (
    id              text primary key,
    visit_id        text not null references visits(id) on delete cascade,
    beneficiary_id  text,
    code            text not null,
    label           text not null,
    category        text not null,
    urgency         text not null,
    matched_text    text,
    source          text,
    referral_status text not null default 'pending'
                    check (referral_status in ('pending','referred','closed')),
    created_at      timestamptz not null default now()
);

create table if not exists followups (
    id             text primary key,
    visit_id       text not null references visits(id) on delete cascade,
    beneficiary_id text,
    title          text not null,
    detail         text,
    due_date       date,
    priority       text not null check (priority in ('urgent','high','normal')),
    reason         text,
    kind           text,
    status         text not null default 'pending' check (status in ('pending','done')),
    created_at     timestamptz not null default now(),
    completed_at   timestamptz
);

create index if not exists idx_visits_created on visits (created_at desc);
create index if not exists idx_followups_status on followups (status, due_date);
create index if not exists idx_alerts_visit on danger_alerts (visit_id);

-- Responsible-AI note: all rows are synthetic demo data. No PHI is stored.
