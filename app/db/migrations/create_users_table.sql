-- Create users table
create table if not exists users (
    user_id bigint primary key generated always as identity,
    email text unique not null,
    username text,
    subscription_type text not null,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Create indexes for faster lookups
create index if not exists idx_users_email on users(email);
create index if not exists idx_users_username on users(username);

-- Add check constraint for subscription type
alter table users
    add constraint check_subscription_type
    check (subscription_type in ('basic', 'premium', 'enterprise'));

-- Add comments
comment on table users is 'Stores user account information';
comment on column users.user_id is 'Unique identifier for the user';
comment on column users.email is 'User email address (unique)';
comment on column users.username is 'Optional username';
comment on column users.subscription_type is 'Type of subscription (basic, premium, enterprise)';
comment on column users.created_at is 'Timestamp when the user account was created';
