"""URLs."""
from django.urls import include, path

urlpatterns = [
    path(
        "api/",
        include("threads.weave.urls"),
    ),
    path(
        "silk/",
        include("silk.urls", namespace="silk"),
    ),
]
