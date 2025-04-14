# Prerequesist
## Gurobi Licece
To run the optimization, a Gurobi WSL Licence is required. For academic use it can be obtained from https://www.gurobi.com/academia/academic-program-and-licenses/. 
If you have optained a `gurobi.lic` file, place it in `docker-files/secrets`. You can delete the `gurobi.lic.sample` file.
## Set Up Postgres
In `docker-files/secrets` rename `postgres_password.txt.sample` to `postgres_password.txt` and put in it a secure passwoed used for the database.

# Local Deploylemt
Run `docker compose up` in docker-files. You can now open your browser on `localhost` to view the website and upload datasets to be visualized.

# Web Deploylemt without SSL certificates
Change `localhost` in `- SERVER_ADDR=localhost` to your domain.

Run `docker compose up` in docker-files. You can now open your browser on `localhost` to view the website and upload datasets to be visualized.

# Web Deploylemt without SSL certificates
Change `localhost` in `- SERVER_ADDR=localhost` to your domain.

Run `docker compose up -d` in docker-files. To run the server without SSL certificate.
Now you can accuire a certificate with the command `docker compose run --rm  certbot certonly --webroot --webroot-path /var/www/certbot/ -d example.org`. Please replace `example.org` with your domain.

Open the file `docker-files/nginx/templates/http.conf.template` and uncomment the commeted out code.
Restart the containers with the command `docker compose restart` to reload the certificate. This process is also described here: https://mindsers.blog/en/post/https-using-nginx-certbot-docker/
