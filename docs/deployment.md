# 배포 전체 흐름

## 아키텍처 구성

```
GitHub push
    ↓
GitHub Actions (CI: 테스트 → 빌드)
    ↓
GitHub Actions (CD: SSH → EC2)
    ↓
EC2 deploy.sh 실행
    ↓
docker compose -f docker-compose.prod.yml up -d --build
    ↓
nginx (80) → drf-web (8000) / fastapi-server (8001)
```

## 컨테이너 구성

| 컨테이너 | 역할 |
|---|---|
| nginx | 리버스 프록시, 정적 파일 서빙 |
| drf-web | Django + Gunicorn (API 서버) |
| fastapi-server | AI 추론 서버 |
| celery-worker | 비동기 작업 처리 |
| redis-server | Celery 브로커/결과 저장 |
| product_review_postgres | PostgreSQL + pgvector |

## 배포 절차

### 최초 배포 (EC2 직접 접속)

```bash
# EC2 접속
ssh -i product-review-key.pem ubuntu@<EC2_IP>

# 레포 클론
git clone https://github.com/dasol-log/product-review-service2.git
cd product-review-service2/backend

# .env 파일 생성
vi .env

# deploy.sh 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh
```

### 이후 배포 (자동 CD)

main 브랜치에 push하면 GitHub Actions가 자동으로 deploy.sh 실행

## EC2 운영 명령어

```bash
# 컨테이너 상태 확인
docker compose -f docker-compose.prod.yml ps

# 로그 확인
docker compose -f docker-compose.prod.yml logs --tail=30 web
docker compose -f docker-compose.prod.yml logs --tail=30 fastapi
docker compose -f docker-compose.prod.yml logs --tail=30 celery
docker compose -f docker-compose.prod.yml logs --tail=30 nginx

# 재시작
docker compose -f docker-compose.prod.yml restart

# 전체 중지
docker compose -f docker-compose.prod.yml down
```
