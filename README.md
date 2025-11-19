# Free watermark bot

**English**

A bot can add a watermark to an image.
A watermark can be either an image or text.

## ✨ Requirements
- 📥 **docker-compose**
- 📋 **python**

## ✨ Reestrictions / Only for free bot. There are no such restrictions for Pro version.
- There are no user restrictions. All settings are the same for everyone
- The bot doesn't clean up photo folders
- There is only Russian language
  
## ✨ The pro version of bot includes
-  An admin panel
-  A limit of 10 photos per day for members
-  Subscription management
-  Automatic folder cleaning
-  English language


## 🛠️ Installation
```bash
git clone https://github.com/adjuster2004/watermark/
cd watermark
```
**Edit** config.yaml
telegram:
  **admin_id**: here is your token
  **bot_token**: here is your bot's token
  **channel_id**: 'Specify the channel ID of the channel in which the bot will post' (Optional parameter)

**Examle**
  **admin_id**: 9989543478
  **bot_token**: 6183733821:AAHKNDHFUDJFjiqtBWkWd0FMDYSLRKJT2YxXY
  **channel_id**: '-**100**2369337436'

Channel IDs:

- In Telegram, find a bot like @username_to_id_bot.
- To get the ID of a channel, you must forward a message from that channel to the bot.
- Important: Do NOT send a link to the channel or type the channel name. You must use Telegram's "Forward" functionality.
- Go into your source channel.
- Tap and hold (or right-click) on any message.
- Select "Forward".
- Choose @userinfobot as the recipient.
- The bot will reply with the correct Channel ID. It will likely be a negative number (e.g., -100123456789).
- Repeat the forwarding process for your destination channel.
- Finding a Specific Message ID (Optional): By default, the script reposts the latest message. To repost a specific message, you need its ID.

- Go to the source channel/group and find the message.
- Right-click on it and select Copy Message Link.
- The link will look like https://t.me/channel_name/12345. The number at the end (12345) is the message ID.
- Add this to your .env file as SOURCE_MESSAGE_ID.

## 🛠️ Run
```bash
docker-compose up -d
```
## 🛠️ Stop
```bash
docker-compose down
```
-------------------------------------------------

**Русский**

Бот может добавить водяной знак к изображению.
Водяной знак может быть изображением или текстом.

## ✨ Требования
- 📥 **docker-compose**
- 📋 **python**

## ✨ Ограничения / Только для бесплатного бота. Для Pro-версии таких ограничений нет.
- Нет ограничений для пользователей. Все настройки одинаковы для всех.
- Бот не чистит папки с фотографиями.
- Язык только русский.

## ✨ Pro версия бота включает в себя
– Панель администратора
– Лимит на 10 фотографий в день для участников (значение можно поменять через админ панель)
– Управление подписками (безлимитное количество фотографий в день)
– Автоматическая очистка папок
– Английский язык


## 🛠️ Установка
```bash
git clone https://github.com/adjuster2004/watermark/
cd watermark
```
**Редактировать** config.yaml
telegram:
  **admin_id**: здесь укажите Ваш ID
  **bot_token**: Здесь укажите токен бота (можно взять у @fatherbot)
  **channel_id**: 'ID канала или чата, куда бот будет постить картинки с watermark' (Необязательный параметр)

**Пример**
  **admin_id**: 9989543478
  **bot_token**: 6183733821:AAHKNDHFUDJFjiqtBWkWd0FMDYSLRKJT2YxXY
  **channel_id**: '-**100**2369337436'

Идентификаторы каналов:

- В Telegram найдите бота, например @username_to_id_bot.
- Чтобы получить идентификатор канала, необходимо переслать сообщение с этого канала боту.
- Важно: НЕ отправляйте ссылку на канал и не вводите его название. Используйте функцию «Пересылка» в Telegram.
- Перейдите в исходный канал.
- Нажмите и удерживайте (или щелкните правой кнопкой мыши) любое сообщение.
- Выберите «Переслать».
- Выберите @userinfobot в качестве получателя.
- Бот ответит правильным идентификатором канала. Скорее всего, это будет отрицательное число (например, -100123456789).
- Повторите процесс пересылки для целевого канала.
- Поиск конкретного идентификатора сообщения (необязательно): По умолчанию скрипт перепечатывает последнее сообщение. Чтобы перепечатать конкретное сообщение, вам нужен его идентификатор.

- Перейдите в исходный канал/группу и найдите сообщение. - Щёлкните по нему правой кнопкой мыши и выберите «Копировать ссылку на сообщение».
- Ссылка будет выглядеть так: https://t.me/channel_name/12345. Число в конце (12345) — это идентификатор сообщения.
- Добавьте это в файл .env как SOURCE_MESSAGE_ID.

## 🛠️ Запустить
```bash
docker-compose up -d
```
## 🛠️ Остановить
```bash
docker-compose down
```

### 📋 Фотографии

<img width="530" height="415" alt="image" src="https://github.com/user-attachments/assets/efedcbb7-4a0a-4aca-8ebb-65cb8ec00b2b" />

<img width="482" height="693" alt="image" src="https://github.com/user-attachments/assets/8cfe623e-37ea-427f-8800-9d5fb2de3f0b" />

<img width="409" height="339" alt="image" src="https://github.com/user-attachments/assets/2445920e-251b-4389-acd3-c6e081dc1dcd" />

<img width="473" height="401" alt="image" src="https://github.com/user-attachments/assets/b1ffc8eb-010f-4d26-861f-613676fd9108" />

<img width="289" height="440" alt="image" src="https://github.com/user-attachments/assets/2f8c6586-684a-4f45-be24-f76a89b99952" />

<img width="367" height="92" alt="image" src="https://github.com/user-attachments/assets/6fe06708-73be-4935-a62b-77623ba4c409" />


## 📄 Лицензия
Этот проект распространяется под лицензией **MIT**.

Copyright (c) 2025 Sergey S @adjuster2004

Подробности в файле [LICENSE](LICENSE).
