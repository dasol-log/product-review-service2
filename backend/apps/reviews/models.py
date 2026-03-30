from apps.products.models import Product
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Review(models.Model):
    """
    제품 리뷰
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    content = models.TextField()
    rating = models.IntegerField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product} - {self.user}"


class ReviewImage(models.Model):

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="reviews/")
    created_at = models.DateTimeField(auto_now_add=True)


class ReviewAI(models.Model):

    review = models.OneToOneField(
        Review, on_delete=models.CASCADE, related_name="ai_result"
    )
    sentiment = models.CharField(max_length=50)
    confidence = models.FloatField()
    keywords = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
