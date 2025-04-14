# Prerequesist
## Gurobi Licece
To run the optimization, a Gurobi WSL Licence is required. For academic use it can be obtained from https://www.gurobi.com/academia/academic-program-and-licenses/. If you have optained a `gurobi.lic` file, place it in `docker-files/secrets`. You can delete the `gurobi.lic.sample` file.
## Set Up Postgres
In `docker-files/secrets` rename `postgres_password.txt.sample` to `postgres_password.txt` and put in it a secure passwoed used for the database.

# Local Deploylemt
Rum `docker comoise up` in docker-files. You can now open your browser on `localhost` to view the website.