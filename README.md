# Chatzzk

네이버 치지직(Chzzk) 채팅을 수집하여 Google Cloud Pub/Sub로 퍼블리시하고, PostgreSQL에 저장하는 수집 파이프라인


## 주요 기능

- 치지직 웹소켓 연결 및 이벤트 수신
- Pub/Sub 퍼블리시(배치 설정 포함)
- 스트리머별 채팅 분석


## 디렉터리 구조
```
collect/
├─ config/
│ ├─ settings.py        # 환경 설정(경로, Pub/Sub, DB)
│ ├─ sql.py             # DDL/INSERT SQL
│ ├─ cookies.json       # 로그인 쿠키(Chzzk API용)
│ └─ streamer_list.json # 수집 대상 스트리머 목록
├─ pub.py               # WebSocket → Pub/Sub
├─ sub.py               # Pub/Sub → Postgres
└─ api.py               # 치지직 API 오픈소스

notebook/
├─ eda.ipynb            # 데이터 분석 파일
└─ stopwords.txt        # 불용어 사전
```

## 실행
WebSocket → Pub/Sub
```
python3 pub.py
```

Pub/Sub → Postgres
```
python3 sub.py
```

## 요구 사항
- Python 3.9+
- google-cloud-pubsub, websocket-client, requests, psycopg2