# Chatzzk

네이버 치지직(Chzzk) 채팅을 Google Cloud Pub/Sub을 이용하여 PostgreSQL에 저장하고, Streamlit으로 시각화하는 프로젝트입니다.


## 주요 기능

- 치지직 웹소켓 연결 및 채팅 수집
- 채팅 데이터 DB 저장 (Google Pub/Sub)
- 스트리머 채팅 분석 페이지 (Streamlit)


## 디렉터리 구조
```
collect/
├─ config/
│ ├─ settings.py        	# 환경 설정 (경로, Pub/Sub, DB)
│ ├─ sql.py             	# DDL/INSERT SQL
│ ├─ cookies.json       	# 로그인 쿠키 (Chzzk API용)
│ └─ streamer_list.json 	# 수집 대상 스트리머 목록
├─ pub.py               	# WebSocket → Pub/Sub
├─ sub.py               	# Pub/Sub → Postgres
└─ api.py               	# 치지직 API 오픈소스

notebook/
├─ eda.ipynb            	# 데이터 분석 파일
└─ stopwords.txt        	# 불용어 사전

streamlit/
├─ config/
│ ├─ settings.py       		# 환경 설정 (경로, Pub/Sub, DB)
│ ├─ sql.py            		# DDL SQL (뷰 테이블)
│ └─ streamer_list.json 	# 수집 대상 스트리머 목록
├─ style.css            	# Streamlit 스타일 정의
└─ app.py               	# Streamlit 웹 서버
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