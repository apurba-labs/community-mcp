const messages = document.getElementById("messages");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const language = document.getElementById("language");
const notice = document.getElementById("notice");
const micButton = document.getElementById("micButton");

let sessionId = crypto.randomUUID();
let busy = false;

function addMessage(role, text, trace = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  if (role === "assistant") {
    const meta = document.createElement("div");
    meta.className = "trace";

    if (trace?.tool) {
      const label = document.createElement("strong");
      label.textContent = `MCP tool: ${trace.tool}`;
      meta.appendChild(label);
    } else {
      meta.textContent = "No MCP tool called";
    }

    if ("speechSynthesis" in window) {
      const speak = document.createElement("button");
      speak.className = "speak-button";
      speak.textContent = "🔊 Listen";
      speak.addEventListener("click", () => {
        speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language.value === "bn" ? "bn-BD" : "en-US";
        speechSynthesis.speak(utterance);
      });
      meta.appendChild(speak);
    }

    wrapper.appendChild(meta);
  }

  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
}

async function sendMessage(text) {
  if (busy || !text.trim()) return;

  busy = true;
  sendButton.disabled = true;
  notice.textContent = "";

  const welcome = messages.querySelector(".welcome");
  if (welcome) welcome.remove();

  addMessage("user", text);
  input.value = "";

  try {
    const response = await fetch("/simulator/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: text,
        locale: language.value,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      if (response.status === 429) {
        throw new Error("Too many requests. Please wait a minute.");
      }
      throw new Error("The assistant is temporarily unavailable.");
    }

    const result = await response.json();
    sessionId = result.session_id;
    addMessage("assistant", result.message, result.trace);
  } catch (error) {
    notice.textContent = error.message;
    addMessage("assistant", "I couldn't complete that request. Please try again.");
  } finally {
    busy = false;
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.question));
});

document.getElementById("newChat").addEventListener("click", () => {
  sessionId = crypto.randomUUID();
  messages.replaceChildren();
  notice.textContent = "";
  input.value = "";
  input.focus();
});

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  micButton.addEventListener("click", () => {
    const recognition = new SpeechRecognition();
    recognition.lang = language.value === "bn" ? "bn-BD" : "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      input.value = event.results[0][0].transcript;
      input.focus();
    };

    recognition.onerror = () => {
      notice.textContent = "Voice recognition failed. Please type your question.";
    };

    recognition.start();
  });
} else {
  micButton.disabled = true;
  micButton.title = "Voice input is not supported in this browser.";
}
