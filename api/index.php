<?php

$conexion = new mysqli("localhost", "root", "", "chatbot");
$input = strtolower(trim($_POST['mensaje'] ?? ''));

function normalizar($texto)
{
    $texto = strtolower($texto);
    $texto = str_replace(
        ['á', 'é', 'í', 'ó', 'ú', 'ñ'],
        ['a', 'e', 'i', 'o', 'u', 'n'],
        $texto
    );
    $texto = preg_replace('/[^\w\s]/', '', $texto);
    return trim($texto);
}

$mensaje = normalizar($input);

$intencion = null;

// 1. Horario (Prioridad: debe contener la idea de tiempo o formato de horario)
if (preg_match('/(horario|hora|clase)/', $mensaje) && preg_match('/([A-Z]{1,2}\d{1,2}:\d{2})|([A-E]\d{3})/', $_POST['mensaje'])) {
    $intencion = 'horario';
    // 2. Crédito/Costo
} elseif (preg_match('/cuanto|credito|costo\s+creditos|costo\s+credito/', $mensaje)) {
    $intencion = 'credito';
    // 3. Aula/Ubicación (Sólo si NO es horario)
} elseif (preg_match('/donde\s+aula|donde\s+salon|donde\s+ubicacion\s+aula|donde\s+ubicacion\s+salon/', $mensaje)) {
    $intencion = 'aula';
}

preg_match('/\b(\d+)\b/', $mensaje, $match);
$numero = isset($match[1]) ? intval($match[1]) : 0;

if ($intencion === 'credito' && $numero > 0) {

    if ($numero > 33) {
        echo "Estoy en entrenamiento, asi que puedo estar errado, pero creo no puedes tomar esa cantidad de créditos por cuatrimestre.";
        exit;
    }

    $q = $conexion->query("SELECT valor_numerico FROM chatbot_logica WHERE clave='costo_credito'");
    $costo_credito = $q->fetch_assoc()['valor_numerico'];
    $total = $costo_credito * $numero;
    echo "Si tomas $numero créditos, el costo total del cuatrimestre sería de RD$" . number_format($total, 2) . " con un pago mensual de RD$" . number_format($total / 4, 2) . ", Recuerda esto es solo una estimación, puede haber ligeras diferencias (300~500 RD$ adicionales por mes) por cargos de servicios colocados por la universidad.";
    exit;
}

if ($intencion === 'aula') {

    if (preg_match('/([A-E])(\d)(\d{2})/', strtoupper($mensaje), $coincidencias)) {
        $edificio = $coincidencias[1];
        $piso = intval($coincidencias[2]);
        $numAula = intval($coincidencias[3]);

        function describirAula($codigoAula)
        {
            $codigo = strtoupper(trim($codigoAula));

            if (!preg_match('/^([A-D])(\d)(\d{2})$/', $codigo, $m)) {
                return false;
            }

            $edificio = $m[1];
            $piso = intval($m[2]);
            $numAula = intval($m[3]);

            $niveles = [
                1 => 'primer nivel',
                2 => 'segundo nivel',
                3 => 'tercer nivel',
                4 => 'cuarto nivel',
                5 => 'quinto nivel'
            ];

            $nivelTexto = $niveles[$piso] ?? "nivel $piso";

            $extra = '';
            if ($edificio == 'B' && $numAula > 23) {
                $extra = ", parte trasera del edificio";
            }

            // descripción de edificios
            $ubicacion = [
                'A' => 'al frente, por la entrada principal',
                'B' => 'al fondo del recinto, detrás del edificio A cruzando el área verde',
                'C' => 'a la izquierda, por la primera entrada de la Av. Estrella Sadhalá'
            ];

            $zona = $ubicacion[$edificio] ?? '';

            return "edificio {$edificio}, {$nivelTexto}, aula " . str_pad($numAula, 2, '0', STR_PAD_LEFT) . " ({$zona})" . $extra;
        }

        $a = describirAula($edificio . $piso . $numAula);


        if ($a) {
            echo " El aula {$edificio}{$piso}{$numAula} está en el {$a}.";
        } else {
            echo "No tengo información precisa del aula {$edificio}{$piso}{$numAula}, pero parece ser del edificio {$edificio} en el piso {$piso}.";
        }
    } else {
        echo "Por favor, indica el código del aula, por ejemplo: B320 o A105.";
    }

    exit;
}
if ($intencion === 'horario') {

    function describirAula($codigoAula)
    {
        $codigo = strtoupper(trim($codigoAula));
        if (!preg_match('/^([A-E])(\d)(\d{2})$/', $codigo, $m)) return false;

        $edificio = $m[1];
        $piso = intval($m[2]);
        $numAula = intval($m[3]);

        $niveles = [1 => 'primer nivel', 2 => 'segundo nivel', 3 => 'tercer nivel', 4 => 'cuarto nivel', 5 => 'quinto nivel'];
        $nivelTexto = $niveles[$piso] ?? "nivel $piso";

        $extra = ($edificio == 'B' && $numAula > 25) ? ", parte posterior del edificio" : '';

        $ubicacion = [
            'A' => 'al frente, por la entrada principal',
            'B' => 'al fondo del recinto, detrás del edificio A cruzando el área verde',
            'C' => 'a la izquierda, por la primera entrada de la Av. Estrella Sadhalá'
        ];
        $zona = $ubicacion[$edificio] ?? '';

        return "edificio {$edificio}, {$nivelTexto}, aula " . str_pad($numAula, 2, '0', STR_PAD_LEFT) . " ({$zona}){$extra}";
    }

    function traducirDias($texto)
    {
        $dias = ['MI' => 'miércoles', 'LV' => 'lunes y viernes', 'L' => 'lunes', 'M' => 'martes', 'MA' => 'martes', 'J' => 'jueves', 'V' => 'viernes', 'S' => 'sábado', 'D' => 'domingo'];
        uksort($dias, fn($a, $b) => strlen($b) - strlen($a));
        foreach ($dias as $ab => $nom) $texto = preg_replace("/\b$ab\b/iu", $nom, $texto);
        return $texto;
    }

    function sumar45($hora)
    {
        $dt = DateTime::createFromFormat('g:i', $hora);
        if ($dt) $dt->modify('+45 minutes');
        return $dt ? $dt->format('g:i') : $hora;
    }

    function procesarHorario($horarioStr)
    {
        $horarioStr = strtoupper(trim($horarioStr));
        $detalleHoras = [];

        // Patrón para capturar: DIA(S)HORA:MIN,HORA:MIN o DIA(S)HORA:MIN a HORA:MIN
        preg_match_all('/([A-Z]{1,2})(\d{1,2}:\d{2})(?:,(\d{1,2}:\d{2}))?(?:\s*[aA]\s*(\d{1,2}:\d{2}))?(?:\s*([ap]m))?/iu', $horarioStr, $matches, PREG_SET_ORDER);

        foreach ($matches as $h) {
            $dia = traducirDias($h[1]);
            $hora1 = $h[2];
            $hora2 = $h[3] ?? null;
            $hora3 = $h[4] ?? null;
            $periodo = $h[5] ?? '';

            // Agregar am/pm si existe
            $hora1_display = $hora1 . ($periodo ? " $periodo" : '');

            if ($hora3) {
                // Formato: 7:00 a 10:00
                $hora3_display = $hora3 . ($periodo ? " $periodo" : '');
                $detalleHoras[] = "$dia de $hora1_display a $hora3_display";
            } elseif ($hora2) {
                // Formato: 5:30,6:15 (significa 45 min después de 6:15)
                $horaFin = sumar45($hora2);
                $horaFin_display = $horaFin . ($periodo ? " $periodo" : '');
                $detalleHoras[] = "$dia de $hora1_display a $horaFin_display";
            } else {
                // Solo una hora, asumimos 45 min
                $horaFin = sumar45($hora1);
                $horaFin_display = $horaFin . ($periodo ? " $periodo" : '');
                $detalleHoras[] = "$dia de $hora1_display a $horaFin_display";
            }
        }

        return $detalleHoras;
    }

    function procesarAulas($aulasString, $diasCount)
    {
        $lista = array_filter(array_map('trim', explode(' ', strtoupper($aulasString))));
        $resultado = [];

        if (count($lista) == 0) return [];

        for ($i = 0; $i < $diasCount; $i++) {
            $resultado[] = $lista[$i] ?? $lista[count($lista) - 1];
        }

        return $resultado;
    }

    function parsearMateria($lineaMateria)
    {
        // Limpiar la línea removiendo palabras como "horario" o "Horario" al inicio
        $lineaMateria = preg_replace('/^horario\s+/iu', '', trim($lineaMateria));

        // Patrón mejorado para capturar toda la línea
        // Formato: CODIGO NOMBRE CREDITOS HORARIO (MODALIDAD) - AULAS
        $patron = '/([A-Z]{3}-\d{3}-\d{3})\s+(.+?)\s+(\d+)\s+([A-Z0-9:,\s]+(?:a\s+\d{1,2}:\d{2})?(?:\s*[ap]m)?)\s*\(([^)]+)\)\s*-\s*(.+)/iu';

        if (preg_match($patron, $lineaMateria, $m)) {
            return [
                'codigo' => strtoupper(trim($m[1])),
                'nombre' => trim($m[2]),
                'creditos' => intval($m[3]),
                'horario' => trim($m[4]),
                'modalidad' => ucfirst(strtolower(trim($m[5]))),
                'aulas' => trim($m[6])
            ];
        }

        return null;
    }

    function procesarMateria($data)
    {
        if (!$data) return null;

        $detalleHoras = procesarHorario($data['horario']);
        $listaAulas = procesarAulas($data['aulas'], count($detalleHoras));

        $descripcionAulas = [];
        foreach ($listaAulas as $i => $aula) {
            $desc = describirAula($aula);
            if ($desc) {
                $etiqueta = count($listaAulas) > 1 ? ($i == 0 ? "primer día" : "segundo día") : "";
                $descripcionAulas[] = ($etiqueta ? "$etiqueta en el " : "") . $desc;
            }
        }

        return [
            'codigo' => $data['codigo'],
            'nombre' => $data['nombre'],
            'creditos' => $data['creditos'],
            'modalidad' => $data['modalidad'],
            'horarios' => $detalleHoras,
            'ubicaciones' => $descripcionAulas
        ];
    }

    // Procesar el mensaje
    // Primero intentar procesar como una sola línea
    $mensajeLimpio = preg_replace('/\s+/', ' ', trim($_POST['mensaje']));
    $data = parsearMateria($mensajeLimpio);

    $materias = [];

    if ($data) {
        // Si se parsea como una línea, procesar
        $materiaInfo = procesarMateria($data);
        if ($materiaInfo) {
            $materias[] = $materiaInfo;
        }
    } else {
        // Si no, intentar línea por línea
        $lineas = array_filter(array_map('trim', explode("\n", $mensaje)));

        foreach ($lineas as $linea) {
            $data = parsearMateria($linea);
            if ($data) {
                $materiaInfo = procesarMateria($data);
                if ($materiaInfo) {
                    $materias[] = $materiaInfo;
                }
            }
        }
    }

    // Mostrar resultados
    if (empty($materias)) {
        echo "<div class='p-4rounded-lg'>
                <h3 class='text-lg font-semibold text-red-700 mb-2'>Error</h3>
                <p class='text-gray-700'>No pude interpretar ningún horario. Verifica el formato.</p>
                <p class='text-sm text-gray-500 mt-2'>Ejemplo: MAT-360-001 CALCULO IV 4 MA8:30,9:15,J7:00,7:45 pm (Presencial) - B109 B105</p>
              </div>";
    } else {
        echo "<div class='space-y-4'>";

        foreach ($materias as $m) {
            echo "<div class='p-4 rounded-lg border-l-4 border-blue-500'>
                    <h3 class='text-lg font-semibold text-blue-700 mb-2'>{$m['nombre']}</h3>
                    <p class='text-gray-700 leading-relaxed'>
                        <span class='text-sm text-gray-600'>{$m['codigo']}</span> • 
                        <span class='text-sm font-medium'>{$m['creditos']} créditos</span> • 
                        <span class='text-sm'>{$m['modalidad']}</span>
                    </p>";

            if (!empty($m['horarios'])) {
                echo "<p class='mt-2'><strong>Clases:</strong> " . implode(', ', $m['horarios']) . "</p>";
            }

            if (!empty($m['ubicaciones'])) {
                echo "<p class='mt-1'><strong>Ubicación:</strong> " . implode(', ', $m['ubicaciones']) . "</p>";
            }

            echo "</div>";
        }

        echo "</div>";

        // Resumen
        echo count($materias) > 1 ? "<div class='mt-4 p-3 bg-blue-50 rounded-lg'>
                <p class='text-sm text-blue-800'>
                    " . (count($materias) > 1 ? "<strong>Total:</strong> " . count($materias) . " materia(s)" : '') . "
                    <strong>Créditos:</strong> " . array_sum(array_column($materias, 'creditos')) . "
                </p>
              </div>" : '';
    }

    exit;
}

$sql = "SELECT p.texto AS pregunta, r.texto AS respuesta, i.ruta AS imagen
        FROM preguntas p
        JOIN respuestas r ON p.respuesta = r.codigo
        LEFT JOIN imagenes i ON r.imagen = i.codigo";
$res = $conexion->query($sql);

$mayor_similitud = 0;
$respuesta_final = "";

while ($row = $res->fetch_assoc()) {
    $preg_db = normalizar($row['pregunta']);
    similar_text($mensaje, $preg_db, $porcentaje);
    if ($porcentaje > $mayor_similitud) {
        $mayor_similitud = $porcentaje;
        $respuesta_final = $row['respuesta'];
        if ($row['imagen']) {
            $respuesta_final .= "<br><img src='/src/images/" . $row['imagen'] . "' width='300'>";
        }
    }
}

if ($mayor_similitud >= 55) {
    echo $respuesta_final;
} else {
    //  Si no hay buena coincidencia, guardar para entrenamiento futuro
    $stmt = $conexion->prepare("INSERT INTO chatbot_logica (clave, valor_texto, descripcion) VALUES (?, ?, ?)");
    $desc = 'Entrada no reconocida (pendiente de análisis)';
    $stmt->bind_param("sss", $mensaje, $mensaje, $desc);
    $stmt->execute();
    echo "No tengo información sobre eso aún, pero estoy aprendiendo. ¡Intenta reformular tu pregunta! (/≧▽≦)/";
}
