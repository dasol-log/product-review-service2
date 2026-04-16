import http from 'k6/http';
import { check, sleep } from 'k6';

// 부하 설정
export const options = {
  vus: 5,
  duration: '30s',
};

export default function () {

  // 정상 + 실패 섞기
  const reviewId = Math.random() < 0.7 ? 35 : 999999;

  const res = http.post(`http://127.0.0.1:8000/ai/reviews/${reviewId}/analyze/`);

  // 정상 여부 체크
  check(res, {
    'status is 202 or 404': (r) => r.status === 202 || r.status === 404,
  });

  // 요청 간격
  sleep(1);
}
