const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");

function agregarMensaje(texto, tipo) {
    const msg = document.createElement("div");
    msg.classList.add("flex", "items-start", "space-x-2");
    msg.innerHTML =
        tipo === "user"
            ? `<div class="ml-auto bg-green-600 text-white rounded-lg rounded-br-0 px-3 py-2 max-w-[80%] text-sm">${texto}</div>`
            : `<div class="bg-gray-100 text-gray-800 rounded-lg rounded-tl-0 px-3 py-2 max-w-[80%] text-sm shadow">${texto}</div>`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function enviarMensaje() {
    // 1. Obtener y validar el texto
    const texto = userInput.value.trim();
    if (texto === "") return;

    // 2. Agregar el mensaje del usuario e iniciar el indicador de "Escribiendo..."
    agregarMensaje(texto, "user");
    userInput.value = "";

    const typing = document.createElement("div");
    typing.id = "typing";
    // Nota: El indicador 'typing' debe usar la clase 'message-bubble bot' para que luzca bien
    typing.innerHTML = `
        <div class="message-bubble bot">
            <div class="bg-gray-100 text-gray-500 rounded-lg px-3 py-2 text-sm italic">Escribiendo...</div>
        </div>
    `;
    chatBox.appendChild(typing);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
        const API_URL = "http://127.0.0.1:8000/chat";

        // 3. Realizar la petición POST en formato JSON
        const res = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "mensaje": texto // <-- La clave que espera FastAPI
            }),
        });

        // 4. Verificar la respuesta del servidor
        if (!res.ok) {
            // Manejar errores HTTP (e.g., 404, 500)
            throw new Error(`Error HTTP: ${res.status} - ${res.statusText}`);
        }

        const data = await res.json();
        console.log("Respuesta del Backend:", data);

        // 5. Eliminar el indicador de "Escribiendo..."
        document.getElementById("typing").remove();

        // 6. Agregar la respuesta del bot usando el campo 'respuesta'
        // FastAPI devuelve {intencion, respuesta, confianza}
        agregarMensaje(data.respuesta, "bot");
        
    } catch (error) {
        // 7. Manejar errores de conexión (servidor caído) o de la petición
        const typingIndicator = document.getElementById("typing");
        if (typingIndicator) {
             typingIndicator.remove();
        }
        
        // Mensaje de error más profesional
        agregarMensaje(
            "Error de conexión con el servidor. Por favor, verifica que el proceso Uvicorn esté activo en el puerto 8000.", 
            "bot"
        );
        console.error("Error en la función enviarMensaje:", error);
    }
    
    // Asegurar que el scroll esté siempre abajo al finalizar
    chatBox.scrollTop = chatBox.scrollHeight;
}