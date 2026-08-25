# RebirthBot

Bot de Discord desenvolupat amb Python i `discord.py`.

Aquest document explica com instal·lar i executar el bot des de Windows utilitzant Visual Studio Code.

---

# 📋 Requisits

Abans de començar necessites:

* Windows
* Python instal·lat
* Visual Studio Code
* El projecte RebirthBot
* El token del bot de Discord

No cal instal·lar SQLite, `asyncio`, `re`, `random` ni altres llibreries estàndard de Python.

---

# 1. Instal·lar Python

Descarrega Python des de la pàgina oficial:

https://www.python.org/downloads/

Durant la instal·lació és **MOLT IMPORTANT** activar aquesta opció:

```text
☑ Add Python.exe to PATH
```

Després continua amb la instal·lació normal.

Per comprovar que Python funciona, obre una terminal i escriu:

```powershell
py --version
```

Si apareix una versió de Python, està instal·lat correctament.

---

# 2. Instal·lar Visual Studio Code

Descarrega Visual Studio Code:

https://code.visualstudio.com/

Instal·la'l amb les opcions predeterminades.

Quan estigui instal·lat, obre Visual Studio Code.

---

# 3. Obrir el projecte

Descarrega o clona aquest repositori:

https://github.com/fustcoma/RebirthBot

A Visual Studio Code ves a:

```text
File → Open Folder...
```

i selecciona la carpeta:

```text
RebirthBot
```

És important obrir **la carpeta principal del projecte**, no una carpeta de dins.

Hauries de veure una estructura semblant a:

```text
RebirthBot/
│
├── commands/
├── database/
├── events/
├── utils/
│
├── bot.py
├── config.json
├── requirements.txt
├── READ.me
└── .gitignore
```

---

# 4. Obrir la terminal de VS Code

No cal obrir PowerShell manualment fora de VS Code.

A Visual Studio Code ves a:

```text
Terminal → New Terminal
```

També pots utilitzar:

```text
Ctrl + Shift + `
```

La terminal apareixerà a la part inferior de VS Code.

Comprova que estàs dins de la carpeta del projecte.

Per exemple:

```text
PS E:\Documents\DiscordBot>
```

Si no estàs dins de `RebirthBot`, pots entrar-hi amb:

```powershell
cd RebirthBot
```

---

# 5. Crear l'entorn virtual

És recomanable utilitzar un entorn virtual perquè les llibreries del bot no interfereixin amb les altres instal·lacions de Python.

A la terminal de VS Code executa:

```powershell
py -m venv venv
```

Això crearà:

```text
RebirthBot/
└── venv/
```

La carpeta `venv` **no s'ha de pujar a GitHub**.

El `.gitignore` del projecte ja està preparat perquè Git l'ignori.

---

# 6. Activar l'entorn virtual

A la terminal de VS Code executa:

```powershell
.\venv\Scripts\activate
```

Si s'ha activat correctament, al principi de la terminal apareixerà alguna cosa semblant a:

```text
(venv) PS E:\Documents\DiscordBot>
```

El `(venv)` indica que l'entorn virtual està actiu.

---

# 7. Instal·lar els requirements

Amb `(venv)` activat, executa:

```powershell
py -m pip install -r requirements.txt
```

Aquesta comanda instal·larà automàticament totes les llibreries necessàries per al bot.

No cal instal·lar `discord.py` ni `python-dotenv` manualment.

Si vols actualitzar `pip` abans:

```powershell
py -m pip install --upgrade pip
```

i després:

```powershell
py -m pip install -r requirements.txt
```

---

# 8. Configurar el token del bot

El bot utilitza una variable d'entorn anomenada:

```text
DISCORD_TOKEN
```

El token **NO s'ha de posar directament dins de `bot.py`**.

Crea un fitxer anomenat:

```text
.env
```

a la carpeta principal del projecte:

```text
RebirthBot/
│
├── commands/
├── database/
├── events/
├── utils/
│
├── .env
├── bot.py
├── config.json
└── requirements.txt
```

Dins de `.env` posa:

```env
DISCORD_TOKEN=EL_TEU_TOKEN_AQUI
```

Substitueix `EL_TEU_TOKEN_AQUI` pel token real del bot.

**No comparteixis mai aquest fitxer ni el pugis a GitHub.**

El projecte ja té `.env` dins del `.gitignore`.

---

# 9. Configurar el bot de Discord

Has de crear el bot des del Discord Developer Portal:

https://discord.com/developers/applications

Crea una aplicació nova i afegeix-hi un bot.

A la configuració del bot activa els intents necessaris.

Com que RebirthBot utilitza:

```python
intents.message_content = True
intents.members = True
```

has d'activar els intents corresponents al Developer Portal.

Especialment:

```text
MESSAGE CONTENT INTENT
SERVER MEMBERS INTENT
```

---

# 10. Executar el bot

Una vegada:

* Python està instal·lat
* VS Code està instal·lat
* el projecte està obert
* l'entorn `venv` està activat
* els requirements estan instal·lats
* `.env` està configurat

només cal executar:

```powershell
py bot.py
```

Això és tot.

No cal executar cap comanda complicada.

---

# 11. Fer que `venv` s'activi automàticament a VS Code

Per no haver d'escriure cada vegada:

```powershell
.\venv\Scripts\activate
```

VS Code pot seleccionar automàticament l'entorn virtual.

Prem:

```text
Ctrl + Shift + P
```

Busca:

```text
Python: Select Interpreter
```

i selecciona:

```text
.\venv\Scripts\python.exe
```

Després tanca la terminal actual i obre:

```text
Terminal → New Terminal
```

VS Code normalment activarà automàticament:

```text
(venv)
```

A partir d'aquest moment, quan obris el projecte a VS Code i una terminal nova s'activi correctament, només hauràs de fer:

```powershell
py bot.py
```

---

# 12. Aturar el bot

Per aturar el bot des de la terminal:

```text
Ctrl + C
```

El bot es desconnectarà de Discord.

---

# 13. Tornar a iniciar-lo un altre dia

Obre el projecte `RebirthBot` amb VS Code.

Obre:

```text
Terminal → New Terminal
```

Si apareix:

```text
(venv)
```

simplement executa:

```powershell
py bot.py
```

Si no apareix `(venv)`, activa'l amb:

```powershell
.\venv\Scripts\activate
```

i després:

```powershell
py bot.py
```

---

# ⚠️ Errors habituals

## `py` no es reconeix

Python probablement no està instal·lat correctament o no s'ha afegit al PATH.

Comprova:

```powershell
py --version
```

Si no funciona, torna a instal·lar Python i activa:

```text
Add Python.exe to PATH
```

---

## `No module named discord`

No s'han instal·lat els requirements o no està activat el `venv`.

Executa:

```powershell
.\venv\Scripts\activate
```

i:

```powershell
py -m pip install -r requirements.txt
```

---

## `No module named dotenv`

Executa:

```powershell
py -m pip install -r requirements.txt
```

---

## El bot no inicia perquè falta el token

Comprova que existeix:

```text
.env
```

i que conté:

```env
DISCORD_TOKEN=EL_TEU_TOKEN
```

No posis cometes i no deixis espais al voltant de `=`.

---

## El bot es connecta però no funcionen alguns comandos

Comprova que els intents necessaris estan activats al Discord Developer Portal i que el bot té els permisos necessaris al servidor.

---

# 🚀 Resum ràpid

Una vegada instal·lat i configurat tot, el funcionament habitual és simplement:

```powershell
# Obrir el projecte amb VS Code

# Obrir:
Terminal → New Terminal

# Si apareix (venv):
py bot.py
```

I el bot començarà a funcionar.

---

# 🔒 Important

**No pugis mai a GitHub:**

```text
.env
venv/
```

El `.gitignore` del projecte ja està configurat per ignorar aquests fitxers i carpetes.

Especialment, **mai comparteixis el token del bot**.

Si el token es fa públic accidentalment, genera'n un de nou immediatament des del Discord Developer Portal.
