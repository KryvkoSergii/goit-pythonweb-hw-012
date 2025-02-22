# Python web app with AuthN and AuthZ

## Description
The application is designed for securely storing contacts. Each user can create and manage their own contacts. The interface is provided by Swagger UI, allowing users to send authenticated requests.

### Features and Functionality
* User registration
* Email confirmation
* Avatar management
* User authentication via username and password
* Reset user password flow
* Secure creation, updating, and deletion of contacts
* Contact search based on specific criteria
* Retrieval of contacts with birthdays in the next 7 days
* Caching token using Redis

By default Swagger UI accessible:
```
http://localhost:8000/docs#/
```
![swagger](static/image.png)
![authentication](static/auth.jpg)

## Tech stack
* SQLAlchemy
* Alembic
* FastAPI

## Integrations
* Application sents confirmation letters using https://meta.ua/
* Application stores avatars (images) in https://cloudinary.com/
* Uses PostgreSQL for data storage 

## Checkout repo 
To clone the repository, use the following command:
```bash
git clone https://github.com/yourusername/goit-pythonweb-hw-012.git
```

## Run application locally
Register and provide credentials for https://meta.ua/ and https://cloudinary.com/ into .env-example file.
Rename .env-example into .env

Install dependencies
```bash
poetry install
``` 
Active environment
```bash
poetry shell
``` 
Apply DDL to DB 
```bash
alembic upgrade head
``` 
To run the server:
```bash
poetry run .\app\main.py
```

### Run postgres for local setup
Start postgres database:
```bash
docker run --name postgres-goit-pythonweb-hw-12 -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=hw12 -d postgres
```
Start Redis cache:
```bash
docker run --name redis-goit-pythonweb-hw-12 -p 6379:6379 -d redis
```

## Run application with docker compose
Register and provide credentials for https://meta.ua/ and https://cloudinary.com/ into .env-example file.
Rename .env-example into .env

```bash
 docker compose -f .\docker-compose.yaml up
```

## Run test
Run tests
```bash
 pytest -v
```
Check code coverage
```bash
 pytest --cov=app
```
Coverage example
```bash
Name                         Stmts   Miss  Cover
------------------------------------------------
app\errors.py                    4      4     0%
app\main.py                     47     47     0%
app\repository\__init__.py       0      0   100%
app\repository\contacts.py      45      1    98%
app\repository\models.py        26      0   100%
app\repository\users.py         27      0   100%
app\schemas.py                  53      0   100%
------------------------------------------------
TOTAL                          202     52    75%
```

## How to
### Visual Code and Poetry
In order to enable poerty env in visual code
```bash
poetry config virtualenvs.in-project true

poetry env list
poetry env remove <current environment>
poetry install
```