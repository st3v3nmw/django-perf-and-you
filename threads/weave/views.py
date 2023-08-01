"""Views."""
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.viewsets import ReadOnlyModelViewSet

from threads.weave import filters, models, paginators, serializers


class PersonViewSet(ReadOnlyModelViewSet):
    """Persons viewset."""

    queryset = models.Person.objects.filter(deleted=False)
    serializer_class = serializers.PersonSerializer
    filterset_class = filters.PersonFilter


class ThreadViewSet(ReadOnlyModelViewSet):
    """Threads viewset."""

    queryset = models.Thread.objects.filter(deleted=False).prefetch_related(
        "messages",
        "messages__sent_by",
    )
    serializer_class = serializers.ThreadSerializer
    filterset_class = filters.ThreadFilter


class MessageViewSet(ReadOnlyModelViewSet):
    """Message viewset."""

    queryset = models.Message.objects.filter(deleted=False)
    serializer_class = serializers.MessageSerializer
    filterset_class = filters.MessageFilter
    pagination_class = paginators.CustomPageNumberPagination

    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = models.Message.objects.select_related("sent_by").all()[:100]
        data = serializers.MessageSerializer(
            messages,
            many=True,
        ).data
        return Response(data=data, status=HTTP_200_OK)
