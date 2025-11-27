# iAsisst-UTESA
Agente que ofrece acceso inmediato a los datos oficiales que necesita para enfocarse en lo que realmente importa: sus estudios y su futuro profesional.

## 🛠️ 2. Stack Tecnológico

### 2.1. Backend API
- **Tecnología:** Python (3.10+)
- **Propósito:** Lógica del servidor y ejecución de la IA.

### 2.2. Framework Web
- **Tecnología:** FastAPI / Uvicorn
- **Propósito:** Gestión de endpoints y peticiones POST.

### 2.3. Inteligencia Artificial
- **Tecnología:** NumPy
- **Propósito:** Implementación de la Red Neuronal desde cero.

### 2.4. Base de Datos
- **Tecnología:** MySQL / XAMPP
- **Propósito:** Almacenamiento de datos de entrenamiento y configuración.

### 2.5. Frontend
- **Tecnología:** HTML/CSS+Tailwinds/JavaScript
- **Propósito:** Interfaz de usuario y comunicación con la API.

## ⚙️ 3. Instalación y Configuración para funcionamiento

### 3.1. Requisitos Previos
- Python 3.10 o superior  
- MySQL Server (XAMPP, WAMP, o similar)

### 3.2. Configuración del Entorno Python
- Crear entorno virtual: `python -m venv venv`
- Activar entorno (Windows): `.\venv\Scripts\activate`
- Instalar dependencias:  
  `pip install uvicorn fastapi numpy mysql-connector-python`

### 3.3. Configuración de la Base de Datos
- Iniciar servidor MySQL  
- Crear base de datos llamada **chatbot**  
- Poblar tablas (`preguntas`, `respuestas`, `chatbot_logica`) con el archivo `chatbot.sql` 
- Verificar credenciales en `combined_service.py`

## ▶️ 4. Ejecución y Entrenamiento

### 4.1. Iniciar el Servidor
- Comando: `python -m uvicorn combined_service:app --port 8000`
- URL: `http://127.0.0.1:8000`

### 4.2. Acceso a la Documentación
- URL: `http://127.0.0.1:8000/docs`  
- Permite verificar y probar endpoints de forma interactiva.

### 4.3. Entrenar el Modelo de IA (Paso Crucial Único)
**Propósito:** Cargar datos de la DB y activar el modelo.  
**Pasos:**
1. Abrir `http://127.0.0.1:8000/docs`
2. Buscar el endpoint **POST /train**
3. Clic en “Try it out” → “Execute”

## 💬 5. Uso y Pruebas
**Intención: Lógica de Crédito**  
Ejemplo: `dime el costo de 20 creditos`

**Intención: Lógica de Aula**  
Ejemplo: `aula B405`

**Intención: IA/Similitud**  
Ejemplo: `quien es el director de la carrera de software`

**Intención: Lógica de Horario**  
Ejemplo: `horario MAT-360-001 CALCULO IV 4 MA8:30 pm`
