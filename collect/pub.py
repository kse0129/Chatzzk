import os
import json
import logging
import datetime
import threading

import api
from config.settings import *

from websocket import WebSocket
from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import BatchSettings, PublisherOptions
from requests.exceptions import HTTPError


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger("chzzk-pub")

batch_settings = BatchSettings(
    max_bytes=1_000_000,
    max_messages=1000,
    max_latency=0.05
)
publisher_options = PublisherOptions(enable_message_ordering=False)

PUBLISHER = pubsub_v1.PublisherClient(
    batch_settings=batch_settings,
    publisher_options=publisher_options
)

class ChzzkChat:
    def __init__(self, streamer, cookies, logger, publisher, topic_path):
        self.streamer = streamer
        self.cookies = cookies
        self.logger = logger

        self.publisher = publisher
        self.topic_path = topic_path

        self.sid = None
        self.userIdHash = api.fetch_userIdHash(self.cookies)
        self.chatChannelId = api.fetch_chatChannelId(self.streamer, self.cookies)
        self.channelName = api.fetch_channelName(self.streamer)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId, self.cookies)

        self.sock = None
        self.connect()

    def _publish(self, payload: dict, attributes: dict):
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            future = self.publisher.publish(self.topic_path, data, **attributes)

            def _on_done(f):
                try:
                    mid = f.result()
                    self.logger.debug(f"published mid={mid}")
                except Exception as e:
                    self.logger.error(f"publish failed: {e}")

            future.add_done_callback(_on_done)

        except Exception as e:
            self.logger.exception(f"publish exception: {e}")

    def connect(self):
        self.chatChannelId = api.fetch_chatChannelId(self.streamer, self.cookies)
        self.accessToken, self.extraToken = api.fetch_accessToken(self.chatChannelId, self.cookies)

        sock = WebSocket()
        sock.connect("wss://kr-ss1.chat.naver.com/chat")
        print(f"{self.channelName} 채팅창에 연결 중 .", end="")

        default_dict = {
            "ver": "2",
            "svcid": "game",
            "cid": self.chatChannelId,
        }

        send_dict = {
            "cmd": CHZZK_CHAT_CMD["connect"],
            "tid": 1,
            "bdy": {
                "uid": self.userIdHash,
                "devType": 2001,
                "accTkn": self.accessToken,
                "auth": "SEND",
            },
        }

        sock.send(json.dumps(dict(send_dict, **default_dict)))
        sock_response = json.loads(sock.recv())
        self.sid = sock_response["bdy"]["sid"]
        print(f"\r{self.channelName} 채팅창에 연결 중 ..", end="")

        send_dict = {
            "cmd": CHZZK_CHAT_CMD["request_recent_chat"],
            "tid": 2,
            "sid": self.sid,
            "bdy": {
                "recentMessageCount": 50,
            },
        }

        sock.send(json.dumps(dict(send_dict, **default_dict)))
        sock.recv()
        print(f"\r{self.channelName} 채팅창에 연결 중 ...")

        self.sock = sock
        if self.sock.connected:
            print("연결 완료")
        else:
            raise ValueError("오류 발생")

    def send(self, message: str):
        default_dict = {
            "ver": 2,
            "svcid": "game",
            "cid": self.chatChannelId,
        }

        extras = {
            "chatType": "STREAMING",
            "emojis": "",
            "osType": "PC",
            "extraToken": self.extraToken,
            "streamingChannelId": self.chatChannelId,
        }

        send_dict = {
            "tid": 3,
            "cmd": CHZZK_CHAT_CMD["send_chat"],
            "retry": False,
            "sid": self.sid,
            "bdy": {
                "msg": message,
                "msgTypeCode": 1,
                "extras": json.dumps(extras),
                "msgTime": int(datetime.datetime.now().timestamp()),
            },
        }

        self.sock.send(json.dumps(dict(send_dict, **default_dict)))

    def run(self):
        while True:
            try:
                try:
                    raw_message = self.sock.recv()
                except KeyboardInterrupt:
                    break
                except Exception:
                    self.connect()
                    raw_message = self.sock.recv()

                raw_message = json.loads(raw_message)
                chat_cmd = raw_message["cmd"]

                if chat_cmd == CHZZK_CHAT_CMD["ping"]:
                    self.sock.send(json.dumps({"ver": "2", "cmd": CHZZK_CHAT_CMD["pong"]}))

                    if self.chatChannelId != api.fetch_chatChannelId(self.streamer, self.cookies):
                        self.connect()

                    continue

                if chat_cmd == CHZZK_CHAT_CMD["chat"]:
                    chat_type = "채팅"
                elif chat_cmd == CHZZK_CHAT_CMD["donation"]:
                    chat_type = "후원"
                else:
                    continue

                for chat_data in raw_message["bdy"]:
                    if chat_data.get("uid") == "anonymous":
                        user_id = "익명의 후원자"
                    else:
                        try:
                            profile_data = json.loads(chat_data["profile"])
                            user_id = profile_data["nickname"]
                            if "msg" not in chat_data:
                                continue
                        except Exception:
                            continue

                    msg_ms = chat_data.get("msgTime")
                    try:
                        ts_iso = datetime.datetime.utcfromtimestamp(msg_ms / 1000).isoformat() + "Z"
                    except Exception:
                        ts_iso = None

                    payload = {
                        "streamer_id": self.streamer,
                        "streamer_name": self.channelName,
                        "chat_channel_id": self.chatChannelId,
                        "type": chat_type,
                        "uid": chat_data.get("uid"),
                        "user_id": user_id,
                        "msg": chat_data.get("msg"),
                        "msgTime_ms": msg_ms,
                        "ts_iso": ts_iso,
                    }

                    attributes = {
                        "streamer_id": str(self.streamer),
                        "type": "chat" if chat_type == "채팅" else "donation",
                    }

                    self._publish(payload, attributes)

            except Exception as e:
                self.logger.debug(f"loop error: {e}")
                pass

if __name__ == "__main__":
    with open(COOKIES_PATH, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    with open(STREAMER_LIST_PATH, "r", encoding="utf-8") as streamer_list_json:
        streamer_list = json.load(streamer_list_json)

    chzzkchat_list = []
    threads = []

    for streamer in streamer_list:
        try:
            chzzkchat = ChzzkChat(
                streamer["id"],
                cookies,
                logger,
                PUBLISHER,
                TOPIC_PATH,
            )
        except HTTPError as e:
            logger.warning(f"스트리머 {streamer['id']} 초기화 실패 (HTTPError): {e}")
            continue
        except Exception as e:
            logger.warning(f"스트리머 {streamer['id']} 초기화 실패: {e}")
            continue

        chzzkchat_list.append(chzzkchat)
        t = threading.Thread(target=chzzkchat.run, name=f"chzzk-{streamer['name']}", daemon=True)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()