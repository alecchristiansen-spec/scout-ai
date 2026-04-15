# Scout

Scout is a starter AI website for college students. It lets users:
- ask questions,
- upload a screenshot,
- choose a response style,
- and optionally turn on live web research.

## Why this is different from plain chat
Scout is opinionated around one workflow: helping students understand tech issues and everyday questions faster. Instead of a blank chat box, it includes:
- screenshot analysis,
- response modes,
- research toggle,
- simple UI copy for students.

## Tech stack
- Flask backend
- Vanilla HTML/CSS/JS frontend
- OpenAI Responses API

## 1) Create a virtual environment
### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies
```bash
pip install -r requirements.txt
```

## 3) Add your API key
Copy `.env.example` to `.env` and add your real key.

### Windows PowerShell
```powershell
Copy-Item .env.example .env
```

### macOS / Linux
```bash
cp .env.example .env
```

## 4) Run the app
```bash
python app.py
```

Then open:
```text
http://127.0.0.1:5000
```

## Suggested next features
### Version 1.1
- markdown rendering in answers
- saved chat history
- branded logo and landing page sections

### Version 1.2
- file upload and retrieval for class notes
- user accounts
- usage limits

### Version 2.0
- live voice with Realtime API
- file search over uploaded documents
- “study mode” and “career mode”
- subscription billing

## Important notes
- Keep your API key on the server only.
- This starter app uses the Responses API, which supports text/image input and built-in tools like web search.
- If you enable research, answers can include up-to-date web-grounded info.

## Pricing thought
Start with this as a personal prototype. Use it yourself, show friends, then narrow the niche further.
