
# Веб-сокет на FastApi для оповещения авторизированных пользователей

В данном руководстве описывается, как клонировать репозиторий, протестировать его локально и развернуть как службу с помощью `systemd`.

## Оглавление

- [Начало работы](#начало-работы)
  - [Требования](#требования)
  - [Клонирование репозитория](#клонирование-репозитория)
  - [Настройка виртуального окружения](#настройка-виртуального-окружения)
  - [Запуск тестов](#запуск-тестов)
- [Развертывание с помощью `systemd`](#развертывание-с-помощью-systemd)
  - [Создание файла службы Systemd](#создание-файла-службы-systemd)
  - [Запуск службы](#запуск-службы)

---

## Начало работы

### Требования

Убедитесь, что у вас установлены следующие компоненты:

- Python 3.7+
- `pip` (менеджер пакетов Python)
- `git`
- Виртуальное окружение (`venv`)

### Клонирование репозитория

Для клонирования репозитория на локальный компьютер:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### Настройка виртуального окружения

После клонирования создайте виртуальное окружение для управления зависимостями:

```bash
python3 -m venv venv
source venv/bin/activate  # Для Linux/macOS
# Для Windows: venv\Scripts\activate
```

Теперь установите зависимости:

```bash
pip install -r requirements.txt
```

### Запуск тестов

Если в репозитории есть тесты (необходимо настроить в зависимости от вашего проекта):

1. Убедитесь, что у вас есть файл `.env`, который включает тестовый режим:

```bash
TESTING=True
```

2. Запустите FastAPI-приложение:

```bash
uvicorn main:app --reload
```

Это запустит приложение FastAPI в режиме разработки, что позволит вам тестировать его.

Доступ к приложению можно получить по адресу:

```bash
http://127.0.0.1:8000
```

Для тестирования WebSocket перейдите по адресу:

```bash
http://127.0.0.1:8000/test
```

---

## Развертывание с помощью `systemd`

Чтобы запустить FastAPI-приложение в фоновом режиме с помощью `systemd`, выполните следующие шаги.

### Создание файла службы Systemd

1. Сначала найдите полный путь к `uvicorn` в виртуальном окружении:

```bash
which uvicorn
```

Вы получите путь, например, `/home/user/your-repo-name/venv/bin/uvicorn`.

2. Создайте файл службы в `/etc/systemd/system/` с именем `your-app.service`:

```bash
sudo nano /etc/systemd/system/your-app.service
```

3. Добавьте в файл следующий контент:

```ini
[Unit]
Description=FastAPI Web Service
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/home/user/your-repo-name
ExecStart=/home/user/your-repo-name/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Замените пути на ваши фактические пути, и убедитесь, что указаны правильные `User` и `WorkingDirectory`.

### Запуск службы

1. Перезагрузите `systemd`, чтобы зарегистрировать новую службу:

```bash
sudo systemctl daemon-reload
```

2. Включите службу, чтобы она запускалась при загрузке системы:

```bash
sudo systemctl enable your-app.service
```

3. Запустите службу:

```bash
sudo systemctl start your-app.service
```

4. Проверьте статус, чтобы убедиться, что служба запущена:

```bash
sudo systemctl status your-app.service
```

Теперь ваше FastAPI-приложение должно работать как служба, и вы можете получить доступ к нему по адресу `http://your-server-ip:8000`.

---

### Остановка или перезапуск службы

Чтобы остановить службу:

```bash
sudo systemctl stop your-app.service
```

Чтобы перезапустить службу:

```bash
sudo systemctl restart your-app.service
```

---

## Заключение

Теперь вы успешно настроили, протестировали и развернули FastAPI-приложение с помощью `systemd`. Если вам нужно внести изменения в службу, не забудьте перезагрузить `systemd` командой `sudo systemctl daemon-reload` после каждого обновления.

--- 

