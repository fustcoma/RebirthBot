# RebirthBot

Bot de Discord desenvolupat amb Python i `discord.py`.

Aquest document explica com instal¡¤lar i executar el bot des de Windows utilitzant Visual Studio Code.

---

# Requisits

Abans de comen?ar necessites:

* Windows
* Python instal¡¤lat
* Visual Studio Code
* El projecte RebirthBot
* El token del bot de Discord

No cal instal¡¤lar SQLite, `asyncio`, `re`, `random` ni altres llibreries est¨¤ndard de Python.

---

# 1. Instal¡¤lar Python

Descarrega Python des de la p¨¤gina oficial:

https://www.python.org/downloads/

Durant la instal¡¤laci¨® ¨¦s **MOLT IMPORTANT** activar aquesta opci¨®:

```text
Add Python.exe to PATH
```

Despr¨¦s continua amb la instal¡¤laci¨® normal.

Per comprovar que Python funciona, obre una terminal i escriu:

```powershell
py --version
```

Si apareix una versi¨® de Python, est¨¤ instal¡¤lat correctament.

---

# 2. Instal¡¤lar Visual Studio Code

Descarrega Visual Studio Code:

https://code.visualstudio.com/

Instal¡¤la'l amb les opcions predeterminades.

Quan estigui instal¡¤lat, obre Visual Studio Code.

---

# 3. Obrir el projecte

Descarrega o clona aquest repositori:

https://github.com/fustcoma/RebirthBot

A Visual Studio Code ves a:

```text
File ¡ú Open Folder...
```

i selecciona la carpeta:

```text
RebirthBot
```

¨¦s important obrir **la carpeta principal del projecte**, no una carpeta de dins.

Hauries de veure una estructura semblant a:

```text
RebirthBot/
©¦
©À©¤©¤ commands/
©À©¤©¤ database/
©À©¤©¤ events/
©À©¤©¤ utils/
©¦
©À©¤©¤ bot.py
©À©¤©¤ config.json
©À©¤©¤ requirements.txt
©À©¤©¤ READ.me
©¸©¤©¤ .gitignore
```

---

# 4. Obrir la terminal de VS Code

No cal obrir PowerShell manualment fora de VS Code.

A Visual Studio Code ves a:

```text
Terminal ¡ú New Terminal
```

Tamb¨¦ pots utilitzar:

```text
Ctrl + Shift + `
```

La terminal apareixer¨¤ a la part inferior de VS Code.

Comprova que est¨¤s dins de la carpeta del projecte.

Per exemple:

```text
PS E:\Documents\DiscordBot>
```

Si no est¨¤s dins de `RebirthBot`, pots entrar-hi amb:

```powershell
cd RebirthBot
```

---

# 5. Crear l'entorn virtual

¨¦s recomanable utilitzar un entorn virtual perqu¨¨ les llibreries del bot no interfereixin amb les altres instal¡¤lacions de Python.

A la terminal de VS Code executa:

```powershell
py -m venv venv
```

Aix¨° crear¨¤:

```text
RebirthBot/
©¸©¤©¤ venv/
```

La carpeta `venv` **no s'ha de pujar a GitHub**.

El `.gitignore` del projecte ja est¨¤ preparat perqu¨¨ Git l'ignori.

---

# 6. Activar l'entorn virtual

A la terminal de VS Code executa:

```powershell
.\venv\Scripts\activate
```

Si s'ha activat correctament, al principi de la terminal apareixer¨¤ alguna cosa semblant a:

```text
(venv) PS E:\Documents\DiscordBot>
```

El `(venv)` indica que l'entorn virtual est¨¤ actiu.

Si et dona error, prova de posar aquesta comanda i probar a fer un altre cop el `venv`
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

# 7. Instal¡¤lar els requirements

Amb `(venv)` activat, executa:

```powershell
py -m pip install -r requirements.txt
```

Aquesta comanda instal¡¤lar¨¤ autom¨¤ticament totes les llibreries necess¨¤ries per al bot.

No cal instal¡¤lar `discord.py` ni `python-dotenv` manualment.

Si vols actualitzar `pip` abans:

```powershell
py -m pip install --upgrade pip
```

i despr¨¦s:

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
©¦
©À©¤©¤ commands/
©À©¤©¤ database/
©À©¤©¤ events/
©À©¤©¤ utils/
©¦
©À©¤©¤ .env
©À©¤©¤ bot.py
©À©¤©¤ config.json
©¸©¤©¤ requirements.txt
```

Dins de `.env` posa:

```env
DISCORD_TOKEN=EL_TEU_TOKEN_AQUI
```

Substitueix `EL_TEU_TOKEN_AQUI` pel token real del bot.

**No comparteixis mai aquest fitxer ni el pugis a GitHub.**

El projecte ja t¨¦ `.env` dins del `.gitignore`.

---

# 9. Configurar el bot de Discord

Has de crear el bot des del Discord Developer Portal:

https://discord.com/developers/applications

Crea una aplicaci¨® nova i afegeix-hi un bot.

A la configuraci¨® del bot activa els intents necessaris.

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

* Python est¨¤ instal¡¤lat
* VS Code est¨¤ instal¡¤lat
* el projecte est¨¤ obert
* l'entorn `venv` est¨¤ activat
* els requirements estan instal¡¤lats
* `.env` est¨¤ configurat

nom¨¦s cal executar:

```powershell
py bot.py
```

Aix¨° ¨¦s tot.

No cal executar cap comanda complicada.

---

# 11. Fer que `venv` s'activi autom¨¤ticament a VS Code

Per no haver d'escriure cada vegada:

```powershell
.\venv\Scripts\activate
```

VS Code pot seleccionar autom¨¤ticament l'entorn virtual.

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

Despr¨¦s tanca la terminal actual i obre:

```text
Terminal ¡ú New Terminal
```

VS Code normalment activar¨¤ autom¨¤ticament:

```text
(venv)
```

A partir d'aquest moment, quan obris el projecte a VS Code i una terminal nova s'activi correctament, nom¨¦s haur¨¤s de fer:

```powershell
py bot.py
```

---

# 12. Aturar el bot

Per aturar el bot des de la terminal:

```text
Ctrl + C
```

El bot es desconnectar¨¤ de Discord.

---

# 13. Tornar a iniciar-lo un altre dia

Obre el projecte `RebirthBot` amb VS Code.

Obre:

```text
Terminal ¡ú New Terminal
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

i despr¨¦s:

```powershell
py bot.py
```

---

# Errors habituals

## `py` no es reconeix

Python probablement no est¨¤ instal¡¤lat correctament o no s'ha afegit al PATH.

Comprova:

```powershell
py --version
```

Si no funciona, torna a instal¡¤lar Python i activa:

```text
Add Python.exe to PATH
```

---

## `No module named discord`

No s'han instal¡¤lat els requirements o no est¨¤ activat el `venv`.

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

## El bot no inicia perqu¨¨ falta el token

Comprova que existeix:

```text
.env
```

i que cont¨¦:

```env
DISCORD_TOKEN=EL_TEU_TOKEN
```

No posis cometes i no deixis espais al voltant de `=`.

---

## El bot es connecta per¨° no funcionen alguns comandos

Comprova que els intents necessaris estan activats al Discord Developer Portal i que el bot t¨¦ els permisos necessaris al servidor.

---

# Resum r¨¤pid

Una vegada instal¡¤lat i configurat tot, el funcionament habitual ¨¦s simplement:

```powershell
# Obrir el projecte amb VS Code

# Obrir:
Terminal ¡ú New Terminal

# Si apareix (venv):
py bot.py
```

I el bot comen?ar¨¤ a funcionar.

---

# Important

**No pugis mai a GitHub:**

```text
.env
venv/
```

El `.gitignore` del projecte ja est¨¤ configurat per ignorar aquests fitxers i carpetes.

Especialment, **mai comparteixis el token del bot**.

Si el token es fa p¨²blic accidentalment, genera'n un de nou immediatament des del Discord Developer Portal.

## Llic¨¨ncia

Aquest projecte est¨¤ publicat sota la **llic¨¨ncia MIT**.

## Autor

Creat per **fustcoma**.
