-- Create sessions table
create table if not exists sessions (
    session_id uuid primary key,
    user_id bigint references users(user_id) not null,
    token text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    expiry timestamp with time zone not null,
    is_active boolean default true not null
);

-- Create indexes for faster lookups
create index if not exists idx_sessions_user_id on sessions(user_id);
create index if not exists idx_sessions_active_user on sessions(user_id, is_active);
create index if not exists idx_sessions_expiry on sessions(expiry);

-- Add foreign key constraint
alter table sessions
    add constraint fk_sessions_user
    foreign key (user_id)
    references users(user_id)
    on delete cascade;

-- Add comments
comment on table sessions is 'Stores user session information and encrypted tokens';
comment on column sessions.session_id is 'Unique identifier for the session';
comment on column sessions.user_id is 'Reference to the user who owns this session';
comment on column sessions.token is 'Encrypted session token';
comment on column sessions.created_at is 'Timestamp when the session was created';
comment on column sessions.expiry is 'Timestamp when the session expires';
comment on column sessions.is_active is 'Whether the session is currently active';
