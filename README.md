# petheaven-monitoring-bot
Telegram bot that monitor products of petheaven.co.za and send notification when info about product is updated.

## Dev requirements
* Python 3.9.7
* MySQL 8.0.28-0ubuntu0.21.10.3
* Redis 6.2.6

## How to install
1. Clone repository.

2. Install dependencies with:
    ```
    pip install -r requirements.txt
    ```

3. Create MySQL database and then run createdb.sql script:
    ```
    mysql --user=user --password=password db_name < createdb.sql
    ```

4. Create **.env** file in a root directory with your environment variables:
    ```
    TOKEN=token
    DB_HOST=db_host
    DB_USER=db_user
    DB_PASSWORD=db_password
    DB_NAME=db_name
    TEST_DB_NAME=test_db_name
    ```

## Run

To run app use:
```
python3 app.py
```

To run tests use:
```
python3 -m unittest -v
```
Or to run single test:
```
python3 -m unittest -v bot.tests.test_name_of_unit
```