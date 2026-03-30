document.addEventListener("DOMContentLoaded", function () {
    const productList = document.getElementById("productList");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const pageInfo = document.getElementById("pageInfo");

    let currentPage = 1;
    let nextPageExists = false;

    async function renderProductCard(product) {
        const card = document.createElement("div");
        card.className = "product-card";
        card.dataset.productId = product.id;

        card.innerHTML = `
            <a href="/products/${product.id}/" class="product-link">
                ${product.image_url ? `<img src="${product.image_url}" alt="${product.name}" class="thumb">` : ""}
                <h3>${product.name}</h3>
                <p class="muted">${product.description || ""}</p>
                <p><strong>${product.price}원</strong></p>
            </a>
        `;

        return card;
    }

    async function loadProducts(page = 1) {
        try {
            const response = await axios.get(`/products/api/?page=${page}`);
            const data = response.data;

            console.log("상품 응답:", data);

            productList.innerHTML = "";

            const products = Array.isArray(data) ? data : (data.results || []);

            if (products.length === 0) {
                productList.innerHTML = "<p>등록된 상품이 없습니다.</p>";
            } else {
                for (const product of products) {
                    const card = await renderProductCard(product);
                    productList.appendChild(card);
                }
            }

            currentPage = page;
            nextPageExists = !!data.next;

            pageInfo.textContent = `${currentPage} 페이지`;
            prevBtn.disabled = currentPage <= 1;
            nextBtn.disabled = !nextPageExists;

        } catch (error) {
            console.error("상품 목록 불러오기 에러:", error.response?.data || error);
            alert("상품 목록을 불러오지 못했습니다.");
        }
    }

    prevBtn.addEventListener("click", function () {
        if (currentPage > 1) {
            loadProducts(currentPage - 1);
        }
    });

    nextBtn.addEventListener("click", function () {
        if (nextPageExists) {
            loadProducts(currentPage + 1);
        }
    });

    loadProducts(1);
});