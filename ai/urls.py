from django.urls import path

from .views import (
    GenerateCarouselView,
    GenerateImageView,
    GenerateTextView,
    ImprovePromptView,
)

urlpatterns = [
    path("text/", GenerateTextView.as_view()),
    path("image/", GenerateImageView.as_view()),
    path("carousel/", GenerateCarouselView.as_view()),
    path("image-prompt/", ImprovePromptView.as_view()),
]
