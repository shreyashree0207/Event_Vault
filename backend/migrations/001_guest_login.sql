-- Apply once to an existing PostgreSQL database before enabling guest login.
-- Stop without modifying data if legacy emails collide after normalization.
DO $$
BEGIN
    IF EXISTS (
        SELECT lower(trim(email))
        FROM users
        GROUP BY lower(trim(email))
        HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION
            'Duplicate users.email values exist after normalization; resolve them before applying this migration.';
    END IF;
END
$$;

UPDATE users SET email = lower(trim(email));
ALTER TABLE users ALTER COLUMN password DROP NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email_lower ON users (lower(email));
