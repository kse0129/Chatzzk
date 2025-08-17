import os
import json
import signal
import logging
from datetime import datetime, timezone
from concurrent.futures import TimeoutError

from config.settings import *
from config.sql import *

from google.cloud import pubsub_v1
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import Json


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("chatzzk-sub")


def init_db_pool():
    global pool
    dsn = f"host={PG_HOST} port={PG_PORT} dbname={PG_DB} user={PG_USER} password={PG_PASS}"
    pool = SimpleConnectionPool(POOL_MIN, POOL_MAX, dsn=dsn)
    conn = pool.getconn()
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)
    finally:
        pool.putconn(conn)


def _to_datetime_utc(val):
    if val is None:
        return datetime.now(tz=timezone.utc)
    if isinstance(val, datetime):
        return val.astimezone(timezone.utc) if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(tz=timezone.utc)
    return datetime.now(tz=timezone.utc)


def parse_message(message):
    fields = {
        "message_id": getattr(message, "message_id", None),
        "streamer_id": None,
        "user_id": None,
        "msg": None,
        "ts": None,
        "raw": None,
    }

    text = None
    payload = None
    try:
        data_bytes = message.data or b""
        text = data_bytes.decode("utf-8", errors="replace")
        payload = json.loads(text)
    except Exception:
        payload = None

    attrs = message.attributes or {}

    def pick(*candidates, default=None):
        for c in candidates:
            if c is not None and c != "":
                return c
        return default

    fields["streamer_id"] = pick(
        payload.get("streamer_id") if isinstance(payload, dict) else None,
        attrs.get("streamer_id"),
        default="unknown_streamer",
    )

    fields["user_id"] = pick(
        (payload.get("user_id") if isinstance(payload, dict) else None),
        attrs.get("user_id"),
        default=None,
    )

    fields["msg"] = pick(
        (payload.get("msg") if isinstance(payload, dict) else None),
        (payload.get("message") if isinstance(payload, dict) else None),
        text,
        default="",
    )

    ts_candidate = pick(
        (payload.get("ts") if isinstance(payload, dict) else None),
        attrs.get("ts"),
        getattr(message, "publish_time", None),
        default=None,
    )
    fields["ts"] = _to_datetime_utc(ts_candidate)
    fields["raw"] = payload if isinstance(payload, dict) else {"data": text, "attributes": dict(attrs)}

    return fields


def callback(message):
    global pool
    try:
        fields = parse_message(message)

        conn = pool.getconn()
        try:
            conn.autocommit = True
            with conn.cursor() as cur:
                cur.execute(
                    INSERT_SQL,
                    (
                        fields["message_id"],
                        fields["streamer_id"],
                        fields["user_id"],
                        fields["msg"],
                        fields["ts"],
                        Json(fields["raw"]),
                    ),
                )
            message.ack()
            logger.info(
                "DB 저장 | mid=%s, streamer=%s, user=%s, ts=%s",
                fields["message_id"], fields["streamer_id"], fields["user_id"], fields["ts"].isoformat()
            )
        finally:
            pool.putconn(conn)

    except Exception as e:
        logger.exception("DB 저장 실패. error=%s", e)
        try:
            message.nack()
        except Exception:
            pass


def shutdown(signum=None, frame=None):
    global streaming_pull_future, subscriber, pool
    try:
        if streaming_pull_future:
            streaming_pull_future.cancel()
    except Exception:
        pass
    try:
        if subscriber:
            subscriber.close()
    except Exception:
        pass
    try:
        if pool:
            pool.closeall()
    except Exception:
        pass


def main():
    global subscriber, streaming_pull_future
    init_db_pool()

    subscriber = pubsub_v1.SubscriberClient()
    streaming_pull_future = subscriber.subscribe(SUBSCRIPTION_PATH, callback=callback)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    with subscriber:
        try:
            streaming_pull_future.result()
        except TimeoutError:
            logger.warning("stream timed out")
            streaming_pull_future.cancel()
            streaming_pull_future.result()
        except Exception as e:
            logger.exception("streaming_pull_future error: %s", e)
        finally:
            shutdown()

if __name__ == "__main__":
    main()