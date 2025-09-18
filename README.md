# Open-Meteo Weather

App en **Python/Django** para cargar datos horarios de **temperatura** y **precipitación** desde la API pública de [Open-Meteo](https://open-meteo.com/en/docs), almacenarlos en **PostgreSQL** y consultarlos.

## Tecnologías

- Django + Django REST Framework  
- PostgreSQL + psycopg3  
- Requests  
- Pandas / NumPy
- Pytest 


## Base de datos

- **City**: info de la ciudad (nombre, país, coords).  
- **HourlyWeather**: datos horarios con FK a City.  

## Uso

Instalar dependencias:
```bash
pip install -r requirements.txt
```

Migrar
```bash
python manage.py makemigrations
python manage.py migrate
```

Cargar datos:
```bash
python manage.py load_weather --city <city> --start <AAAA-MM-DD> --end <AAAA-MM-DD>
```

## Endpoints

Todos los endpoints están bajo `/api/`.

### 1) Temperatura
**GET** `/api/temperature/`  
**Parámetros:**
- `city` (str, requerido)
- `start`, `end` (YYYY-MM-DD, requeridos)
- `threshold` (float, opcional, default 30.0)
- `threshold_low` (float, opcional, default 0.0)
- `timezone` (str, opcional, default Europe/Madrid)

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/api/temperature/?city=Madrid&start=2024-07-01&end=2024-07-03&threshold=30"
```

### 2) Precipitación
**GET** `/api/precipitation/`  
**Parámetros:**
- `city` (str, requerido)
- `start`, `end` (YYYY-MM-DD, requeridos)
- `timezone` (str, opcional, default Europe/Madrid)

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/api/precipitation/?city=Madrid&start=2024-07-01&end=2024-07-03"
```

### 3) Resumen (multi-ciudad)
**GET** `/api/summary/`  
**Parámetros (uno de los dos primeros):**
- `city` (str) **o** `cities` (lista separada por comas)  
- `start`, `end` (YYYY-MM-DD, requeridos)  
- `timezone` (str, opcional, default Europe/Madrid)  

**Ejemplos:**
```bash
# Una ciudad
curl "http://127.0.0.1:8000/api/summary/?city=Madrid&start=2024-07-01&end=2024-07-03"

# Varias ciudades
curl "http://127.0.0.1:8000/api/summary/?cities=Madrid,Sevilla&start=2024-07-01&end=2024-07-03"
```

## Decisiones de diseño

He realizado la prueba con **Django** porque sé que es el framework con el que trabajáis y quería aprovechar para familiarizarme con él.  
De este modo, además de mostrar mis conocimientos en **Python**, **Pandas** y **NumPy**, puedo demostrar mi capacidad de adaptarme rápidamente y aprender nuevas tecnologías en contexto real.  

La estructura sigue la organización típica de un proyecto Django, adaptada a las necesidades de la prueba.
