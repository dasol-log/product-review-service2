# CD 설정 방법

## 개요

GitHub Actions + appleboy/ssh-action으로 main 브랜치 push 시 EC2 자동 배포

## 사전 준비

### 1. EC2 보안 그룹 설정

EC2 인바운드 규칙에 SSH(22) 허용 필요
- GitHub Actions IP 범위 허용 또는 `0.0.0.0/0` 허용

### 2. GitHub Secrets 등록

Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| EC2_HOST | EC2 퍼블릭 IP |
| EC2_USERNAME | ubuntu |
| EC2_SSH_KEY | pem 파일 전체 내용 (-----BEGIN ~ -----END 포함) |
| EC2_PORT | 22 |

### 3. EC2에 deploy.sh 생성

```bash
# EC2 접속 후
vi /home/ubuntu/product-review-service2/backend/deploy.sh
```

```bash
#!/bin/bash
set -e
cd /home/ubuntu/product-review-service2/backend
echo "=== Git pull ==="
git pull origin main
echo "=== Docker compose up ==="
docker compose -f docker-compose.prod.yml up -d --build
echo "=== Clean images ==="
docker image prune -f
echo "Deploy Complete"
```

```bash
chmod +x deploy.sh
```

## CD 워크플로우 (.github/workflows/cd.yml)

```yaml
name: CD Deploy to EC2

on:
  push:
    branches:
      - main

jobs:
  deploy:
    name: Deploy to EC2
    runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ${{ secrets.EC2_USERNAME }}
          key: ${{ secrets.EC2_SSH_KEY }}
          port: ${{ secrets.EC2_PORT }}
          script: |
            cd /home/ubuntu/product-review-service2/backend
            ./deploy.sh
```

## 배포 확인

GitHub → Actions 탭에서 워크플로우 실행 결과 확인
- 초록 체크: 배포 성공
- 빨간 X: 실패 → 로그 확인 후 troubleshooting.md 참고
