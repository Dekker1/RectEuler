FROM bitnami/postgresql

COPY 0_init_db.sql /docker-entrypoint-initdb.d/
COPY 1_data.sql /docker-entrypoint-initdb.d/