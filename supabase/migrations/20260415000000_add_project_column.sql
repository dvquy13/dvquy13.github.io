alter table metrics_snapshots add column if not exists project text not null default '';

create index if not exists metrics_snapshots_project_fetched_at_idx on metrics_snapshots (project, fetched_at desc);
