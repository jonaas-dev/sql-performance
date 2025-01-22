# Proyecto PostgreSQL con Docker

Este proyecto utiliza Docker para ejecutar una base de datos PostgreSQL de manera sencilla.

## Requisitos

- Docker
- Docker Compose

## Configuración

1. Clona este repositorio y navega al directorio.
2. Levanta el contenedor con Docker Compose:
   ```bash
   docker-compose up -d
   ```
3. Accede a la base de datos PostgreSQL:
    Host: localhost
    Puerto: 5432
    Usuario: user
    Contraseña: password
    Base de datos: test_db

4. Para detener el contenedor:
   ```bash
   docker-compose down
   ```


## Play 

```bash
docker exec -it postgres-db psql -U user -d test_db


# test_db=# \dt
#        List of relations
#  Schema | Name  | Type  | Owner
# --------+-------+-------+-------
#  public | users | table | user
# (1 row)

# test_db=# SELECT * FROM users;
#  id |    name    |         email
# ----+------------+------------------------
#   1 | John Doe   | john.doe@example.com
#   2 | Jane Smith | jane.smith@example.com
# (2 rows)

# test_db=# EXPLAIN ANALYZE SELECT * FROM users;
#                                              QUERY PLAN
# ----------------------------------------------------------------------------------------------------
#  Seq Scan on users  (cost=0.00..11.70 rows=170 width=440) (actual time=0.018..0.020 rows=2 loops=1)
#  Planning Time: 0.067 ms
#  Execution Time: 0.049 ms
# (3 rows)
```


