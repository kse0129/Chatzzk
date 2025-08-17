import os

# GCP 인증
GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
    "GOOGLE_APPLICATION_CREDENTIALS",
    "/home/Chatzzk/collect/config/chatzzk-private-key.json"
)

# Pub/Sub
PROJECT_ID = os.getenv("GCP_PROJECT", "chatzzk")

# Publisher
TOPIC_ID = os.getenv("PUBSUB_TOPIC", "chat")
TOPIC_PATH = f"projects/{PROJECT_ID}/topics/{TOPIC_ID}"

# Subscriber
SUBSCRIPTION_ID = os.getenv("PUBSUB_SUBSCRIPTION", "chat-sub")
SUBSCRIPTION_PATH = f"projects/{PROJECT_ID}/subscriptions/{SUBSCRIPTION_ID}"

# PostgreSQL
PG_HOST = os.getenv("PGHOST", "distracted_wing")
PG_PORT = int(os.getenv("PGPORT", "5432"))
PG_DB   = os.getenv("PGDATABASE", "postgres")
PG_USER = os.getenv("PGUSER", "postgres")
PG_PASS = os.getenv("PGPASSWORD", "password")

POOL_MIN = int(os.getenv("PG_POOL_MIN", "1"))
POOL_MAX = int(os.getenv("PG_POOL_MAX", "5"))

# 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COOKIES_PATH = os.path.join(BASE_DIR, "cookies.json")
STREAMER_LIST_PATH = os.path.join(BASE_DIR, "streamer_list.json")

# 로깅
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# API 코드
CHZZK_CHAT_CMD = {
    'ping'                : 0,
    'pong'                : 10000,
    'connect'             : 100,
    'send_chat'           : 3101,
    'request_recent_chat' : 5101,
    'chat'                : 93101,
    'donation'            : 93102,
}