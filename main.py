import time
from fastapi import FastAPI
from redis import Redis
from rq import Queue

# FastAPI 앱 생성
app = FastAPI()

# Redis 및 RQ 큐 연결
# (K8s 내부 DNS 'redis-service'를 사용합니다.)
redis_conn = Redis(host='redis-service', port=6379)
q = Queue('jobs', connection=redis_conn)

# --- 워커가 수행할 실제 작업 함수 ---
def background_task(job_id):
    """5초가 걸리는 샘플 작업"""
    print(f"Working on job: {job_id}")
    time.sleep(5)
    print(f"Job finished: {job_id}")
    return f"Job {job_id} completed"

# --- API 엔드포인트 ---
@app.get("/")
def read_root():
    return {"message": "HA Pipeline API is running!"}

@app.get("/health")
def health_check():
    """K8s Liveness/Readiness Probe용 헬스체크"""
    return {"status": "ok"}

@app.post("/enqueue_job/")
def enqueue_job():
    """'jobs' 큐에 5초짜리 작업을 추가하는 API"""
    try:
        # 'background_task' 함수를 큐에 넣음
        job = q.enqueue(background_task, job_id="sample_job_123")
        return {"message": "Job enqueued", "job_id": job.id}
    except Exception as e:
        return {"error": str(e)}