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
layout: intro
---

# Django Performance & You

<div style="display: flex; justify-content: center;">
  <img src="assets/screaming flork.webp" height="100" width="100" />
</div>

<br/><br/>

Presented by <a href="https://github.com/st3v3nmw">@st3v3nmw</a> (~~Software Engineer~~ Senior Intern)

---
transition: fade-out
---

# Agenda

0. Quick walkthrough on the Demo Project & Django Silk
1. The N+1 Query Problem
2. Interpreting EXPLAIN ANALYZE
3. Scan Types
4. Covering & Partial Indexes
5. Periodic Tasks

<a href="https://github.com/st3v3nmw/django-perf-and-you">Link to code repository.</a>

---
transition: fade-out
---

# Profile Before Optimizing

> Premature optimization is the root of all evil ~ Donald Knuth

The problem with premature optimization is that you never know in advance where the bottlenecks will be while coding the system.

A heuristic / rule of thumb to address this would be:

> 1. Make it work
> 2. Make it right
> 3. Use the system and find performance bottlenecks
> 4. Use a profiler in those bottlenecks to determine what needs to be optimized
> 5. Make it fast \
> https://wiki.c2.com/?ProfileBeforeOptimizing=

**Performance Targets**

_Ideally_, backend APIs should target a `p50` latency of `100 - 150ms`, and a `p95` latency of `250 - 300ms`.
Some systems which will remain unnamed have tail latencies (`p99s, p99.9s`) greater than `20,000ms` 💀.
Tail latencies affect your most valuable customers since they have more data, etc.

---
transition: fade-out
---

# Django Silk Setup

In `settings.py`, add the following:

```python
INSTALLED_APPS = (
    ...
    "silk"
)

MIDDLEWARE = [
    "silk.middleware.SilkyMiddleware",
    ...
]
SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = "profiling/"
SILKY_EXPLAIN_FLAGS = {"costs": True, "verbose": True}
```

To enable access to the user interface add the following to your `urls.py`:

```python
urlpatterns += [("silk/", include("silk.urls", namespace="silk"))]
```

Then run `migrate` & `collectstatic`.

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

```python {3-|8}
class MessageViewSet(ReadOnlyModelViewSet):
    """Message viewset."""

    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = models.Message.objects.all()[:100]
        data = serializers.MessageSerializer(messages, many=True).data
        return Response(data=data, status=HTTP_200_OK)
```

```python {5-8}
    @action(methods=["GET"], detail=False)
    def list_some(self, request):
        """List some messages."""
        messages = models.Message.objects.all()[:100]
        data = []
        for message in messages:
          sent_by = message.sent_by
          data.append({"sender": sent_by.full_name, "text": message.text})
        return Response(data=data, status=HTTP_200_OK)
```

<Arrow x1="500" y1="310" x2="400" y2="450" />

---
transition: fade-out
---

# Example 1: Queries

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

# Query Plan 1

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

<br/>

<img src="assets/seq scan.svg"/>

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

```python {4-7}
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

```python {2-}
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

```python {2-}
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

# Example 3: Covering Indexes

http://127.0.0.1:8000/api/messages/

<i style="margin-right: 20px;" class="text-amber-400"><material-symbols-database/>88.364ms</i>

```sql
# We will be focusing on only one query this time
# This query is run during pagination to get the total
# number of objects in the database

SELECT COUNT(*) AS "__count" FROM "weave_message"
WHERE NOT "weave_message"."deleted"
```

#### Query Plan

```sql
Aggregate  (cost=2904.02..2904.03 rows=1 width=8) (actual time=23.799..23.800 rows=1 loops=1)
  Output: count(*)
  ->  Seq Scan on public.weave_message  (cost=0.00..2679.00 rows=90007 width=0) (actual time=0.008..17.689 rows=89964 loops=1)
        Output: id, created, updated, deleted, text, sent_by_id, thread_id
        Filter: (NOT weave_message.deleted)
        Rows Removed by Filter: 10036
Planning Time: 0.063 ms
Execution Time: 23.826 ms
```

---
transition: fade-out
---

# Example 3: Covering Indexes

```python {6}
class AbstractBase(models.Model):
    """Abstract Base."""

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(db_index=True)

    class Meta:
        ordering = ("-updated",)
        abstract = True
```

#### Query Plan

<i style="margin-right: 20px;" class="text-green-400"><material-symbols-database/>14.985ms</i>

```sql
Aggregate  (cost=2116.43..2116.44 rows=1 width=8) (actual time=17.813..17.814 rows=1 loops=1)
  Output: count(*)
  ->  Index Only Scan using weave_message_deleted_9517d20b on public.weave_message  (cost=0.29..1891.41 rows=90007 width=0) (actual time=0.028..11.037 rows=89964 loops=1)
        Output: deleted
        Index Cond: (weave_message.deleted = false)
        Heap Fetches: 0
Planning Time: 0.078 ms
Execution Time: 17.846 ms
```

---
transition: fade-out
---

# Example 3: Covering Indexes

<div style="display: flex; justify-content: center;">
  <img src="assets/index scan.svg" height="450" width="450" />
</div>

---
transition: fade-out
---

# Example 3: Partial Indexes

```python
from django.db.models import Index, Q

class Message(AbstractBase):
    class Meta(AbstractBase.Meta):
        indexes = [
            Index(
                fields=["deleted"],
                name="soft_deletes_ignore",
                condition=Q(deleted=False),
            )
        ]
```

#### Query Plan

<i style="margin-right: 20px;" class="text-green-400"><material-symbols-database/>21.83ms</i>

```sql
Aggregate  (cost=1887.20..1887.21 rows=1 width=8) (actual time=25.893..25.895 rows=1 loops=1)
  Output: count(*)
  ->  Index Only Scan using soft_deletes_ignore on public.weave_message  (cost=0.29..1662.18 rows=90007 width=0) (actual time=0.031..16.012 rows=89964 loops=1)
        Output: deleted
        Heap Fetches: 0
Planning Time: 0.137 ms
Execution Time: 25.931 ms
```

---
transition: fade-out
---

# Example 4: Index Scans

```python {all|1-2|3-4|5-13|14-24}
> from threads.weave.models import *
> deleted_messages = Message.objects.filter(deleted=True)
> str(deleted_messages.query)
SELECT * FROM "weave_message" WHERE "weave_message"."deleted" ORDER BY "weave_message"."updated" DESC
> deleted_messages.explain(analyze=True)  # Before Index
Sort  (cost=3342.87..3367.85 rows=9993 width=104) (actual time=21.625..22.368 rows=10036 loops=1)
  Sort Key: updated DESC
  Sort Method: quicksort  Memory: 1835kB
  ->  Seq Scan on weave_message  (cost=0.00..2679.00 rows=9993 width=104) (actual time=0.020..17.314 rows=10036 loops=1)
        Filter: deleted
        Rows Removed by Filter: 89964
Planning Time: 0.099 ms
Execution Time: 23.005 ms
> deleted_messages.explain(analyze=True)  # After Index
Sort  (cost=2556.54..2581.52 rows=9993 width=104) (actual time=16.202..17.342 rows=10036 loops=1)
  Sort Key: updated DESC
  Sort Method: quicksort  Memory: 1835kB
  ->  Bitmap Heap Scan on weave_message  (cost=113.74..1892.67 rows=9993 width=104) (actual time=1.528..9.371 rows=10036 loops=1)
        Filter: deleted
        Heap Blocks: exact=1676
        ->  Bitmap Index Scan on weave_message_deleted_9517d20b  (cost=0.00..111.24 rows=9993 width=0) (actual time=0.870..0.871 rows=10036 loops=1)
              Index Cond: (deleted = true)
Planning Time: 0.207 ms
Execution Time: 18.260 ms
```

---
transition: fade-out
---

# SELECT COUNT(*) Estimates

Do we really need exact total counts during pagination? 🤔

> Google Search Doesn't...
>> "About 25,200,000,000 results (0.45 seconds)"

```python
# threads.weave.paginators.py

class CustomPaginator(Paginator):

    @cached_property
    def count(self) -> int:
        """Return the total number of objects, across all pages."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT reltuples FROM pg_class WHERE relname = %s",
                [self.object_list.query.model._meta.db_table],
            )
            return int(cursor.fetchone()[0])

class CustomPageNumberPagination(PageNumberPagination):

    django_paginator_class = CustomPaginator
```

---
transition: fade-out
---

# SELECT COUNT(*) Estimates

<i style="margin-right: 20px;" class="text-green-400"><material-symbols-database/>1.39ms</i>

#### Query

```sql
SELECT reltuples FROM pg_class WHERE relname = weave_message
# Output = 100,000; Correct = 89,964 😖
# Filters/conditions not applied
```

> The catalog `pg_class` catalogs tables and most everything else that has columns or is otherwise similar to a table. This includes indexes, views, materialized views, composite types, and TOAST tables; see `relkind`. When we mean all of these kinds of objects we speak of “relations”. \
> `reltuples` is the number of live rows in the table. This is only an estimate used by the planner. It's updated by `VACUUM`, `ANALYZE`, and a few DDL commands such as `CREATE INDEX`. \
> ~ https://www.postgresql.org/docs/current/catalog-pg-class.html

#### Query Plan

```sql
Index Scan using pg_class_relname_nsp_index on pg_class
  (cost=0.28..8.29 rows=1 width=4)
  (actual time=0.043..0.046 rows=1 loops=1)
```

Are we able to surface the count estimates from the query planner? Probably not.

---
transition: fade-out
---

# SELECT COUNT(*) Estimates

Introducing `TABLESAMPLE SYSTEM/BERNOULLI (n)` 🥁

<i style="margin-right: 20px;" class="text-green-400"><material-symbols-database/>11.50ms</i>

#### But can we do better? Yes!

> The `TABLESAMPLE SYSTEM/BERNOULLI` method returns an approximate percentage of rows. It generates a random number for each physical storage page for the underlying relation. Based on this random number and the sampling percentage specified, it either includes or exclude the corresponding storage page. If that page is included, the whole page will be returned in the result set.\
> ~ https://wiki.postgresql.org/wiki/TABLESAMPLE_Implementation

<br/>

```sql
SELECT COUNT(*) AS "__count" FROM "weave_message" TABLESAMPLE BERNOULLI (10) REPEATABLE (42)
WHERE NOT "weave_message"."deleted"
# Average output from several runs = 90,122.5; Correct = 89,964
# Off by ONLY 0.18%
```

<br/>

#### Query Plan

```sql
Aggregate (cost=1801.50..1801.51 rows=1 width=8) (actual time=11.505..11.506 rows=1 loops=1)
# Original time taken: Around 25ms
```

---
transition: fade-out
---

# SELECT COUNT(*) Estimates

```python {4-}
class CustomPaginator(Paginator):
    @cached_property
    def count(self) -> int:
        """Return an estimate of the total number of objects.
        Could be made more robust by first running the normal COUNT(*)
        with a `SET LOCAL statement_timeout TO 50`
        and then reverting to this if that doesn't complete in time.
        """
        with connection.cursor() as cursor:
            db_table = self.object_list.model._meta.db_table
            query = (
                self.object_list.annotate(__count=Count("*"))
                .values("__count")
                .order_by()
                .query
            )
            query.group_by = None
            query_string = str(query)
            query_string = query_string.replace(
                f'FROM "{db_table}"',
                f'FROM "{db_table}" TABLESAMPLE BERNOULLI (10) REPEATABLE (42)',
            )
            cursor.execute(query_string)
            return 10 * int(cursor.fetchone()[0])
```

---
transition: fade-out
---

# Periodic Tasks

- Periodic tasks are one of the 4 horsemen of the apocalypse 😏. They should be avoided like the plague.
  - Instead, prefer event-driven tasks
    - These typa tasks run immediately after an event e.g. `instance.save`, `instance.create`, `instance.transition`, Django signals, etc, ...
    - You can use Celery to set-up automatic retries for certain errors
      - Retry with exponential backoff to reduce load
  - For reporting, separate your transactional (Postgres) and analytical (BigQuery) databases so that reports don't slow down your main database
- If you must:
  - Do things in bulk e.g. `bulk_create`, `bulk_update`
  - Use iterators when looping over a large number of objects (`qs.iterator()`)
    - Helps reduce memory usage
  - Add indexes to fields that are used to filter. This speeds up reads but slows down writes (there's no such thing as a free lunch)

---
transition: fade-out
---

# Periodic Tasks

```python
q = Entry.objects.filter(headline__startswith="What")
q = q.filter(pub_date__lte=datetime.date.today())
q = q.exclude(body_text__icontains="food")
print(q)
```

<br/>

- Realize that querysets are lazy, so avoid things like:
  - `len(qs)` -> `qs.count()`
  - `list(qs)` 😒
  - `bool(qs)` -> `qs.exists()`

<br/>

> QuerySets are lazy – the act of creating a QuerySet doesn’t involve any database activity. You can stack filters together all day long, and Django won’t actually run the query until the QuerySet is evaluated \
> https://docs.djangoproject.com/en/4.2/ref/models/querysets/#when-querysets-are-evaluated

---
layout: statement
---

# Thank You!

<br/><br/>

### And if everything fails, try API caching lol 🫠
