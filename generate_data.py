#!/usr/bin/env python
"""Generate test data."""
import os
from random import randint

import django
from faker import Faker
from tqdm import trange

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "threads.config.settings")
django.setup()

from threads.weave.models import Message, Person, Thread

N_PERSONS = 1_000
N_THREADS = 1_000
N_MESSAGES = 100_000

print("Resetting DB...\n")
Message.objects.all().delete()
Thread.objects.all().delete()
Person.objects.all().delete()

fake = Faker()
Faker.seed(0)

persons = []
print("Generating persons data...")
for _ in trange(N_PERSONS):
    first_name = fake.first_name()
    last_name = fake.last_name()
    persons.append(
        Person(
            first_name=first_name,
            last_name=last_name,
            email_address=(
                f"{first_name}.{last_name}.".lower() + fake.email(safe=True)
            ),
            deleted=fake.boolean(chance_of_getting_true=10),
        )
    )
print("Saving to DB...\n")
Person.objects.bulk_create(persons)

threads = []
print("Generating threads data...")
for _ in trange(N_THREADS):
    threads.append(
        Thread(
            title=fake.catch_phrase(),
            deleted=fake.boolean(chance_of_getting_true=10),
        )
    )
print("Saving to DB...\n")
Thread.objects.bulk_create(threads)

messages = []
print("Generating messages data...")
for _ in trange(N_MESSAGES):
    messages.append(
        Message(
            text=fake.sentence(nb_words=10),
            sent_by=persons[randint(0, N_PERSONS - 1)],
            thread=threads[randint(0, N_THREADS - 1)],
            deleted=fake.boolean(chance_of_getting_true=10),
        )
    )
print("Saving to DB...")
Message.objects.bulk_create(messages)
