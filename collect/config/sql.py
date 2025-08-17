CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_logs (
  id           BIGSERIAL PRIMARY KEY,
  message_id   TEXT UNIQUE,
  streamer_id  TEXT NOT NULL,
  user_id      TEXT,
  msg          TEXT NOT NULL,
  ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw          JSONB
);
  ON chat_logs (streamer_id, ts DESC);
"""

INSERT_SQL = """
INSERT INTO chat_logs (message_id, streamer_id, user_id, msg, ts, raw)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (message_id) DO NOTHING;
"""