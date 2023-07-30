"""URLs."""
from django.urls import include, path

urlpatterns = [
    path(
        "silk/",
        include("silk.urls", namespace="silk"),
    ),
]
