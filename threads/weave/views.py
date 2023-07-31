"""Views."""
from rest_framework.viewsets import ReadOnlyModelViewSet

from threads.weave import filters, models, serializers


class PersonViewSet(ReadOnlyModelViewSet):
    """Persons viewset."""

    queryset = models.Person.objects.filter(deleted=False)
    serializer_class = serializers.PersonSerializer
    filterset_class = filters.PersonFilter


class ThreadViewSet(ReadOnlyModelViewSet):
    """Threads viewset."""

    queryset = models.Thread.objects.filter(deleted=False)
    serializer_class = serializers.ThreadSerializer
    filterset_class = filters.ThreadFilter


class MessageViewSet(ReadOnlyModelViewSet):
    """Message viewset."""

    queryset = models.Message.objects.filter(deleted=False)
    serializer_class = serializers.MessageSerializer
    filterset_class = filters.MessageFilter
