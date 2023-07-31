"""URLs."""
from rest_framework.routers import SimpleRouter

from threads.weave.views import MessageViewSet, PersonViewSet, ThreadViewSet

router = SimpleRouter()
router.register("persons", PersonViewSet)
router.register("threads", ThreadViewSet)
router.register("messages", MessageViewSet)
urlpatterns = router.urls
