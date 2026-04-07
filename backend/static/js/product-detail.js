document.addEventListener("DOMContentLoaded", function () {
    // [시작] 페이지가 열리면 필요한 DOM 요소들을 먼저 가져옵니다.
    const productDetailBox = document.getElementById("productDetailBox");
    const productId = window.PRODUCT_ID; // [핵심] 현재 상품 ID

    const editBtn = document.getElementById("editBtn");
    const deleteBtn = document.getElementById("deleteProductBtn");

    const reviewForm = document.getElementById("reviewCreateForm");
    const contentInput = document.getElementById("content");
    const ratingInput = document.getElementById("rating");
    const imageInput = document.getElementById("images");
    const previewBox = document.getElementById("previewBox");
    const reviewList = document.getElementById("reviewList");

    // [핵심] axios 또는 공통 api 인스턴스 사용
    const api = window.api || axios;

    // [공통] 로그인 토큰이 있으면 헤더에 붙여서 요청
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

    // [흐름 1] 상품 상세 정보 불러와서 화면에 출력
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

    // [흐름 2] 리뷰 목록 불러오기 → 카드 생성 → AI 버튼 붙이기
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

            reviews.forEach((review) => {
                let imagesHtml = "";

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

                // [핵심] 각 리뷰 카드에 AI 분석 버튼과 결과 출력 영역을 함께 만듭니다.
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
                        data-review-id="${review.id}"  <!-- [핵심] review_id를 버튼에 저장 -->
                        style="margin-top:12px; padding:8px 14px; border:none; border-radius:8px; background:#2563eb; color:#fff; font-weight:700; cursor:pointer;"
                    >
                        AI 분석
                    </button>

                    <div
                        class="ai-result-box"
                        id="ai-result-${review.id}"   <!-- [핵심] 이 리뷰의 AI 결과가 출력될 자리 -->
                        style="display:none; margin-top:12px; padding:12px; border:1px solid #ddd; border-radius:8px; background:#f8fafc;"
                    ></div>
                `;

                reviewList.appendChild(card);
            });

            // [핵심] 리뷰 카드 생성이 끝난 뒤 버튼 이벤트 연결
            bindAnalyzeButtons();

        } catch (error) {
            console.error("리뷰 목록 조회 실패:", error.response?.data || error);
            reviewList.innerHTML = "<p>리뷰 목록을 불러오지 못했습니다.</p>";
        }
    }

    // [보조] 유사도 점수를 사람이 읽기 쉬운 문구로 바꿔줌
    function getSimilarityLabel(score) {
        if (score > 0.7) return "매우 비슷";
        if (score > 0.5) return "비슷";
        if (score > 0.3) return "약간 비슷";
        return "관련 있음";
    }

    // [흐름 3] AI 분석 버튼 클릭 → Django API 호출 → 결과 출력
    function bindAnalyzeButtons() {
        const buttons = document.querySelectorAll(".ai-analyze-btn");

        buttons.forEach((button) => {
            button.addEventListener("click", async () => {
                // [핵심] 버튼에 저장된 review_id 꺼내기
                const reviewId = button.dataset.reviewId;
                const resultBox = document.getElementById(`ai-result-${reviewId}`);

                button.disabled = true;
                button.textContent = "분석 중...";

                resultBox.style.display = "block";
                resultBox.innerHTML = "<p>AI 분석 중입니다...</p>";

                try {
                    // [핵심 흐름]
                    // JS → Django /ai/reviews/<review_id>/analyze/ 호출
                    const response = await api.get(`/ai/reviews/${reviewId}/analyze/`);
                    const data = response.data;

                    // [분기] 비슷한 리뷰가 없을 때
                    if (!data.similar_reviews || data.similar_reviews.length === 0) {
                        resultBox.innerHTML = `
                            <div class="ai-result-inner">
                                <p><strong>AI 분석 결과</strong></p>
                                <p>비슷한 리뷰를 찾지 못했습니다.</p>
                            </div>
                        `;
                        return;
                    }

                    // [핵심] Django가 반환한 similar_reviews를 화면에 출력
                    resultBox.innerHTML = `
                        <div class="ai-result-inner">
                            <p><strong>AI 분석 결과</strong></p>
                            <p>이 리뷰와 유사한 리뷰 TOP ${data.similar_reviews.length}</p>
                            <ul style="margin-top:10px; padding-left:18px;">
                                ${data.similar_reviews.map((item) => `
                                    <li style="margin-bottom:12px;">
                                        <p>  
											<strong>${item.username}</strong>  
											/ ${getSimilarityLabel(item.score)}  
											(유사도: ${item.score.toFixed(2)})  
										</p>
                                        <p>${item.content}</p>
                                        <p><small>${item.created_at}</small></p>
                                    </li>
                                `).join("")}
                            </ul>
                        </div>
                    `;
                } catch (error) {
                    console.error("AI 분석 실패:", error.response?.data || error);

                    const detail =
                        error.response?.data?.detail || "AI 분석 중 오류가 발생했습니다.";

                    resultBox.innerHTML = `
                        <div class="ai-result-inner error">
                            <p>${detail}</p>
                        </div>
                    `;
                } finally {
                    button.disabled = false;
                    button.textContent = "AI 분석";
                }
            });
        });
    }

    // [보조] 리뷰 이미지 미리보기
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

    // [흐름 4] 리뷰 작성 폼 제출 → Django에 저장 요청
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
                // [핵심] 리뷰 작성은 FormData로 전송
                const formData = new FormData();
                formData.append("product", productId);
                formData.append("content", content);
                formData.append("rating", rating);

                if (imageInput && imageInput.files.length > 0) {
                    for (let i = 0; i < imageInput.files.length; i++) {
                        formData.append("uploaded_images", imageInput.files[i]);
                    }
                }

                for (const pair of formData.entries()) {
                    console.log(pair[0], pair[1]);
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

                // [핵심] 리뷰 등록 후 목록을 다시 불러와 새 리뷰 반영
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

    // [보조] 상품 수정 페이지 이동
    if (editBtn) {
        editBtn.addEventListener("click", function () {
            console.log("수정 버튼 클릭");
            window.location.href = `/products/${productId}/update/`;
        });
    }

    // [보조] 상품 삭제 요청
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

    // [시작 시 실행]
    // 1. 상품 정보 불러오기
    // 2. 리뷰 목록 불러오기
    loadProductDetail();
    loadReviews();
});