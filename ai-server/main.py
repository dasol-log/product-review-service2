from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from api.recommend import router as recommend_router
from redis.asyncio import Redis
from prometheus_fastapi_instrumentator import Instrumentator
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# logger 생성
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(title="AI Recommendation Server")

# Redis 연결 설정 (Docker 서비스명 'redis' 사용)
REDIS_URL = "redis://redis:6379/0"

# 라우터 연결
app.include_router(recommend_router)


# 기본 테스트 API
@app.get("/")
def root():
    return {"message": "AI server is running"}


@app.websocket("/ws/task/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):

    # WebSocket 연결 요청 로그
    logger.info(f"[WS CONNECT] task_id={task_id}")

    """
    클라이언트가 task_id를 가지고 웹소켓에 접속하면,
    해당 task의 완료 알림을 Redis에서 기다렸다가 전송합니다.
    """
    await websocket.accept()

    # 비동기 Redis 객체 생성
    redis = Redis.from_url(REDIS_URL)
    pubsub = redis.pubsub()
    channel_name = f"task_result_{task_id}"

    # 해당 task_id를 채널 이름으로 구독
    # Redis 구독 시작 로그
    logger.info(f"[REDIS SUBSCRIBE] channel={channel_name}")
    await pubsub.subscribe(channel_name)

    try:
        # 메시지를 무한 루프로 기다림
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            raw_data = message["data"]

            # bytes로 오면 문자열로 변환
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8")

            # 메시지 수신 로그
            logger.info(f"[REDIS RECEIVE] task_id={task_id}")

            data = json.loads(raw_data)

            # Celery가 보낸 결과를 그대로 전달
            # 클라이언트 전송 로그
            logger.info(f"[WS SEND] task_id={task_id} status={data.get('status')}")

            await websocket.send_json(data)

            # 결과 전송 후 연결 종료 (1회성 알림)
            break

    except WebSocketDisconnect:
        # 클라이언트 강제 종료 로그
        logger.warning(f"[WS DISCONNECT] task_id={task_id}")

    except Exception as e:
        # 에러 로그 (stack trace 포함)
        logger.exception(f"[WS ERROR] task_id={task_id} error={str(e)}")

    finally:
        # 정리 작업 로그
        logger.info(f"[WS CLEANUP] task_id={task_id}")

        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
        await redis.close()
        
        # 이미 끊긴 경우 예외 방지용 try
        try:
            await websocket.close()
        except Exception:
            pass


# Prometheus 메트릭 설정
Instrumentator(
    excluded_handlers=["/metrics", "/docs", "/openapi.json"]
).instrument(app).expose(app, endpoint="/metrics")