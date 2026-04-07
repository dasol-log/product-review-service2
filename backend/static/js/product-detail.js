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

    // [유지 + 일부 수정] 리뷰 목록 조회 후 카드 생성
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

            // [추가]
            // 처음 코드에는 없었음
            // 리뷰 목록 상단에 이 기능이 무엇인지 안내 문구를 보여줌
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

                // [유지] 리뷰 이미지가 있으면 렌더링
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

                    <!-- [수정]
                         처음 코드: 버튼 문구가 "AI 분석"
                         변경 후: 버튼 문구를 "비슷한 후기 보기" 로 변경 -->
                    <button
                        class="ai-analyze-btn"
                        data-review-id="${review.id}"
                        style="margin-top:12px; padding:8px 14px; border:none; border-radius:8px; background:#2563eb; color:#fff; font-weight:700; cursor:pointer;"
                    >
                        비슷한 후기 보기
                    </button>

                    <!-- [유지] 결과 출력 영역 -->
                    <div
                        class="ai-result-box"
                        id="ai-result-${review.id}"
                        style="display:none; margin-top:12px; padding:12px; border:1px solid #ddd; border-radius:8px; background:#f8fafc;"
                    ></div>
                `;

                reviewList.appendChild(card);
            });

            // [유지] 버튼 이벤트 연결
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

    // [유지였던 추가 함수]
    // 처음 코드에서는 없었고, 중간 변경 단계에서 추가된 설명용 함수
    function getSimilarityDescription(score) {
        if (score > 0.7) return "표현과 느낌이 매우 비슷한 후기예요.";
        if (score > 0.5) return "비슷한 의견을 담고 있는 후기예요.";
        if (score > 0.3) return "어느 정도 관련 있는 후기예요.";
        return "참고용으로 볼 수 있는 후기예요.";
    }

    // [유지 + 결과 출력 부분 수정]
    function bindAnalyzeButtons() {
        const buttons = document.querySelectorAll(".ai-analyze-btn");

        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                const reviewId = button.dataset.reviewId;
                const resultBox = document.getElementById(`ai-result-${reviewId}`);

                button.disabled = true;

                // [수정]
                // 처음 코드: "분석 중..."
                // 변경 후: "후기 찾는 중..."
                button.textContent = "후기 찾는 중...";

                resultBox.style.display = "block";

                // [수정]
                // 처음 코드: "AI 분석 중입니다..."
                // 변경 후: "비슷한 후기를 찾는 중입니다..."
                resultBox.innerHTML = "<p>비슷한 후기를 찾는 중입니다...</p>";

                try {
                    // [유지] Django AI 분석 API 호출
                    const response = await api.get(`/ai/reviews/${reviewId}/analyze/`);
                    const data = response.data;

                    // [수정]
                    // 처음 코드:
                    // - "AI 분석 결과"
                    // - "비슷한 리뷰를 찾지 못했습니다."
                    //
                    // 변경 후:
                    // - 제목 문구 변경
                    // - 부족한 이유 설명 추가
                    if (!data.similar_reviews || data.similar_reviews.length === 0) {
                        resultBox.innerHTML = `
                            <div class="ai-result-inner">
                                <p><strong>이 리뷰와 비슷한 다른 후기</strong></p>
                                <p>충분히 비슷한 후기를 찾지 못했어요.</p>
                                <p class="ai-sub-guide">
                                    아직 비교할 후기가 부족하거나, 현재 등록된 후기와 표현 차이가 클 수 있어요.
                                </p>
                            </div>
                        `;
                        return;
                    }

                    // [추가]
                    // 처음 코드에는 없었음
                    // 몇 개를 찾았는지 사용자에게 자연스럽게 안내
                    const countText = `비슷한 후기 ${data.similar_reviews.length}개를 찾았어요.`;

                    // [수정]
                    // 처음 코드:
                    // - AI 분석 결과
                    // - TOP n
                    // - username / label / 숫자 중심
                    //
                    // 변경 후:
                    // - 사용자 중심 제목
                    // - 설명 문구 추가
                    // - 숫자보다 의미 문구를 먼저 노출
                    // - analysis_id 표시 추가
                    resultBox.innerHTML = `
                        <div class="ai-result-inner">
                            <p><strong>이 리뷰와 비슷한 다른 후기</strong></p>
                            <p>${countText}</p>
                            <p class="ai-sub-guide">
                                같은 상품에 대해 비슷하게 느낀 사용자 후기입니다.
                            </p>

                            <ul class="ai-similar-review-list" style="margin-top:10px; padding-left:18px;">
                                ${data.similar_reviews.map((item) => `
                                    <li class="ai-similar-review-item" style="margin-bottom:14px;">
                                        <p>
                                            <!-- [수정]
                                                 처음 코드: getSimilarityLabel(item.score)만 사용
                                                 변경 후: 백엔드에서 내려준 label이 있으면 우선 사용 -->
                                            <strong>${item.label || getSimilarityLabel(item.score)}</strong>
                                            : ${item.content}
                                        </p>

                                        <!-- [유지] 작성자 표시 -->
                                        <p><small>작성자: ${item.username}</small></p>

                                        <!-- [유지] 설명 문구 표시 -->
                                        <p><small>${getSimilarityDescription(item.score)}</small></p>

                                        <!-- [유지] 점수/작성일 표시 -->
                                        <p><small>유사도 ${item.score.toFixed(2)} / 작성일 ${item.created_at}</small></p>

                                        <!-- [추가]
                                             처음 코드에는 없었음
                                             DB에 저장된 AI 결과 id를 보여줌 -->
                                        <p><small>AI 결과 ID: ${item.analysis_id}</small></p>
                                    </li>
                                `).join("")}
                            </ul>

                            <!-- [유지] 안내 문구 -->
                            <p class="ai-sub-guide">
                                아직 리뷰 수가 적어 결과가 제한적일 수 있어요.
                            </p>
                        </div>
                    `;
                } catch (error) {
                    // [수정]
                    // 처음 코드: "AI 분석 실패"
                    // 변경 후: "비슷한 후기 조회 실패"
                    console.error("비슷한 후기 조회 실패:", error.response?.data || error);

                    const detail =
                        error.response?.data?.detail || "후기를 불러오는 중 오류가 발생했습니다.";

                    resultBox.innerHTML = `
                        <div class="ai-result-inner error">
                            <p>${detail}</p>
                        </div>
                    `;
                } finally {
                    button.disabled = false;

                    // [수정]
                    // 처음 코드: "AI 분석"
                    // 변경 후: "비슷한 후기 보기"
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