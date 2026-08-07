"""
가장 최소 구성의 PoP(엣지 서버) 시뮬레이터. (컨테이너 1: pop)

역할:
- 좌석 요청(seat_id)을 받으면, "이 요청이 PoP에 도착한 순간"의 타임스탬프를 서버가 직접 찍는다.
- 이 값이 실제 시스템에서 말하는 "엣지 타임스탬프"에 해당한다.
- 기록은 메모리 리스트에 저장한다 (나중에 Kafka로 발행하는 부분을 지금은 생략).
"""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mini PoP Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

records: list[dict] = []
# "좌석 예매하기" 버튼을 눌러 예매 흐름에 진입한 시각을 좌석 클릭 기록과 분리해서 저장
entry_records: list[dict] = []


class SeatRequest(BaseModel):
    seat_id: str
    client_sent_at: str | None = None  # 클라이언트가 주장하는 시각 (참고용, 판정에 안 씀)


@app.post("/seat-request")
def receive_seat_request(req: SeatRequest):
    arrival_time = datetime.now(timezone.utc)
    record = {
        "request_id": str(uuid.uuid4()),
        "seat_id": req.seat_id,
        "client_sent_at": req.client_sent_at,
        "pop_arrival_timestamp": arrival_time.isoformat(),
        "pop_arrival_epoch_ms": int(arrival_time.timestamp() * 1000),
    }
    records.append(record)
    return record


@app.get("/requests")
def get_all_requests():
    return records


@app.get("/requests/{seat_id}")
def get_requests_for_seat(seat_id: str):
    return [r for r in records if r["seat_id"] == seat_id]


@app.delete("/requests")
def clear_requests():
    records.clear()
    return {"status": "cleared"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/booking-entry")
def receive_booking_entry():
    """
    메인 페이지에서 '좌석 예매하기'를 눌렀을 때 호출되는 엔드포인트.
    아직 특정 좌석을 고른 게 아니라 '예매 흐름에 진입했다'는 이벤트이므로,
    좌석 클릭 기록(records)과는 별도로 저장한다.
    """
    arrival_time = datetime.now(timezone.utc)
    record = {
        "entry_id": str(uuid.uuid4()),
        "pop_arrival_timestamp": arrival_time.isoformat(),
        "pop_arrival_epoch_ms": int(arrival_time.timestamp() * 1000),
    }
    entry_records.append(record)
    return record


@app.get("/entries")
def get_all_entries():
    return entry_records


# 정적 파일(정적 UI) 서빙 — 반드시 위의 API 라우트들을 다 정의한 뒤 마지막에 마운트해야
# "/" 하위 정적 파일 처리가 다른 API 라우트를 가리지 않는다.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
