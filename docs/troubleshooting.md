# 운영 장애 대응 매뉴얼

## CD 실패 시 문제 해결

### 1. git pull 실패

```
Permission denied (publickey)
```

원인: EC2에서 GitHub 인증 안됨

```bash
cd ~/product-review-service2/backend
git remote -v
git pull origin main
```

실패하면:
- `git@github.com:...` → SSH 방식 → EC2에 SSH 키 등록 필요
- `https://github.com/...` → HTTPS 방식 → 토큰 인증 확인

---

### 2. i/o timeout (SSH 접속 실패)

```
dial tcp <IP>:22: i/o timeout
```

원인: EC2 보안 그룹에서 포트 22 막힘

해결:
- AWS 콘솔 → EC2 → 보안 그룹 → 인바운드 규칙
- SSH(22) 소스를 `0.0.0.0/0`으로 변경

---

### 3. docker compose 빌드 실패 - 디스크 부족

```
no space left on device
```

해결:
```bash
# 사용하지 않는 이미지/컨테이너 정리
docker system prune -f
docker image prune -a -f
```

---

### 4. 컨테이너 실행 후 502 Bad Gateway

원인: nginx는 떴지만 upstream(web/fastapi)이 아직 준비 안됨

해결:
```bash
# nginx 재시작
docker compose -f docker-compose.prod.yml restart nginx

# upstream 로그 확인
docker compose -f docker-compose.prod.yml logs --tail=30 web
docker compose -f docker-compose.prod.yml logs --tail=30 fastapi
```

---

### 5. DB 관련 에러

```
type "vector" does not exist
```

원인: pgvector 익스텐션 미설치

해결:
```bash
docker exec -it product_review_postgres psql -U product_user -d product_db
# psql 접속 후
CREATE EXTENSION vector;
\q
```

---

### 6. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'models'
```

원인: `.dockerignore`에서 해당 디렉토리 제외됨

해결: `.dockerignore`에서 해당 경로 제거 후 재빌드

---

## 전체 상태 점검 명령어

```bash
cd ~/product-review-service2/backend

# 컨테이너 상태
docker compose -f docker-compose.prod.yml ps

# 각 서비스 로그
docker compose -f docker-compose.prod.yml logs --tail=30 web
docker compose -f docker-compose.prod.yml logs --tail=30 fastapi
docker compose -f docker-compose.prod.yml logs --tail=30 celery
docker compose -f docker-compose.prod.yml logs --tail=30 nginx
```
