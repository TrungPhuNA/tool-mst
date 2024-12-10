python -m venv venv
source venv/bin/activate
#pip install selenium beautifulsoup4 flask mysql-connector-python
pipenv install selenium beautifulsoup4 flask mysql-connector-python
pip freeze


pip freeze > requirements.txt
https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json



#INSTALL
pipenv shell
pipenv install selenium beautifulsoup4 flask mysql-connector-python gunicorn
flask run

# chay

Sau khi run thành công 
pipenv install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app => Chạy ok rồi thì  nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app &
gunicorn -w 4 -b 0.0.0.0:5000 app:app --access-logfile gunicorn_access.log --error-logfile gunicorn_error.log
