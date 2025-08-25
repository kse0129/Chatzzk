# Chatzzk

네이버 치지직(Chzzk) 채팅을 Google Cloud Pub/Sub을 이용하여 PostgreSQL에 저장하고, Jupyter Notebook을 활용해 스트리머별 채팅 데이터를 **분석**하는 프로젝트


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

streamlit/
├─ config/
│ ├─ settings.py        # 환경 설정(경로, Pub/Sub, DB)
│ ├─ sql.py             # DDL/INSERT SQL
│ └─ streamer_list.json # 수집 대상 스트리머 목록
└─ app.py               # streamlit 웹 서버
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