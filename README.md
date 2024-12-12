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
flask run

#Cấu hình run forevr
Sau khi run thành công 
pipenv install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app => Chạy ok rồi thì  nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app &
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app --reload --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log &

Hoạc cập nhật tay = pkill -HUP gunicorn


#Docker
docker-compose up -d

```
ALTER TABLE `tax_info`  ADD `param_search` VARCHAR(191) NULL  AFTER `status`;
```
#
Danh sách => http://mst.s-notification.com/tax-info-list
Tìm kiếm => http://127.0.0.1:5000/api/get-tax-info?param=040094022486