document.getElementById("chatbot-button").addEventListener("click", function() {
    let chatbot = document.getElementById("chatbot-container");
    chatbot.style.display = chatbot.style.display === "flex" ? "none" : "flex";
});

async function sendMessage() {
    let inputField = document.getElementById("userInput");
    let chatbox = document.getElementById("chatbox");
    let userMessage = inputField.value.trim();
    
    if (!userMessage) return;

    // Display user message
    chatbox.innerHTML += `<div class='message user'>${userMessage}</div>`;
    inputField.value = "";
    chatbox.scrollTop = chatbox.scrollHeight;

    // ✅ Correct Flask API URL
    const API_URL = "https://coffee-rag.onrender.com/ask";

    try {
        let response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: userMessage })
        });

        let data = await response.json();
        chatbox.innerHTML += `<div class='message bot'>${data.response}</div>`;
        chatbox.scrollTop = chatbox.scrollHeight;
    } catch (error) {
        console.error("Error connecting to Flask API:", error);
        chatbox.innerHTML += `<div class='message bot error'>Error: Could not connect to AI server.</div>`;
    }
}

document.getElementById("sendButton").addEventListener("click", sendMessage);
document.getElementById("userInput").addEventListener("keypress", function(event) {
    if (event.key === "Enter") sendMessage();
});

