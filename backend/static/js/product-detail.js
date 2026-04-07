document.addEventListener("DOMContentLoaded", function () {
    // [유지] 상품 상세 영역 DOM
    const productDetailBox = document.getElementById("productDetailBox");
    const productId = window.PRODUCT_ID;

    // [유지] 수정 / 삭제 버튼 DOM
    const editBtn = document.getElementById("editBtn");
    const deleteBtn = document.getElementById("deleteProductBtn");

    // [유지] 리뷰 작성 관련 DOM
    const reviewForm = document.getElementById("reviewCreateForm");
    const contentInput = document.getElementById("content");
    const ratingInput = document.getElementById("rating");
    const imageInput = document.getElementById("images");
    const previewBox = document.getElementById("previewBox");
    const reviewList = document.getElementById("reviewList");

    // [유지] axios 또는 공통 api 인스턴스 사용
    const api = window.api || axios;

    // [유지] 로그인 토큰을 헤더에 붙이는 공통 함수
    function getAuthHeaders(extraHeaders = {}) {
        const token =
            localStorage.getItem("access") ||
            localStorage.getItem("access_token") ||
            localStorage.getItem("token");

        const headers = { ...extraHeaders };

        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        return headers;
    }

    // [유지] 상품 상세 조회 후 화면 출력
    async function loadProductDetail() {
        try {
            const response = await api.get(`/products/api/${productId}/`);
            const product = response.data;

            productDetailBox.innerHTML = `
                <img src="${product.image_url || ""}" alt="${product.name}" class="thumb">
                <h1>${product.name}</h1>
                <p>${product.description || ""}</p>
                <p><strong>${Number(product.price).toLocaleString()}원</strong></p>
                <p class="muted">등록일: ${product.created_at || "-"}</p>
            `;
        } catch (error) {
            console.error("상품 상세 조회 실패:", error.response?.data || error);
            productDetailBox.innerHTML = `<p>상품 상세 정보를 불러오지 못했습니다.</p>`;
        }
    }

    // [유지] 리뷰 목록 조회 후 카드 생성
    async function loadReviews() {
        try {
            const response = await api.get(`/reviews/?product=${productId}`);
            const data = response.data;
            const reviews = data.results || data;

            reviewList.innerHTML = "";

            if (!reviews || reviews.length === 0) {
                reviewList.innerHTML = "<p>아직 등록된 리뷰가 없습니다.</p>";
                return;
            }

            // 안내 문구
            const guideBox = document.createElement("div");
            guideBox.className = "review-guide-box";
            guideBox.innerHTML = `
                <p class="review-guide-text">
                    작성한 리뷰와 비슷한 다른 사용자의 후기를 찾아 보여줍니다.<br>
                    리뷰 수가 적으면 결과가 제한적일 수 있습니다.
                </p>
            `;
            reviewList.appendChild(guideBox);

            reviews.forEach((review) => {
                let imagesHtml = "";

                // 리뷰 이미지가 있으면 렌더링
                if (review.images && review.images.length > 0) {
                    imagesHtml = `
                        <div style="margin-top: 12px; display:flex; flex-wrap:wrap; gap:10px;">
                            ${review.images.map((img) => `
                                <img
                                    src="${img.image}"
                                    alt="리뷰 이미지"
                                    style="width:120px; height:120px; object-fit:cover; border-radius:8px;"
                                >
                            `).join("")}
                        </div>
                    `;
                }

                const card = document.createElement("div");
                card.className = "review-card";
                card.style.border = "1px solid #ddd";
                card.style.borderRadius = "8px";
                card.style.padding = "16px";
                card.style.marginBottom = "12px";

                card.innerHTML = `
                    <p><strong>작성자:</strong> ${review.username || review.user || "-"}</p>
                    <p><strong>평점:</strong> ${review.rating ?? "-"}</p>
                    <p style="margin-top: 10px;">${review.content || ""}</p>
                    ${imagesHtml}
                    <p class="muted" style="margin-top: 10px;">
                        작성일: ${review.created_at || "-"}
                    </p>

                    <button
                        class="ai-analyze-btn"
                        data-review-id="${review.id}"
                        style="margin-top:12px; padding:8px 14px; border:none; border-radius:8px; background:#2563eb; color:#fff; font-weight:700; cursor:pointer;"
                    >
                        비슷한 후기 보기
                    </button>

                    <div
                        class="ai-result-box"
                        id="ai-result-${review.id}"
                        style="display:none; margin-top:12px; padding:12px; border:1px solid #ddd; border-radius:8px; background:#f8fafc;"
                    ></div>
                `;

                reviewList.appendChild(card);
            });

            bindAnalyzeButtons();

        } catch (error) {
            console.error("리뷰 목록 조회 실패:", error.response?.data || error);
            reviewList.innerHTML = "<p>리뷰 목록을 불러오지 못했습니다.</p>";
        }
    }

    // [유지] 점수를 짧은 라벨로 변환
    function getSimilarityLabel(score) {
        if (score > 0.7) return "매우 비슷";
        if (score > 0.5) return "비슷";
        if (score > 0.3) return "약간 비슷";
        return "관련 있음";
    }

    // 설명 문구
    function getSimilarityDescription(score) {
        if (score > 0.7) return "표현과 느낌이 매우 비슷한 후기예요.";
        if (score > 0.5) return "비슷한 의견을 담고 있는 후기예요.";
        if (score > 0.3) return "어느 정도 관련 있는 후기예요.";
        return "참고용으로 볼 수 있는 후기예요.";
    }

    // =========================================================
    // [추가] Celery 상태 polling 함수
    // =========================================================
    async function pollTaskStatus(taskId, reviewId, button, resultBox) {
        const intervalId = setInterval(async () => {
            try {
                const response = await api.get(`/ai/tasks/${taskId}/status/`);
                const data = response.data;

                if (data.status === "SUCCESS") {
                    clearInterval(intervalId);

                    const result = data.result || {};

                    if (!result.similar_reviews || result.similar_reviews.length === 0) {
                        resultBox.innerHTML = `
                            <div class="ai-result-inner">
                                <p><strong>이 리뷰와 비슷한 다른 후기</strong></p>
                                <p>충분히 비슷한 후기를 찾지 못했어요.</p>
                                <p class="ai-sub-guide">
                                    아직 비교할 후기가 부족하거나, 현재 등록된 후기와 표현 차이가 클 수 있어요.
                                </p>
                            </div>
                        `;
                    } else {
                        const countText = `비슷한 후기 ${result.similar_reviews.length}개를 찾았어요.`;

                        resultBox.innerHTML = `
                            <div class="ai-result-inner">
                                <p><strong>이 리뷰와 비슷한 다른 후기</strong></p>
                                <p>${countText}</p>
                                <p class="ai-sub-guide">
                                    같은 상품에 대해 비슷하게 느낀 사용자 후기입니다.
                                </p>

                                <ul class="ai-similar-review-list" style="margin-top:10px; padding-left:18px;">
                                    ${result.similar_reviews.map((item) => `
                                        <li class="ai-similar-review-item" style="margin-bottom:14px;">
                                            <p>
                                                <strong>${item.label || getSimilarityLabel(item.score)}</strong>
                                                : ${item.content}
                                            </p>
                                            <p><small>작성자: ${item.username}</small></p>
                                            <p><small>${getSimilarityDescription(item.score)}</small></p>
                                            <p><small>유사도 ${item.score.toFixed(2)} / 작성일 ${item.created_at}</small></p>
                                            <p><small>AI 결과 ID: ${item.analysis_id}</small></p>
                                        </li>
                                    `).join("")}
                                </ul>

                                <p class="ai-sub-guide">
                                    아직 리뷰 수가 적어 결과가 제한적일 수 있어요.
                                </p>
                            </div>
                        `;
                    }

                    button.disabled = false;
                    button.textContent = "비슷한 후기 보기";
                    return;
                }

                // 진행 중 상태 표시
                resultBox.innerHTML = `<p>분석 중... (${data.status})</p>`;

            } catch (error) {
                clearInterval(intervalId);
                resultBox.innerHTML = `<p>작업 조회 실패</p>`;
                button.disabled = false;
                button.textContent = "비슷한 후기 보기";
            }
        }, 1500);
    }

    // =========================================================
    // [수정] AI 분석 버튼 - Celery 비동기 방식으로 변경
    // =========================================================
    function bindAnalyzeButtons() {
        const buttons = document.querySelectorAll(".ai-analyze-btn");

        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                const reviewId = button.dataset.reviewId;
                const resultBox = document.getElementById(`ai-result-${reviewId}`);

                button.disabled = true;
                button.textContent = "작업 등록 중...";

                resultBox.style.display = "block";
                resultBox.innerHTML = "<p>작업 등록 중...</p>";

                try {
                    // [핵심 수정] POST 방식으로 Celery 작업 등록
                    const response = await api.post(
                        `/ai/reviews/${reviewId}/analyze/`,
                        {},
                        { headers: getAuthHeaders() }
                    );

                    const taskId = response.data.task_id;

                    // task_id 기반 polling 시작
                    button.textContent = "분석 진행 중...";
                    pollTaskStatus(taskId, reviewId, button, resultBox);

                } catch (error) {
                    console.error("작업 등록 실패:", error.response?.data || error);
                    resultBox.innerHTML = `<p>작업 등록 실패</p>`;
                    button.disabled = false;
                    button.textContent = "비슷한 후기 보기";
                }
            });
        });
    }

    // [유지] 이미지 미리보기
    if (imageInput && previewBox) {
        imageInput.addEventListener("change", function () {
            previewBox.innerHTML = "";

            Array.from(imageInput.files).forEach((file) => {
                if (!file.type.startsWith("image/")) return;

                const reader = new FileReader();

                reader.onload = function (e) {
                    const img = document.createElement("img");
                    img.src = e.target.result;
                    img.className = "preview-image";
                    img.style.width = "120px";
                    img.style.height = "120px";
                    img.style.objectFit = "cover";
                    img.style.marginRight = "10px";
                    img.style.marginTop = "10px";
                    img.style.borderRadius = "8px";
                    previewBox.appendChild(img);
                };

                reader.readAsDataURL(file);
            });
        });
    }

    // [유지] 리뷰 작성 기능
    if (reviewForm) {
        reviewForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const content = contentInput.value.trim();
            const rating = ratingInput.value.trim();

            if (!content || !rating) {
                alert("리뷰 내용과 평점을 입력해주세요.");
                return;
            }

            try {
                const formData = new FormData();
                formData.append("product", productId);
                formData.append("content", content);
                formData.append("rating", rating);

                if (imageInput && imageInput.files.length > 0) {
                    for (let i = 0; i < imageInput.files.length; i++) {
                        formData.append("uploaded_images", imageInput.files[i]);
                    }
                }

                const response = await api.post("/reviews/", formData, {
                    headers: getAuthHeaders({
                        "Content-Type": "multipart/form-data",
                    }),
                });

                console.log("리뷰 등록 성공:", response.data);

                alert("리뷰가 등록되었습니다.");

                reviewForm.reset();
                previewBox.innerHTML = "";

                await loadReviews();
            } catch (error) {
                console.error("리뷰 등록 실패:", error.response?.data || error);

                if (error.response?.status === 401) {
                    alert("리뷰 작성은 로그인 후 가능합니다.");
                    return;
                }

                alert("리뷰 등록 실패: " + JSON.stringify(error.response?.data || {}));
            }
        });
    }

    // [유지] 상품 수정 이동
    if (editBtn) {
        editBtn.addEventListener("click", function () {
            window.location.href = `/products/${productId}/update/`;
        });
    }

    // [유지] 상품 삭제
    if (deleteBtn) {
        deleteBtn.addEventListener("click", async function () {
            const confirmDelete = confirm("정말 이 상품을 삭제하시겠습니까?");
            if (!confirmDelete) return;

            try {
                await api.delete(`/products/api/${productId}/`, {
                    headers: getAuthHeaders(),
                });

                alert("상품이 삭제되었습니다.");
                window.location.href = "/products/";
            } catch (error) {
                console.error("상품 삭제 실패:", error.response?.data || error);

                if (error.response?.status === 401) {
                    alert("상품 삭제는 로그인 후 가능합니다.");
                    return;
                }

                alert("상품 삭제에 실패했습니다.");
            }
        });
    }

    // [유지] 페이지 시작 시 실행
    loadProductDetail();
    loadReviews();
});