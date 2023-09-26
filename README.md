# Foodgram project

Foodgram - сайт любителей вкусно покушать. Вы можете делиться своими любимыми рецептами, добавлять в избранное рецепты других пользователей, формировать список покупок, необходимый для выбранных вами рецептов.

### Установка и настройка

Следуйте этим шагам, чтобы установить и настроить проект на своем локальном компьютере.

#### Требования

- Python (версия ^3.9)
- Django (версия ^4.0)
- Node.js
- npm (устанавливается вместе с Node.js)
- Gunicorn
- Nginx

#### Установка и настройка Django Api

Клонируйте репозиторий проекта:
```
$ git@github.com:verafadeeva/foodgram-project-react.git
```
Перейдите в каталог проекта
```
$ cd foodgram-project-react/backend/
```
Создайте и активируйте виртуальное окружение
```
$ python3 -m venv venv
$ source venv/bin/activate
```
Установите зависимости
```
$ python -m pip install -r requirements.txt
```
Из директории с файлом manage.py: примените миграции и запустите сервер
```
$ python manage.py migrate
$ python manage.py runserver
```

### Установка и настройка React

Находясь в директории foodgram-project-react/frontend, установите зависимости
```
$ npm install
```
Разверните frontend
```
$ nmp start
```
