## Caixinha ###

### Caixinha is a simple Dashboard and finance management where you add INs and OUTs with description, value and can even add or choose categories when doing it.

### It has the following languages, frameworks and tools:
- Django
- Django Rest Framework
- Decouple (for treating .env)
- PostgreSQL configuration as Database

### How to use
- Create a virtual environment (just recommended for package encapsulation)
`python -m venv venv`

- Add dependencies
`pip install -r requirements.txt`

- Make migrations
`python manage.py makemigrations`
`python manage.py migrate`

### P.S. change user, name and password in .env to fit your needs
