# External AI Image Worker (Windows)

This folder contains the standalone Windows client for FjordLens external AI image descriptions.

## Files

- `ai_billedbeskriver.py`: core image analysis script (CLI)
- `ai_billedbeskriver_gui.pyw`: GUI client that can process one image or run the external queue
- `Start AI Billedbeskriver.vbs`: helper launcher that starts the GUI without a console window
- `requirements.txt`: Python dependencies for this worker


## Prerequisites

1. Windows med Python 3.10+ installeret
2. [Ollama](https://ollama.com/download) installeret og kørende lokalt
3. Qwen vision-model installeret i Ollama (`qwen2.5vl:7b`)
4. Ekstern AI-beskrivelse aktiveret i FjordLens-indstillinger

### Sådan installerer du Ollama og Qwen-modellen

1. **Installer Ollama**
	- Download og installer Ollama fra: [https://ollama.com/download](https://ollama.com/download)
	- Start Ollama (genstart evt. computeren efter installation)

2. **Installer Qwen-modellen**
	- Åbn PowerShell og kør:
	  ```powershell
	  ollama pull qwen2.5vl:7b
	  ```
	- Se flere modeller her: [https://ollama.com/library](https://ollama.com/library)

3. **Start Ollama** (hvis ikke allerede kørende):
	- Kør i PowerShell:
	  ```powershell
	  ollama serve
	  ```

4. **Test at Ollama virker**
	- Kør f.eks.:
	  ```powershell
	  ollama list
	  ```
	- Du bør se `qwen2.5vl:7b` på listen.


## Setup

Åbn PowerShell i denne mappe og kør:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```


## Brug

### GUI-tilstand

- Dobbeltklik på `Start AI Billedbeskriver.vbs`, eller
- Kør `pythonw.exe .\ai_billedbeskriver_gui.pyw`

I GUI'en:

1. Indsæt dit FjordLens-forbindelseslink
2. Klik på `Kør ekstern kø`
3. Lad programmet være åbent, mens den behandler køen

### CLI-tilstand (enkelt billede)

```powershell
python .\ai_billedbeskriver.py "C:\sti\til\billede.jpg"
```


## Miljøvariabler

- `OLLAMA_HOST` (default: `http://localhost:11434`)
- `OLLAMA_VISION_MODEL` (default: `qwen2.5vl:7b`)

Eksempel:

```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_VISION_MODEL = "qwen2.5vl:7b"
pythonw.exe .\ai_billedbeskriver_gui.pyw
```
