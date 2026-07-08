-- مسیر فایل: storage/schema.sql
-- اجرای این اسکریپت در Supabase → SQL Editor
-- مطابق architecture.md بخش ۹
-- مسیر فایل: storage/schema.sql
-- اجرای این اسکریپت در Supabase → SQL Editor

create table if not exists ohlcv_cache (
    id bigint generated always as identity primary key,
    symbol text not null,
    timeframe text not null,
    timestamp timestamptz not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    volume double precision not null,
    source text not null,
    created_at timestamptz default now(),
    unique (symbol, timeframe, timestamp)
);

create table if not exists signals (
    id bigint generated always as identity primary key,
    symbol text not null,
    timestamp timestamptz not null,
    direction text not null check (direction in ('bull', 'bear')),
    entry double precision not null,
    stop_loss double precision not null,
    tp1 double precision,
    tp2 double precision,
    tp3 double precision,
    ml_confidence double precision,
    status text not null default 'pending'
        check (status in ('pending', 'tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'expired')),
    closed_at timestamptz,
    pnl_pct double precision,
    sent_to_telegram boolean default false,
    params_version text,
    created_at timestamptz default now()
);

create table if not exists model_registry (
    id bigint generated always as identity primary key,
    symbol text not null,
    version text not null,
    trained_at timestamptz not null,
    metrics_json jsonb,
    file_path text,
    is_active boolean default true,
    created_at timestamptz default now()
);

create table if not exists param_history (
    id bigint generated always as identity primary key,
    symbol text not null,
    version text not null,
    effective_from timestamptz not null,
    atr_mult double precision not null,
    tp1_r double precision not null,
    tp2_r double precision not null,
    tp3_r double precision not null,
    ml_threshold double precision not null,
    adjusted_score double precision,
    backtest_weight double precision,
    live_weight double precision,
    accepted boolean not null default false,
    notes text,
    created_at timestamptz default now()
);

create table if not exists backtest_runs (
    id bigint generated always as identity primary key,
    symbol text not null,
    date_range_start timestamptz,
    date_range_end timestamptz,
    metrics_json jsonb,
    report_path text,
    created_at timestamptz default now()
);

create index if not exists idx_signals_symbol_status on signals (symbol, status);
create index if not exists idx
create table if not exists ohlcv_cache (
    id bigint generated always as identity primary key,
    symbol text not null,
    timeframe text not null,
    timestamp timestamptz not null,
    open double precision not null,
    high double precision not null,
    low double precision not null,
    close double precision not null,
    volume double precision not null,
    source text not null,
    created_at timestamptz default now(),
    unique (symbol, timeframe, timestamp)
);

create table if not exists signals (
    id bigint generated always as identity primary key,
    symbol text not null,
    timestamp timestamptz not null,
    direction text not null check (direction in ('bull', 'bear')),
    entry double precision not null,
    stop_loss double precision not null,
    tp1 double precision,
    tp2 double precision,
    tp3 double precision,
    ml_confidence double precision,
    status text not null default 'pending'
        check (status in ('pending', 'tp1_hit', 'tp2_hit', 'tp3_hit', 'sl_hit', 'expired')),
    closed_at timestamptz,
    pnl_pct double precision,
    sent_to_telegram boolean default false,
    params_version text,
    created_at timestamptz default now()
);

create table if not exists model_registry (
    id bigint generated always as identity primary key,
    symbol text not null,
    version text not null,
    trained_at timestamptz not null,
    metrics_json jsonb,
    file_path text,
    is_active boolean default true,
    created_at timestamptz default now()
);

create table if not exists param_history (
    id bigint generated always as identity primary key,
    symbol text not null,
    version text not null,
    effective_from timestamptz not null,
    atr_mult double precision not null,
    tp1_r double precision not null,
    tp2_r double precision not null,
    tp3_r double precision not null,
    ml_threshold double precision not null,
    adjusted_score double precision,
    backtest_weight double precision,
    live_weight double precision,
    accepted boolean not null default false,
    notes text,
    created_at timestamptz default now()
);

create table if not exists backtest_runs (
    id bigint generated always as identity primary key,
    symbol text not null,
    date_range_start timestamptz,
    date_range_end timestamptz,
    metrics_json jsonb,
    report_path text,
    created_at timestamptz default now()
);

-- ایندکس‌های پرکاربرد برای کوئری‌های job ساعتی/ماهانه
create index if not exists idx_signals_symbol_status on signals (symbol, status);
create index if not exists idx_param_history_symbol_accepted on param_history (symbol, accepted, effective_from desc);
create index if not exists idx_ohlcv_cache_symbol_tf on ohlcv_cache (symbol, timeframe, timestamp desc);
