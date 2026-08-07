"""
좌석 요청을 보내는 클라이언트 컨테이너 (컨테이너 2: client)

docker-compose 안에서는 서비스 이름(pop)으로 서로를 찾을 수 있기 때문에,
POP_URL 기본값을 http://pop:8000 으로 잡아둔다.
"""

import os
import time

import requests

POP_URL = os.environ.get("POP_URL", "http://pop:8000")
SEAT_ID = os.environ.get("SEAT_ID", "A1")
REQUEST_COUNT = int(os.environ.get("REQUEST_COUNT", "3"))


def wait_for_pop(max_tries: int = 20):
    """pop 컨테이너가 완전히 뜨기 전에 client가 먼저 시작될 수 있으니, 준비될 때까지 재시도."""
    for i in range(max_tries):
        try:
            res = requests.get(f"{POP_URL}/health", timeout=2)
            if res.status_code == 200:
                print(f"[client] PoP 서버 연결 확인 완료 ({POP_URL})")
                return
        except requests.exceptions.ConnectionError:
            pass
        print(f"[client] PoP 서버 대기 중... ({i+1}/{max_tries})")
        time.sleep(1)
    raise RuntimeError("PoP 서버에 연결할 수 없습니다.")


def send_seat_request(seat_id: str):
    payload = {"seat_id": seat_id}
    res = requests.post(f"{POP_URL}/seat-request", json=payload, timeout=5)
    res.raise_for_status()
    return res.json()


def main():
    wait_for_pop()

    print(f"[client] 좌석 '{SEAT_ID}'에 대해 요청 {REQUEST_COUNT}건을 보냅니다.\n")
    for i in range(REQUEST_COUNT):
        result = send_seat_request(SEAT_ID)
        print(
            f"[client] 요청 {i+1}/{REQUEST_COUNT} 전송 완료 -> "
            f"PoP 도착 시각: {result['pop_arrival_timestamp']} "
            f"(epoch_ms={result['pop_arrival_epoch_ms']})"
        )
        time.sleep(0.2)  # 약간의 간격을 두고 여러 요청을 보내는 시뮬레이션

    print("\n[client] 이 좌석에 대해 PoP에 쌓인 전체 기록:")
    all_records = requests.get(f"{POP_URL}/requests/{SEAT_ID}", timeout=5).json()
    for r in all_records:
        print(f"  - {r['request_id'][:8]} | {r['pop_arrival_timestamp']}")


if __name__ == "__main__":
    main()
