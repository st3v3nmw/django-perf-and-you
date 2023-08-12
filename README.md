### Django Performance and You

This repository contains a code for a presentation around
profiling Django applications with [Django Silk](https://github.com/jazzband/django-silk).

#### Setting up & Running the Project

- Create a virtual environment called `venv`, preferrably in Python 3.11
- Activate said virtual environment
- Install requirements: `pip install -r requirements.txt`
- Run `setup.sql` to create the database and user
- Run `./generate_data.py` to generate the test data
- Run `python manage.py runserver` to start the server
- You can hit some of the endpoints like:
    - http://127.0.0.1:8000/api/messages/
    - http://127.0.0.1:8000/api/threads/
- Access the Django Silk profiling dashboard on http://127.0.0.1:8000/silk/

#### Slides

- Check out the presentation slides [here](https://www.stephenmwangi.com/talks/django-perf-and-you/)
- Here's a [PDF export](https://raw.githubusercontent.com/st3v3nmw/talks/main/django-perf-and-you/slides-export.pdf)
