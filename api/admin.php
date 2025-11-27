<?php
$conexion = new mysqli("localhost", "root", "", "chatbot");
$conexion->set_charset("utf8");

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['agregar_manual'])) {
        $frase = trim($_POST['frase']);
        $respuesta_texto = trim($_POST['respuesta_texto']);

        if ($frase && $respuesta_texto) {
            $stmt = $conexion->prepare("INSERT INTO respuestas (texto) VALUES (?)");
            $stmt->bind_param("s", $respuesta_texto);
            $stmt->execute();
            $respuesta_id = $conexion->insert_id;

            $stmt = $conexion->prepare("INSERT INTO preguntas (texto, respuesta) VALUES (?, ?)");
            $stmt->bind_param("si", $frase, $respuesta_id);
            $stmt->execute();

            $mensaje = "<div class='bg-green-100 text-green-800 px-4 py-2 rounded-lg mb-4'>Nueva pregunta y respuesta añadidas exitosamente.</div>";
        }
    }

    if (isset($_POST['asignar'])) {
        $frase = $_POST['frase'];
        $respuesta_id = intval($_POST['respuesta_id']);
        $stmt = $conexion->prepare("INSERT IGNORE INTO preguntas (texto, respuesta) VALUES (?, ?)");
        $stmt->bind_param("si", $frase, $respuesta_id);
        $stmt->execute();

        $conexion->query("UPDATE chatbot_logica SET descripcion='procesada' WHERE valor_texto='$frase'");
        $mensaje = "<div class='bg-green-100 text-green-800 px-4 py-2 rounded-lg mb-4'>Frase asignada correctamente.</div>";
    }

    // Crear nueva respuesta para una frase pendiente
    if (isset($_POST['nueva'])) {
        $frase = $_POST['frase'];
        $respuesta_texto = $_POST['respuesta_texto'];

        $stmt = $conexion->prepare("INSERT INTO respuestas (texto) VALUES (?)");
        $stmt->bind_param("s", $respuesta_texto);
        $stmt->execute();
        $respuesta_id = $conexion->insert_id;

        $stmt = $conexion->prepare("INSERT INTO preguntas (texto, respuesta) VALUES (?, ?)");
        $stmt->bind_param("si", $frase, $respuesta_id);
        $stmt->execute();

        $conexion->query("UPDATE chatbot_logica SET descripcion='procesada' WHERE valor_texto='$frase'");
        $mensaje = "<div class='bg-blue-100 text-blue-800 px-4 py-2 rounded-lg mb-4'>Nueva respuesta añadida y asociada.</div>";
    }
}
?>

<!DOCTYPE html>
<html lang="es">

<head>
    <meta charset="UTF-8">
    <title>Chatbot</title>
    <link rel="stylesheet" href="../public/css/style.css">
</head>

<body class="bg-gray-100 min-h-screen">

    <div class="max-w-5xl mx-auto py-10 px-4">
        <h1 class="text-3xl font-bold text-center text-blue-700 mb-8">Panel de Entrenamiento para el Chatbot UTESA</h1>

        <?php if (isset($mensaje)) echo $mensaje; ?>

        <!-- Sección para agregar manualmente -->
        <div class="bg-white shadow-md rounded-lg p-6 mb-10">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Agregar nueva pregunta y respuesta</h2>
            <form method="POST" class="space-y-3">
                <input type="text" name="frase" placeholder="Ej: ¿Cómo veo mi pensum?" class="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring focus:ring-blue-300">
                <textarea name="respuesta_texto" rows="3" placeholder="Respuesta del chatbot..." class="w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring focus:ring-blue-300"></textarea>
                <button type="submit" name="agregar_manual" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition">
                    Agregar pregunta
                </button>
            </form>
        </div>

        <div class="bg-white shadow-md rounded-lg p-6">
            <h2 class="text-xl font-semibold text-gray-700 mb-4">Frases pendientes por procesar</h2>

            <?php
            $sql = "SELECT id, valor_texto FROM chatbot_logica WHERE descripcion LIKE '%pendiente%'";
            $result = $conexion->query($sql);

            if ($result->num_rows === 0) {
                echo "<p class='text-gray-600'>No hay frases pendientes por analizar.</p>";
            } else {
                while ($row = $result->fetch_assoc()) {
                    $frase = htmlspecialchars($row['valor_texto']);
                    echo "<div class='border border-gray-300 rounded-lg p-4 mb-4 bg-gray-50'>";
                    echo "<p class='font-semibold text-gray-800 mb-2'>Frase detectada: <span class='text-blue-700'>$frase</span></p>";

                    echo "<form method='POST' class='space-y-2 mb-3'>
                    <input type='hidden' name='frase' value='$frase'>
                    <label class='block text-sm text-gray-600 mb-1'>Asignar a respuesta existente:</label>
                    <select name='respuesta_id' class='w-full border border-gray-300 rounded-md p-2'>
                ";

                    $resps = $conexion->query("SELECT codigo, texto FROM respuestas ORDER BY codigo DESC");
                    while ($r = $resps->fetch_assoc()) {
                        $texto_corto = mb_substr($r['texto'], 0, 60);
                        echo "<option value='{$r['codigo']}'>{$r['codigo']} - {$texto_corto}</option>";
                    }

                    echo "</select>
                    <button type='submit' name='asignar' class='bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md transition'>
                        Asignar
                    </button>
                </form>";

                    // Formulario 2: Crear nueva respuesta
                    echo "<form method='POST' class='space-y-2'>
                    <input type='hidden' name='frase' value='$frase'>
                    <label class='block text-sm text-gray-600 mb-1'>Crear nueva respuesta:</label>
                    <textarea name='respuesta_texto' rows='2' class='w-full border border-gray-300 rounded-md p-2 focus:outline-none focus:ring focus:ring-blue-300' placeholder='Escribe la respuesta...'></textarea>
                    <button type='submit' name='nueva' class='bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-md transition'>
                        Crear Respuesta
                    </button>
                </form>";

                    echo "</div>";
                }
            }
            ?>
        </div>
    </div>

</body>

</html>