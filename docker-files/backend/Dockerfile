FROM python:3.10

WORKDIR /python-docker
ENV PYTHONUNBUFFERED=1

# Create a group and user to run our app
ARG APP_USER=www-data
#RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}


COPY ./code ./code
COPY gunicorn_config.py gunicorn_config.py
COPY requirements.txt requirements.txt

RUN pip3 install gunicorn

RUN pip3 install -r requirements.txt

COPY cleanup-cron /etc/cron.d/cleanup-cron

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/cleanup-cron

# Apply cron job
#RUN crontab /etc/cron.d/cleanup-cron

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

USER ${APP_USER}:${APP_USER}



CMD ["gunicorn", "--config", "gunicorn_config.py", "code.main:app"]
 #&& cron && tail -f /var/log/cron.log