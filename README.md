# Streaver - CSV to JSON Normalizer

Aplicación Streamlit que procesa archivos CSV, normaliza los datos y los almacena en PostgreSQL, generando archivos JSON formateados.

## Características

- 📊 Interfaz web intuitiva con Streamlit
- 🔄 Normalización de números telefónicos a formato xxx-xxx-xxxx
- 🗄️ Almacenamiento en PostgreSQL con dos tablas (original y normalizada)
- 📝 Exportación a JSON con formato indentado (2 espacios) y claves ordenadas
- ✅ Validación de datos y reporte de errores por línea
- 📈 Ordenamiento alfabético por apellido y nombre

## Estructura del Proyecto

```
Streaver/
├── app/
│   ├── main.py              # Aplicación principal Streamlit
│   ├── assets/
│   │   └── image.png        # Logo de la aplicación
│   └── utils/
│       ├── database.py      # Gestor de base de datos PostgreSQL
│       └── normalizer.py    # Lógica de normalización de datos
├── Dockerfile               # Configuración Docker para la app
├── docker-compose.yml       # Orquestación de servicios
├── requirements.txt         # Dependencias Python
├── .env.example            # Ejemplo de variables de entorno
└── README.md               # Este archivo
```

## Requisitos

- Python 3.11+
- PostgreSQL 15+
- Docker y Docker Compose (opcional)

## Instalación

### Opción 1: Con Docker (Recomendado)

1. Clonar el repositorio
2. Copiar el archivo de configuración:
```powershell
Copy-Item .env.example .env
```

3. Iniciar los servicios:
```powershell
docker-compose up -d
```

4. Acceder a la aplicación en: http://localhost:8501

### Opción 2: Instalación Local

1. Instalar PostgreSQL y crear la base de datos:
```sql
CREATE DATABASE streaver_db;
```

2. Crear un entorno virtual e instalar dependencias:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```powershell
Copy-Item .env.example .env
# Editar .env con tus credenciales de PostgreSQL
```

4. Ejecutar la aplicación:
```powershell
streamlit run app/main.py
```

## Uso

1. Abrir la aplicación en el navegador
2. Cargar un archivo CSV con las columnas: `firstname`, `lastname`, `phone`, `zip`
3. Hacer clic en "Process and Normalize Data"
4. Revisar los resultados normalizados
5. Descargar el archivo `result.json` generado

### Ejemplo de CSV

```csv
firstname,lastname,phone,zip
John,Doe,123-456-7890,12345
Jane,Smith,(555) 123-4567,54321
```

### Ejemplo de JSON de Salida

```json
{
  "entries": [
    {
      "firstname": "John",
      "lastname": "Doe",
      "phone": "123-456-7890",
      "zip": "12345"
    },
    {
      "firstname": "Jane",
      "lastname": "Smith",
      "phone": "555-123-4567",
      "zip": "54321"
    }
  ],
  "errors": []
}
```

## Reglas de Normalización

1. **Números telefónicos**: Se convierten al formato `xxx-xxx-xxxx`
2. **Códigos postales**: Se validan formatos de 5 dígitos
3. **Ordenamiento**: Las entradas se ordenan alfabéticamente por `(lastname, firstname)`
4. **Errores**: Las líneas con errores se registran en la lista `errors` con su número de línea
5. **JSON**: Salida con indentación de 2 espacios y claves ordenadas ascendentemente

## Tablas de Base de Datos

### original_data
- `id`: Serial Primary Key
- `upload_timestamp`: Timestamp
- `raw_data`: JSONB (datos originales del CSV)

### normalized_data
- `id`: Serial Primary Key
- `upload_timestamp`: Timestamp
- `firstname`: VARCHAR(255)
- `lastname`: VARCHAR(255)
- `phone`: VARCHAR(20)
- `zip`: VARCHAR(10)
- `original_id`: Foreign Key a original_data

## Tecnologías

- **Streamlit**: Framework de interfaz web
- **PostgreSQL**: Base de datos relacional
- **Pandas**: Procesamiento de datos
- **psycopg2**: Conector PostgreSQL
- **Docker**: Contenerización

## Licencia

MIT