import numpy as np
import re
import mysql.connector
from datetime import datetime, timedelta
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import warnings

# ====================================================
# ?  CONFIGURACIÓN Y DATOS
# ====================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "chatbot" 
}

# Variables globales inicializadas a None
preguntas_global = []
respuestas_global = []
vocabulario = []
W1, b1, W2, b2 = None, None, None, None
lr = 0.1

# Desactivar advertencias de NumPy de MINGW-W64
warnings.filterwarnings("ignore", message="Numpy built with MINGW-W64 on Windows 64 bits is experimental")
warnings.filterwarnings("ignore", message="invalid value encountered in exp2")
warnings.filterwarnings("ignore", message="invalid value encountered in log10")

# ====================================================
# ? CONEXIÓN Y CARGA DE DATOS DESDE LA DB
# ====================================================

def get_db_connection():
    """Establece la conexión a la base de datos."""
    try:
        # Intenta conectar
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        # Imprime el error para que Uvicorn lo muestre, PERO NO CRASHEA EL PROGRAMA
        print(f"ERROR DE CONEXIÓN A LA DB AL INICIO: {err}")
        return None

def load_training_data_from_db():
    """Carga los datos de la DB."""
    conexion = get_db_connection()
    if not conexion:
        return [], []
    
    cursor = conexion.cursor(dictionary=True)
    sql = """
        SELECT p.texto AS pregunta, r.texto AS respuesta
        FROM preguntas p
        JOIN respuestas r ON p.respuesta = r.codigo
    """
    cursor.execute(sql)
    rows = cursor.fetchall()
    cursor.close()
    conexion.close()
        
    preguntas_list = [row['pregunta'] for row in rows]
    respuestas_list = [row['respuesta'] for row in rows]
    
    return preguntas_list, respuestas_list


# ====================================================
# ? LÓGICA DE LA RED NEURONAL (AHORA ENCAPSULADA)
# ====================================================

def vectorizar(frase):
    """Convierte una frase en un vector binario basado en el vocabulario global."""
    if not vocabulario:
         # Esto debería evitar un crash si el vocabulario está vacío
        return np.zeros(1) 
        
    vector = np.zeros(len(vocabulario))
    limpia = re.sub(r'[?!-]', '', frase).lower().split()
    
    for i, palabra in enumerate(vocabulario):
        if palabra in limpia:
            vector[i] = 1
    return vector

def sigmoid(x): return 1 / (1 + np.exp(-x))
def sigmoid_deriv(x): return x * (1 - x)

def train_model():
    """
    Entrena la red neuronal. 
    Se llama solo cuando el servidor está en funcionamiento o se fuerza.
    """
    global W1, b1, W2, b2, vocabulario, preguntas_global, respuestas_global
    
    print(">>> Iniciando carga de datos...")
    preguntas_global, respuestas_global = load_training_data_from_db()

    if not preguntas_global:
        print("ADVERTENCIA: Entrenamiento omitido. No hay datos en la DB.")
        return False
    
    print(f"✅ Datos cargados. Preguntas: {len(preguntas_global)}")

    # Crear vocabulario
    todas = " ".join(preguntas_global).split()
    vocabulario = sorted(set(todas))
    print(f"✅ Vocabulario creado con {len(vocabulario)} palabras.")
    
    # Preparar datos
    X = np.array([vectorizar(p) for p in preguntas_global])
    y = np.eye(len(respuestas_global))

    # Inicializar pesos
    np.random.seed(1)
    W1 = np.random.rand(len(vocabulario), 8)
    b1 = np.zeros((1, 8))
    W2 = np.random.rand(8, len(respuestas_global))
    b2 = np.zeros((1, len(respuestas_global)))

    # Bucle de entrenamiento
    for epoch in range(10000): # Reducido temporalmente a 50k para la prueba
        z1 = np.dot(X, W1) + b1
        a1 = sigmoid(z1)
        z2 = np.dot(a1, W2) + b2
        salida = sigmoid(z2)

        error = y - salida
        d2 = error * sigmoid_deriv(salida)
        d1 = np.dot(d2, W2.T) * sigmoid_deriv(a1)

        W2 += np.dot(a1.T, d2) * lr
        b2 += np.sum(d2, axis=0, keepdims=True) * lr
        W1 += np.dot(X.T, d1) * lr
        b1 += np.sum(d1, axis=0, keepdims=True) * lr

    print("✅ Entrenamiento de la IA completado. Modelo activo.")
    return True

def predict_ia(mensaje):
    """Predice la respuesta de la IA para un mensaje dado."""
    if W1 is None or not respuestas_global:
        # Devolver una respuesta de "no entrenado" si los pesos no están inicializados
        return {"probabilidad": 0, "respuesta_mas_probable": "Modelo de IA no inicializado. Usa /train para activarlo."}

    entrada = vectorizar(mensaje)
    entrada = entrada.reshape(1, -1) 
    # ... (resto de la lógica de predicción)
    z1 = np.dot(entrada, W1) + b1
    a1 = sigmoid(z1)
    z2 = np.dot(a1, W2) + b2
    pred = sigmoid(z2)

    indice_max = np.argmax(pred)
    probabilidad = pred.round(3).flatten()[indice_max]

    return {
        "probabilidad": float(probabilidad),
        "respuesta_mas_probable": respuestas_global[indice_max],
        "indice": int(indice_max)
    }

# NO SE LLAMA A TRAIN_MODEL() AQUÍ. EL SERVIDOR DEBE ARRANCAR AHORA.
# ====================================================
# ? LÓGICA DE NEGOCIO MIGRADA DE PHP (index.php)
# ====================================================
# ====================================================
# ? LÓGICA DE NEGOCIO MIGRADA DE PHP (Funciones Auxiliares)
# ====================================================

def normalizar(texto):
    """Normaliza el texto (minúsculas, sin tildes ni puntuación)."""
    texto = texto.lower()
    mapping = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n'}
    for k, v in mapping.items():
        texto = texto.replace(k, v)
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.strip()

def traducir_dias(texto):
    """Traduce abreviaturas de días a nombres completos."""
    dias = {'MI': 'miércoles', 'LV': 'lunes y viernes', 'L': 'lunes', 'M': 'martes', 'MA': 'martes', 'J': 'jueves', 'V': 'viernes', 'S': 'sábado', 'D': 'domingo'}
    dias_ordenados = sorted(dias.items(), key=lambda item: len(item[0]), reverse=True)
    for ab, nom in dias_ordenados:
        texto = re.sub(r'\b' + re.escape(ab) + r'\b', nom, texto, flags=re.IGNORECASE)
    return texto

def sumar_45(hora_str):
    """Suma 45 minutos a una hora dada (ej: '7:00' -> '7:45')."""
    try:
        dt = datetime.strptime(hora_str, '%H:%M')
        dt_fin = dt + timedelta(minutes=45)
        return dt_fin.strftime('%I:%M').lstrip('0')
    except ValueError:
        try:
            dt = datetime.strptime(hora_str, '%I:%M')
            dt_fin = dt + timedelta(minutes=45)
            return dt_fin.strftime('%I:%M').lstrip('0')
        except ValueError:
            return hora_str

def describir_aula(codigoAula):
    """Genera la descripción de la ubicación del aula."""
    codigo = codigoAula.upper().strip()
    match = re.match(r'^([A-E])(\d)(\d{2})$', codigo)
    if not match: return None
    edificio, piso_str, numAula_str = match.groups()
    piso = int(piso_str)
    niveles = {1: 'primer nivel', 2: 'segundo nivel', 3: 'tercer nivel', 4: 'cuarto nivel', 5: 'quinto nivel'}
    nivelTexto = niveles.get(piso, f"nivel {piso}")
    extra = ', parte trasera del edificio' if edificio == 'B' and int(numAula_str) > 23 else ''
    ubicacion = {'A': 'al frente, por la entrada principal','B': 'al fondo del recinto, detrás del edificio A cruzando el área verde','C': 'a la izquierda, por la primera entrada de la Av. Estrella Sadhalá'}
    zona = ubicacion.get(edificio, '')
    return f"edificio {edificio}, {nivelTexto}, aula {numAula_str.zfill(2)} ({zona}){extra}"

def procesar_aulas(aulasString, diasCount):
    """Asegura que haya una lista de aulas para cada día de clase."""
    lista = [a.strip() for a in aulasString.upper().split() if a.strip()]
    resultado = []
    if not lista: return []
    for i in range(diasCount):
        resultado.append(lista[i] if i < len(lista) else lista[-1])
    return resultado

def procesar_horario(horarioStr):
    """Convierte la cadena de horario de la materia en una lista de descripciones de clase."""
    horarioStr = horarioStr.upper().strip()
    detalleHoras = []
    patron = re.compile(r'([A-Z]{1,2})(\d{1,2}:\d{2})(?:,(\d{1,2}:\d{2}))?(?:\s*[aA]\s*(\d{1,2}:\d{2}))?(?:\s*([ap]m))?', re.IGNORECASE)
    matches = patron.findall(horarioStr)
    for h in matches:
        dia, hora1, hora2_coma, hora3_a, periodo = h
        dia = traducir_dias(dia)
        hora1_display = f"{hora1}{' ' + periodo if periodo else ''}"
        if hora3_a:
            hora3_display = f"{hora3_a}{' ' + periodo if periodo else ''}"
            detalleHoras.append(f"{dia} de {hora1_display} a {hora3_display}")
        elif hora2_coma:
            horaFin = sumar_45(hora2_coma)
            horaFin_display = f"{horaFin}{' ' + periodo if periodo else ''}"
            detalleHoras.append(f"{dia} de {hora1_display} a {horaFin_display}")
        else:
            horaFin = sumar_45(hora1)
            horaFin_display = f"{horaFin}{' ' + periodo if periodo else ''}"
            detalleHoras.append(f"{dia} de {hora1_display} a {horaFin_display}")
    return detalleHoras

def parsear_materia(lineaMateria):
    """Extrae los detalles de la materia de una línea de texto."""
    lineaMateria = re.sub(r'^horario\s+', '', lineaMateria, flags=re.IGNORECASE).strip()
    patron = re.compile(
        r'([A-Z]{3}-\d{3}-\d{3})\s+'        # 1. CODIGO
        r'(.+?)\s+'                         # 2. NOMBRE
        r'(\d+)\s+'                         # 3. CREDITOS
        r'([A-Z0-9:,\s]+(?:a\s+\d{1,2}:\d{2})?(?:\s*[ap]m)?)\s*' # 4. HORARIO
        r'\(([^)]+)\)\s*'                   # 5. MODALIDAD
        r'-\s*(.+)',                        # 6. AULAS
        re.IGNORECASE
    )
    match = patron.match(lineaMateria)
    if match:
        return {
            'codigo': match.group(1).upper().strip(),
            'nombre': match.group(2).strip(),
            'creditos': int(match.group(3)),
            'horario': match.group(4).strip(),
            'modalidad': match.group(5).strip().capitalize(),
            'aulas': match.group(6).strip()
        }
    return None

def procesar_materia_completa(data):
    """Procesa los datos parseados para generar descripciones completas."""
    if not data: return None
    detalleHoras = procesar_horario(data['horario'])
    listaAulas = procesar_aulas(data['aulas'], len(detalleHoras))
    descripcionAulas = []
    for i, aula in enumerate(listaAulas):
        desc = describir_aula(aula)
        if desc:
            etiqueta = ""
            if len(listaAulas) > 1:
                etiqueta = "primer día en el " if i == 0 else "segundo día en el "
            descripcionAulas.append(f"{etiqueta}{desc}")
    return {
        'codigo': data['codigo'], 'nombre': data['nombre'], 'creditos': data['creditos'],
        'modalidad': data['modalidad'], 'horarios': detalleHoras, 'ubicaciones': descripcionAulas
    }

def generar_respuesta_horario(mensaje):
    """Intenta procesar una o varias líneas de horario."""
    data = parsear_materia(mensaje)
    materias = []
    if data:
        materiaInfo = procesar_materia_completa(data)
        if materiaInfo: materias.append(materiaInfo)
    else:
        lineas = [linea.strip() for linea in mensaje.split('\n') if linea.strip()]
        for linea in lineas:
            data = parsear_materia(linea)
            if data:
                materiaInfo = procesar_materia_completa(data)
                if materiaInfo: materias.append(materiaInfo)

    if not materias:
        return {"error": True,"respuesta": """
                <div class='p-4 rounded-lg'><h3 class='text-lg font-semibold text-red-700 mb-2'>Error</h3><p class='text-gray-700'>No pude interpretar ningún horario. Verifica el formato.</p><p class='text-sm text-gray-500 mt-2'>Ejemplo: MAT-360-001 CALCULO IV 4 MA8:30,9:15,J7:00,7:45 pm (Presencial) - B109 B105</p></div>"""
        }
    
    html_respuesta = "<div class='space-y-4'>"
    total_creditos = sum(m['creditos'] for m in materias)

    for m in materias:
        horarios_html = f"<p class='mt-2'><strong>Clases:</strong> {', '.join(m['horarios'])}</p>" if m['horarios'] else ""
        ubicaciones_html = f"<p class='mt-1'><strong>Ubicación:</strong> {', '.join(m['ubicaciones'])}</p>" if m['ubicaciones'] else ""
            
        html_respuesta += f"""
            <div class='p-4 rounded-lg border-l-4 border-blue-500'>
                <h3 class='text-lg font-semibold text-blue-700 mb-2'>{m['nombre']}</h3>
                <p class='text-gray-700 leading-relaxed'>
                    <span class='text-sm text-gray-600'>{m['codigo']}</span> • 
                    <span class='text-sm font-medium'>{m['creditos']} créditos</span> • 
                    <span class='text-sm'>{m['modalidad']}</span>
                </p>
                {horarios_html}
                {ubicaciones_html}
            </div>"""

    html_respuesta += "</div>"
    if len(materias) > 1:
        html_respuesta += f"""
            <div class='mt-4 p-3 bg-blue-50 rounded-lg'>
                <p class='text-sm text-blue-800'>
                    <strong>Total:</strong> {len(materias)} materia(s)
                    <strong>Créditos:</strong> {total_creditos}
                </p>
            </div>"""
            
    return {"error": False, "respuesta": html_respuesta}
# ====================================================
# ? SERVIDOR FASTAPI Y ENDPOINT PRINCIPAL
# ====================================================

app = FastAPI()

origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "file://", # NECESARIO si ejecutas tu HTML localmente
    "*" # Permite todos los orígenes (menos seguro, pero fácil para pruebas)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permitir todos los headers
)

class ChatRequest(BaseModel):
    mensaje: str

# ----------------------------------------------------
# ENDPOINT DE DIAGNÓSTICO Y CONTROL DE ENTRENAMIENTO
# ----------------------------------------------------

@app.post("/train")
def run_training():
    """Endpoint para iniciar el entrenamiento del modelo manualmente."""
    success = train_model()
    if success:
        return {"status": "success", "message": "El modelo de IA se ha entrenado y activado correctamente."}
    else:
        return {"status": "error", "message": "Fallo al entrenar: No se encontraron datos en la base de datos."}

# ----------------------------------------------------
# ENDPOINT PRINCIPAL DE CHAT
# ----------------------------------------------------

@app.post("/chat")
def handle_chat(request: ChatRequest):
    # ... (El cuerpo de esta función /chat sigue exactamente igual que antes)
    # 1. Lógica Horario/Credito/Aula
    # 2. Lógica IA (predict_ia)
    # 3. Lógica Similitud DB
    # 4. Fallback

    input_original = request.mensaje
    mensaje_normalizado = normalizar(input_original)

    # 1. Lógica de Intenciones de Alta Confianza (Horario, Crédito, Aula)
    
    # 1.1. Horario
    if re.search(r'(horario|hora|clase)', mensaje_normalizado) and \
       re.search(r'([A-Z]{1,2}\d{1,2}:\d{2})|([A-E]\d{3})', input_original.upper()):
        
        horario_info = generar_respuesta_horario(input_original)
        if not horario_info['error']:
             return {"intencion": "horario", "respuesta": horario_info['respuesta'], "confianza": 1.0}

    # 1.2. Crédito/Costo
    if re.search(r'cuanto|credito|costo\s+creditos|costo\s+credito', mensaje_normalizado):
        match_numero = re.search(r'\b(\d+)\b', mensaje_normalizado)
        numero = int(match_numero.group(1)) if match_numero else 0

        if numero > 0:
            if numero > 33:
                return {"intencion": "credito", "respuesta": "Estoy en entrenamiento, asi que puedo estar errado, pero creo no puedes tomar esa cantidad de créditos por cuatrimestre.", "confianza": 1.0}

            conexion = get_db_connection()
            costo_credito = 350.00
            if conexion:
                cursor = conexion.cursor(dictionary=True)
                cursor.execute("SELECT valor_numerico FROM chatbot_logica WHERE clave='costo_credito'")
                row = cursor.fetchone()
                if row: costo_credito = float(row['valor_numerico'])
                cursor.close()
                conexion.close()
            
            total = costo_credito * numero
            respuesta = (
                f"Si tomas {numero} créditos, el costo total del cuatrimestre sería de RD${total:,.2f} "
                f"con un pago mensual de RD${total / 4:,.2f}, Recuerda esto es solo una estimación, "
                f"puede haber ligeras diferencias (300~500 RD$ adicionales por mes) por cargos de servicios "
                f"colocados por la universidad."
            )
            return {"intencion": "credito", "respuesta": respuesta, "confianza": 1.0}

    # 1.3. Aula/Ubicación
    if re.search(r'donde\s+aula|donde\s+salon|donde\s+ubicacion\s+aula|donde\s+ubicacion\s+salon|como\s+llego', mensaje_normalizado):
        match_aula = re.search(r'([A-E])(\d)(\d{2})', input_original.upper())
        if match_aula:
            codigo_aula = "".join(match_aula.groups())
            desc = describir_aula(codigo_aula)
            respuesta = f" El aula {codigo_aula} está en el {desc}." if desc else f"No tengo información precisa del aula {codigo_aula}."
            return {"intencion": "aula", "respuesta": respuesta, "confianza": 1.0}
        else:
            return {"intencion": "aula", "respuesta": "Por favor, indica el código del aula, por ejemplo: B320 o A105.", "confianza": 1.0}


    # 2. Lógica de la Red Neuronal (IA de Python)
    pred_ia = predict_ia(input_original)
    
    if pred_ia['probabilidad'] > 0.55: # Umbral de confianza
        return {"intencion": "ia_query", "respuesta": pred_ia['respuesta_mas_probable'], "confianza": pred_ia['probabilidad']}
    
    
    # 3. Lógica de Similitud de Texto (Fallback de PHP)
    mayor_similitud = 0
    respuesta_final = ""

    conexion = get_db_connection()
    if conexion:
        cursor = conexion.cursor(dictionary=True)
        sql = """
            SELECT p.texto AS pregunta, r.texto AS respuesta, i.ruta AS imagen
            FROM preguntas p
            JOIN respuestas r ON p.respuesta = r.codigo
            LEFT JOIN imagenes i ON r.imagen = i.codigo
        """
        cursor.execute(sql)
        rows = cursor.fetchall()
        
        from difflib import SequenceMatcher # Usando la librería SequenceMatcher de Python

        for row in rows:
            preg_db = normalizar(row['pregunta'])
            similitud = SequenceMatcher(None, mensaje_normalizado, preg_db).ratio() * 100
            
            if similitud > mayor_similitud:
                mayor_similitud = similitud
                respuesta_final = row['respuesta']
                if row['imagen']:
                    respuesta_final += f"<br><img src='/src/images/{row['imagen']}' width='300'>"
        
        cursor.close()
        conexion.close()
    
    if mayor_similitud >= 55:
        return {"intencion": "similitud_db", "respuesta": respuesta_final, "confianza": mayor_similitud / 100.0}
    
    
    # 4. Fallback final (Guardar para entrenamiento futuro)
    conexion = get_db_connection()
    if conexion:
        cursor = conexion.cursor()
        stmt = "INSERT INTO chatbot_logica (clave, valor_texto, descripcion) VALUES (%s, %s, %s)"
        desc = 'Entrada no reconocida (pendiente de análisis)'
        cursor.execute(stmt, (input_original[:255], input_original, desc))
        conexion.commit()
        cursor.close()
        conexion.close()
        
    return {"intencion": "fallback", "respuesta": "No tengo información sobre eso aún, pero estoy aprendiendo. ¡Intenta reformular tu pregunta! (/≧▽≦)/", "confianza": 0.0}
# ----------------------------------------------------
# Asegúrate de que no haya código ejecutable aquí abajo
# ----------------------------------------------------