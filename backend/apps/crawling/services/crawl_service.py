from apps.crawling.collectors.danawa_review_collector import DanawaReviewCollector
from apps.crawling.collectors.hwahae_review_collector import HwahaeReviewCollector
from apps.crawling.collectors.glowpick_review_collector import GlowpickReviewCollector
from apps.crawling.services.save_service import save_review_result


def crawl_product_review_target(target, review_limit: int = 20) -> dict:
    """
    product target에 대해 사이트별 리뷰 collector를 실행하고 저장합니다.
    """

    if target.site == "danawa":
        collector = DanawaReviewCollector()
    elif target.site == "hwahae":
        collector = HwahaeReviewCollector()
    elif target.site == "glowpick":
        collector = GlowpickReviewCollector()
    else:
        raise ValueError(f"지원하지 않는 사이트입니다: {target.site}")

    reviews = collector.collect_reviews(target.url, limit=review_limit)
    save_result = save_review_result(target, reviews)

    return {
        "review_count": save_result["review_count"],
        "created_count": save_result["created_count"],
        "updated_count": save_result["updated_count"],
    }