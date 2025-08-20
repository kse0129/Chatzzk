CREATE_VIEW_TABLE_CHAT_COUNTS_PER_STREAMER = """
CREATE MATERIALIZED VIEW chat_counts_per_streamer AS
SELECT streamer_id, DATE(ts) AS chat_date, COUNT(*) AS msg_count
FROM chat_logs
GROUP BY streamer_id, DATE(ts);
"""

CREATE_VIEW_TABLE_UNIQUE_USER_PER_STREAMER = """
CREATE MATERIALIZED VIEW unique_users_per_streamer AS
SELECT streamer_id, DATE(ts) AS chat_date, COUNT(DISTINCT user_id) AS unique_users
FROM chat_logs
GROUP BY streamer_id, DATE(ts);
"""