# 🧠 OMEGA-AI v3

> Multi-AI orchestrator — pełne spektrum BEZ doładowań

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Funkcje

| Panel | Opis |
|-------|------|
| 💬 Chat | Rozmowy z AI, auto-routing modeli, historia sesji |
| 🎓 Eksperci | 10 specjalistów z dedykowanymi promptami |
| ⚡ Pipeline | Łańcuch ekspertów krok po kroku z syntezą |
| ⚖️ Porównaj | Ta sama wiadomość → wiele modeli równolegle |
| 🔐 Koder | Base64, Hex, Binary, URL, ROT13, Morse — 100% offline |
| 🧠 Pamięć | Notatki, lekcje, błędy — lokalnie w przeglądarce |
| 📊 Metryki | Dashboard — koszty, tokeny, latencja |
| ⚙️ Ustawienia | Klucze API — bezpieczne, lokalne |

## 🤖 Obsługiwane AI (60+ modeli, wszystkie FREE)

### ⚡ Groq (14 400 req/day — bezpłatne)
- Llama 3.3 70B, Llama 3.1 8B/70B/405B
- Gemma 2 9B, Mixtral 8x7B
- DeepSeek R1 Distill, Qwen QwQ 32B
- Llama 3.2 Vision 11B/90B, i więcej...

### 🌟 Google Gemini (1500 req/day — bezpłatne)
- Gemini 2.5 Flash ⭐ (najlepszy free)
- Gemini 2.5 Pro, 2.0 Flash, 1.5 Flash/Pro
- Gemini 2.0 Flash Thinking

### 🔀 OpenRouter (darmowe modele)
- Qwen3 235B, DeepSeek R1 free
- Mistral 7B, Gemma 3, Llama 3.3
- Hermes 3 405B, i 20+ więcej...

### 🖥️ Ollama (100% offline, bez limitu)
- Llama 3.3, Phi-4, Qwen3, Gemma 3
- DeepSeek R1, Mistral, CodeLlama, i więcej

### 🐳 DeepSeek
- DeepSeek Chat, DeepSeek Reasoner

## 🚀 Szybki start

### Frontend (przeglądarka — zero instalacji)
1. Otwórz `frontend/index.html` w przeglądarce
2. Wejdź w ⚙️ Ustawienia
3. Wklej klucze API:
   - **Groq**: [console.groq.com](https://console.groq.com) — FREE
   - **Gemini**: [aistudio.google.com](https://aistudio.google.com/app/apikey) — FREE
   - **OpenRouter**: [openrouter.ai/keys](https://openrouter.ai/keys) — FREE modele
   - **Ollama**: zainstaluj lokalnie [ollama.ai](https://ollama.ai) — offline

### Backend Python
```bash
pip install httpx

# Chat
python backend/omega.py chat '{"api_keys":{"groq":"YOUR_KEY"}, "message":"Cześć!"}'

# Lista modeli
python backend/omega.py list_models
```

## 📁 Struktura

```
omega-ai/
├── frontend/
│   └── index.html      # Cała aplikacja (single-file, React CDN)
├── backend/
│   ├── omega.py        # Główny orchestrator AI
│   └── modules/
│       └── decoder.py  # Koder/dekoder (Base64, Hex, etc.)
└── README.md
```

## 🔑 Klucze API (wszystkie FREE)

| Provider | Dzienny limit | Link |
|----------|--------------|------|
| Groq | 14 400 req | [console.groq.com](https://console.groq.com) |
| Google Gemini | 1 500 req | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| OpenRouter | free modele | [openrouter.ai](https://openrouter.ai/keys) |
| Ollama | ∞ offline | [ollama.ai](https://ollama.ai) |

## 📜 Licencja

MIT © Jezior91
