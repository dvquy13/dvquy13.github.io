CREATE TABLE newsletter_subscribers (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email           TEXT UNIQUE NOT NULL,
  subscribed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  unsubscribe_token UUID NOT NULL DEFAULT gen_random_uuid()
);
CREATE INDEX ON newsletter_subscribers (unsubscribe_token);
-- Block all public access; Edge Functions use service role key
ALTER TABLE newsletter_subscribers ENABLE ROW LEVEL SECURITY;
