FROM python:3.10 AS packagepython

ARG GRB_VERSION=9.5.2
ENV PYTHONUNBUFFERED=1

LABEL vendor="Gurobi"
LABEL version=${GRB_VERSION}

# update system and certificates
RUN apt-get update \
    && apt-get install --no-install-recommends -y\
       ca-certificates  \
       p7zip-full \
       zip \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    \
RUN apt-get install ttf-mscorefonts-installer

# Set the application directory
WORKDIR /app

# Install the application dependencies
ADD requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Copy the application code 
ADD ./code /app

# Command used to start the application
CMD ["python","-u","main.py"]