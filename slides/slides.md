---
theme: seriph
class: text-center
highlighter: shiki
lineNumbers: true
drawings:
  persist: false
export:
  format: pdf
  timeout: 30000
  dark: false
  withClicks: false
  withToc: false
colorSchema: 'light'
transition: slide-left
title: Django Performance & You
---

# Django Performance & You

---
transition: fade-out
---

# Raw SQL? We're Civilized Here!

asdfsdf

---
transition: fade-out
---

# Raw SQL? We're Civilized Here!

```python {1-3|5-8|9-18}
> from threads.weave.models import *

> deleted_messages = Message.objects.filter(deleted=True)

> str(deleted_messages.query)  # SQL String
SELECT * FROM "weave_message"
WHERE "weave_message"."deleted"
ORDER BY "weave_message"."updated" DESC

> deleted_messages.explain(analyze=True)  # Query Plan
Sort  (cost=3342.87..3367.85 rows=9993 width=104) (actual time=21.625..22.368 rows=10036 loops=1)
  Sort Key: updated DESC
  Sort Method: quicksort  Memory: 1835kB
  ->  Seq Scan on weave_message  (cost=0.00..2679.00 rows=9993 width=104) (actual time=0.020..17.314 rows=10036 loops=1)
        Filter: deleted
        Rows Removed by Filter: 89964
Planning Time: 0.099 ms
Execution Time: 23.005 ms
```

---
transition: fade-out
---

# The Demo Project: ERD

---
transition: fade-out
---

# The Demo Project: Models

---
transition: fade-out
---

# Example 1: The N+1 Query Problem

http://127.0.0.1:8000/api/messages/list_some/

<div>
  <i style="margin-right: 20px;" class="text-red-400"><mingcute-time-fill/>2,794ms overall</i>
  <i style="margin-right: 20px;" class="text-red-400"><material-symbols-database/>484ms on queries</i>
  <i style="margin-right: 20px;" class="text-red-400"><fluent-text-word-count-24-filled/>103 queries</i>
</div>

```python {3-}
class MessageViewSet(ReadOnlyModelViewSet):
    """Message viewset."""

    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = models.Message.objects.all()[:100]
        data = serializers.MessageSerializer(messages, many=True,).data
        return Response(data=data, status=HTTP_200_OK)
```

### Queries

<i>From http://127.0.0.1:8000/silk/requests/</i>

```sql
# Executed 1X -> Pick 100 messages
SELECT * FROM "weave_message" ORDER BY "weave_message"."updated" DESC LIMIT 100

# Executed 100X -> Once for each message
SELECT * FROM "weave_person" ORDER BY "weave_person"."updated" DESC
```

---
transition: fade-out
---

# Example 1: Query Plan 1

##### SELECT * FROM "weave_person" ORDER BY "weave_person"."updated" DESC

<i>From http://127.0.0.1:8000/silk/request/GUID/sql/ID/</i>

```sql {1,3-5,7-}
Sort  (cost=73.83..76.33 rows=1000 width=76) (actual time=0.600..0.700 rows=1000 loops=1)
  Output: id, created, updated, deleted, first_name, last_name, email_address
  Sort Key: weave_person.updated DESC
  Sort Method: quicksort  Memory: 141kB
  ->  Seq Scan on public.weave_person  (cost=0.00..24.00 rows=1000 width=76) (actual time=0.013..0.207 rows=1000 loops=1)
        Output: id, created, updated, deleted, first_name, last_name, email_address
Planning Time: 0.081 ms
Execution Time: 0.815 ms
```

---
transition: fade-out
---

# Example 1: Query Plan 2

<i>From http://127.0.0.1:8000/silk/request/GUID/sql/ID/</i>

##### SELECT * FROM "weave_message" ORDER BY "weave_message"."updated" DESC LIMIT 100

```sql {3,7,10,13,16,17}
Limit  (cost=5515.46..5526.96 rows=100 width=104) (actual time=27.490..30.617 rows=100 loops=1)
  Output: id, created, updated, deleted, text, sent_by_id, thread_id
  ->  Gather Merge  (cost=5515.46..12280.22 rows=58824 width=104) (actual time=27.489..30.607 rows=100 loops=1)
        Output: id, created, updated, deleted, text, sent_by_id, thread_id
        Workers Planned: 1
        Workers Launched: 1
        ->  Sort  (cost=4515.45..4662.51 rows=58824 width=104) (actual time=24.413..24.418 rows=70 loops=2)
              Output: id, created, updated, deleted, text, sent_by_id, thread_id
              Sort Key: weave_message.updated DESC
              Sort Method: top-N heapsort  Memory: 61kB
              Worker 0:  actual time=21.745..21.752 rows=100 loops=1
                Sort Method: top-N heapsort  Memory: 62kB
              ->  Parallel Seq Scan on public.weave_message  (cost=0.00..2267.24 rows=58824 width=104) (actual time=0.007..6.247 rows=50000 loops=2)
                    Output: id, created, updated, deleted, text, sent_by_id, thread_id
                    Worker 0:  actual time=0.008..6.095 rows=43056 loops=1
Planning Time: 0.093 ms
Execution Time: 30.644 ms
```

---
transition: fade-out
---

# Example 1: Optimized

http://127.0.0.1:8000/api/messages/list_some/

<div>
  <i style="margin-right: 20px;" class="text-red-400"><mingcute-time-fill/>1,487ms overall</i>
  <i style="margin-right: 20px;" class="text-amber-400"><material-symbols-database/>82ms on queries</i>
  <i style="margin-right: 20px;" class="text-green-400"><fluent-text-word-count-24-filled/>1 queries</i>
</div>

```python {monaco-diff}
    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = models.Message.objects.all()[:100]
        data = serializers.MessageSerializer(messages, many=True,).data
        return Response(data=data, status=HTTP_200_OK)
~~~
    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = (
          models.Message.objects
          .select_related("sent_by").all()[:100]
        )
        data = serializers.MessageSerializer(messages, many=True,).data
        return Response(data=data, status=HTTP_200_OK)
```

### Queries

<i>From http://127.0.0.1:8000/silk/request/GUID/sql/ID/</i>

```sql
# Executed 1X -> Picks everything
SELECT * FROM "weave_message"
INNER JOIN "weave_person" ON ("weave_message"."sent_by_id" = "weave_person"."id")
ORDER BY "weave_message"."updated" DESC
LIMIT 100
```

---
transition: fade-out
---

# Example 1: Query Plan

```sql {3,5,9-16,18,20-21}
Limit  (cost=5707.03..5718.53 rows=100 width=180) (actual time=77.875..81.329 rows=100 loops=1)
  Output: weave_message.id, weave_message.created, weave_message.updated, weave_message.deleted, weave_message.text, weave_message.sent_by_id, weave_message.thread_id, weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
  ->  Gather Merge  (cost=5707.03..12471.79 rows=58824 width=180) (actual time=77.874..81.319 rows=100 loops=1)
        Output: weave_message.id, weave_message.created, weave_message.updated, weave_message.deleted, weave_message.text, weave_message.sent_by_id, weave_message.thread_id, weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
        ->  Sort  (cost=4707.02..4854.08 rows=58824 width=180) (actual time=73.949..73.957 rows=85 loops=2)
              Output: weave_message.id, weave_message.created, weave_message.updated, weave_message.deleted, weave_message.text, weave_message.sent_by_id, weave_message.thread_id, weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
              Sort Key: weave_message.updated DESC
              Sort Method: top-N heapsort  Memory: 78kB
              ->  Hash Join  (cost=36.50..2458.80 rows=58824 width=180) (actual time=0.687..36.358 rows=50000 loops=2)
                    Output: weave_message.id, weave_message.created, weave_message.updated, weave_message.deleted, weave_message.text, weave_message.sent_by_id, weave_message.thread_id, weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
                    Inner Unique: true
                    Hash Cond: (weave_message.sent_by_id = weave_person.id)
                    ->  Parallel Seq Scan on public.weave_message  (cost=0.00..2267.24 rows=58824 width=104) (actual time=0.008..7.257 rows=50000 loops=2)
                          Output: weave_message.id, weave_message.created, weave_message.updated, weave_message.deleted, weave_message.text, weave_message.sent_by_id, weave_message.thread_id
                    ->  Hash  (cost=24.00..24.00 rows=1000 width=76) (actual time=0.591..0.591 rows=1000 loops=2)
                          Output: weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
                          Buckets: 1024  Batches: 1  Memory Usage: 114kB
                          ->  Seq Scan on public.weave_person  (cost=0.00..24.00 rows=1000 width=76) (actual time=0.024..0.234 rows=1000 loops=2)
                                Output: weave_person.id, weave_person.created, weave_person.updated, weave_person.deleted, weave_person.first_name, weave_person.last_name, weave_person.email_address
Planning Time: 0.459 ms
Execution Time: 81.380 ms
```

---
transition: fade-out
---

# Example 2: Unoptimized

http://127.0.0.1:8000/api/threads/

<div>
  <i style="margin-right: 20px;" class="text-red-400"><mingcute-time-fill/>113,450ms overall</i>
  <i style="margin-right: 20px;" class="text-red-400"><material-symbols-database/>27,349ms on queries</i>
  <i style="margin-right: 20px;" class="text-red-400"><fluent-text-word-count-24-filled/>10,244 queries</i>
</div>

```python
class ThreadViewSet(ReadOnlyModelViewSet):

    queryset = models.Thread.objects.filter(deleted=False)
    serializer_class = serializers.ThreadSerializer

class MessageSerializer(serializers.ModelSerializer):

    sender = serializers.ReadOnlyField(source="sent_by.full_name")

    class Meta:
        model = Message
        fields = "__all__"

class ThreadSerializer(serializers.ModelSerializer):

    messages = MessageSerializer(many=True)

    class Meta:
        model = Thread
        fields = "__all__"
```

---
transition: fade-out
---

# Example 2: Queries

```sql
# Executed 1X -> Picks 100 threads
SELECT * FROM "weave_thread"
WHERE NOT "weave_thread"."deleted"
ORDER BY "weave_thread"."updated" DESC
LIMIT 100

# Executed 100X -> Picks approx. 100 messages per thread
SELECT * FROM "weave_message"
WHERE "weave_message"."thread_id" = X
ORDER BY "weave_message"."updated" DESC

# Executed approx 10,000X -> Once for each message in each thread
SELECT * FROM "weave_person" WHERE "weave_person"."id" = X LIMIT 21

# Executed 1X -> Pagination
SELECT COUNT(*) AS "__count"
FROM "weave_thread"
WHERE NOT "weave_thread"."deleted"
# {
#    "count": 903,
#    "next": "http://127.0.0.1:8000/api/threads/?page=2",
#    "previous": null,
#    "results": [ ],
# }
```

---
transition: fade-out
---

# Example 2: After prefetching related messages

http://127.0.0.1:8000/api/threads/

<div>
  <i style="margin-right: 20px;" class="text-red-400"><mingcute-time-fill/>135,790ms overall</i>
  <i style="margin-right: 20px;" class="text-red-400"><material-symbols-database/>34,587ms on queries</i>
  <i style="margin-right: 20px;" class="text-red-400"><fluent-text-word-count-24-filled/>10,145 queries</i>
</div>

```python {monaco-diff}
class ThreadViewSet(ReadOnlyModelViewSet):

    queryset = models.Thread.objects.filter(deleted=False)
~~~
class ThreadViewSet(ReadOnlyModelViewSet):

    queryset = (
      models.Thread.objects
      .filter(deleted=False)
      .prefetch_related("messages")
    )
```

### Queries

```sql {all|4-7}
# Executed 1X -> Picks 100 threads
SELECT * FROM "weave_thread" WHERE NOT "weave_thread"."deleted" ORDER BY "weave_thread"."updated" DESC LIMIT 100

# Executed 1X -> Picks approx. 10,000 messages for all threads
SELECT * FROM "weave_message" WHERE "weave_message"."thread_id" IN (THREAD_IDS,)
ORDER BY "weave_message"."updated" DESC

# Executed approx 10,000X -> Once for each message in each thread
SELECT * FROM "weave_person" WHERE "weave_person"."id" = X LIMIT 21

SELECT COUNT(*) AS "__count" FROM "weave_thread" WHERE NOT "weave_thread"."deleted"
```

---
transition: fade-out
---

# Example 2: After prefetching related senders 😲

http://127.0.0.1:8000/api/threads/

<div>
  <i style="margin-right: 20px;" class="text-red-400"><mingcute-time-fill/>7,183ms overall</i>
  <i style="margin-right: 20px;" class="text-red-400"><material-symbols-database/>1,360ms on queries</i>
  <i style="margin-right: 20px;" class="text-green-400"><fluent-text-word-count-24-filled/>4 queries</i>
</div>

```python {monaco-diff}
class ThreadViewSet(ReadOnlyModelViewSet):

    queryset = (
      models.Thread.objects
      .filter(deleted=False)
      .prefetch_related("messages")
    )
~~~
class ThreadViewSet(ReadOnlyModelViewSet):

    queryset = (
      models.Thread.objects
      .filter(deleted=False)
      .prefetch_related("messages", "messages__sent_by")
    )
```

### Queries

```sql {all|7-9}
SELECT * FROM "weave_thread" WHERE NOT "weave_thread"."deleted" ORDER BY "weave_thread"."updated" DESC LIMIT 100

# Executed 1X -> Picks approx. 10,000 messages for all threads
SELECT * FROM "weave_message" WHERE "weave_message"."thread_id" IN (THREAD_IDS,)
ORDER BY "weave_message"."updated" DESC

# Executed approx 1X -> Picks all relevant message senders
SELECT * FROM "weave_person" WHERE "weave_person"."id" IN (MESSAGE_IDS,)
ORDER BY "weave_person"."updated" DESC

SELECT COUNT(*) AS "__count" FROM "weave_thread" WHERE NOT "weave_thread"."deleted"
```

---
transition: fade-out
---

# SELECT COUNT(*)

---
transition: fade-out
---

# SELECT COUNT(*)

---
transition: fade-out
---

# Periodic Tasks

- event-driven architecture

---
transition: fade-out
---

# Periodic Tasks

- .iterator()
- .prefetch_related, .select_related()
- .bulk actions
- avoiding premature qs evaluation

---
transition: fade-out
---

# Caching

---
transition: fade-out
---
