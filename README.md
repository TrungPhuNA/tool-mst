python -m venv venv
source venv/bin/activate
#pip install selenium beautifulsoup4 flask mysql-connector-python
pipenv install selenium beautifulsoup4 flask mysql-connector-python
pip freeze


pip freeze > requirements.txt
https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json

#INSTALL
pipenv shell
pipenv install selenium beautifulsoup4 flask mysql-connector-python gunicorn python-dotenv
flask run hoạc flask run --reload

#Cấu hình run forever
Sau khi run thành công 
pipenv install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app => Chạy ok rồi thì  nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app &
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app --reload --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log &

Hoạc cập nhật tay = pkill -HUP gunicorn


#Docker
``` 
RUN => docker-compose up -d
Kd lại docker => docker-compose down || docker compose down
Xem logs => docker logs selenium-hub
RUn theo file => docker-compose -f docker-compose_v2.yml up -d
```
- Để mở trình duyệt thì cài thêm
```
brew install --cask tigervnc-viewer
```
```
    mở tigervnc => localhost:5900 MK secret
```
#
Danh sách => http://mst.s-notification.com/tax-info-list
Tìm kiếm => http://127.0.0.1:5000?param=040094022488

## Login
``` 
pip install flask-bcrypt flask-login

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```