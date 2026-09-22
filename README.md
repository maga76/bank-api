# Bank API

API использует токен в заголовке `Authorization: Bearer <token>`.

1. Отправьте `POST /api/accounts/auth/` с `{"phone_num": "992900000001"}` для получения OTP.
2. При регистрации отправьте `POST /api/accounts/verify/` с `phone_num`, `otp`, `fname`, `lname` и `passport_id`. Ответ содержит `token`.
3. Для повторного входа запросите новый OTP через `/api/accounts/auth/`, затем отправьте `POST /api/accounts/login/` с `phone_num` и `otp`. Ответ содержит `token`.
4. Передавайте токен в каждом защищённом запросе:

```http
GET /api/accounts/profile/ HTTP/1.1
Authorization: Bearer <token>
```

В `/swagger/` нажмите **Authorize** и введите `Bearer <token>`.
Схему API можно скачать по `/swagger.json` или `/swagger.yaml`.

В текущей конфигурации для разработки OTP выводится в консоль сервера.
OTP действует 5 минут. После обновления проекта примените миграции: `.venv/bin/python manage.py migrate`.

Для запуска без `DEBUG` задайте `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` и
`DJANGO_ALLOWED_HOSTS` (список доменов через запятую). В этом режиме включены
перенаправление на HTTPS, защищённые cookie и HSTS. Публикуйте API только через HTTPS.
Если все поддомены тоже работают только по HTTPS, можно дополнительно включить
`DJANGO_HSTS_INCLUDE_SUBDOMAINS=1` и `DJANGO_HSTS_PRELOAD=1`.
