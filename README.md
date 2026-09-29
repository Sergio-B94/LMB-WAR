# Dashboard WAR — Piratas de Campeche / LMB 2026

**Estado:** ✅ Publicado y funcionando. También en GitHub: https://github.com/Sergio-B94/LMB-WAR (repo público).
**Link del dashboard (Artifact):** https://claude.ai/code/artifact/cb7c99b6-13f1-448c-b26d-93f7cb823b1e
**Snapshot de datos actual:** 19 de agosto de 2026 (Piratas iba 52-41, 93 juegos jugados; temporada
regular de 93 juegos ya estaba terminada para Piratas en esa fecha). El **29 de septiembre de 2026**
se hizo un refresco parcial: se agregaron las columnas **H (Hits)** a bateo y **K (Ponches)** a
pitcheo de liga, jalando Hits en vivo de la API para los 18 equipos que no tenía guardados — ver
sección 7 ("Adición de columnas H/K"). El resto de las métricas (WAR, OPS+, ERA+, wRC+, etc.) siguen
siendo el snapshot original del 19-ago.

Este documento existe para que una conversación futura (con contexto nuevo, sin memoria de esta)
pueda retomar el proyecto sin tener que re-descubrir nada de lo que costó tiempo encontrar la
primera vez — sobre todo la API interna de lmb.com.mx, que no está documentada en ningún lado.

---

## 1. Qué es esto

Un dashboard (Artifact de Claude, HTML autocontenido) con estadísticas y métricas sabermétricas
**aproximadas** de la Liga Mexicana de Beisbol, temporada 2026:

- Roster completo de bateo y pitcheo de **Piratas de Campeche**.
- Clasificación de **toda la liga** (130 bateadores + 49 lanzadores calificados de las 20 novenas).
- Métricas calculadas: **WAR aproximado**, **OPS+**, **ERA+**, **wRC+** (todas con contexto 100%
  derivado de la LMB 2026, no de MLB — ver sección 4).
- Niveles de desempeño por color (MVP / Sobre promedio / Promedio / Bajo promedio / Banca).
- Bandera de nacionalidad de cada jugador (ver sección 5 — truco: se sacó de la API de MLB, no de
  la LMB, porque la LMB no publica esto).
- Organizado en 2 pestañas: "Piratas de Campeche" y "Toda la liga — LMB 2026".
- Metodología completa documentada dentro del propio dashboard (sección `<details>` desplegable
  al fondo de la página).

**Importante:** no existe un WAR oficial de la LMB. Todo esto es una aproximación sabermétrica de
bricolaje, construida porque el sitio oficial no publica nada parecido. Está etiquetado como tal
en el propio dashboard.

---

## 2. Estructura de este repositorio local

**Ruta real del proyecto:** `C:\Users\hp\OneDrive\Sergio Notaria Claude\CODE\LMB\` — ojo, en sesiones
anteriores se usó por error el atajo `C:\Users\hp\OneDrive\LMB\` (funcionaba porque existía algún tipo de
acceso directo/unión hacia la ruta real, pero dejó de existir el 20-ago-2026 a media sesión y todos los
comandos con esa ruta corta empezaron a fallar con "no existe"). Si alguna vez un comando de shell dice que
la carpeta no existe pero las herramientas de archivo sí la leen, es esto — usa la ruta completa de abajo.

```
C:\Users\hp\OneDrive\Sergio Notaria Claude\CODE\LMB\
├── README.md                  <- este archivo
├── dashboard\
│   └── piratas_war.html       <- ÚLTIMA versión publicada del Artifact (fuente completa, ~93KB)
├── data\                      <- snapshots crudos y calculados (del 19-ago-2026)
│   ├── piratas_hit.json       <- 28 bateadores de Piratas (playerPool=ALL)
│   ├── piratas_pit.json       <- 34 lanzadores de Piratas (playerPool=ALL)
│   ├── liga_hit.json          <- 130 bateadores calificados de TODA la liga (playerPool=QUALIFIED)
│   ├── liga_pit.json          <- 49 lanzadores calificados de TODA la liga (playerPool=QUALIFIED)
│   ├── league_agg.json        <- sumas agregadas de liga (para derivar wOBA/ERA/etc. de liga)
│   ├── league_standings.json  <- G/P/Carreras Anotadas de las 20 novenas (para runs-por-victoria)
│   ├── name_to_code.json      <- nombre de jugador -> código de país (US/MX/DO/VE/PR/CU/CO/NI/PA/CA)
│   ├── war_output.json        <- salida completa de compute_war.py (Piratas)
│   └── war_liga_output.json   <- salida completa de compute_war_liga.py (toda la liga)
└── scripts\                   <- scripts Python que generan/actualizan todo (ver sección 6)
    ├── compute_war.py         <- calcula WAR/OPS+/ERA+ para Piratas
    ├── compute_war_liga.py    <- calcula WAR/OPS+/ERA+ para toda la liga + valida nivel de reemplazo
    ├── inject_liga.py         <- inyecta la sección "Toda la liga" en el HTML (histórico, ya aplicado)
    ├── inject_flags2.py       <- inyecta código de país en los arreglos de datos del HTML
    ├── inject_wrcplus.py      <- calcula e inyecta wRC+ en las tablas de bateo
    ├── add_tabs.py            <- envuelve las secciones en las 2 pestañas (histórico, ya aplicado)
    ├── remove_warplus_add_tabs.py <- quitó el "WAR+" (métrica descartada, ver sección 7)
    ├── flag_svgs.py           <- define las 10 banderas SVG usadas (evita el bug de Windows)
    └── serve.py               <- server HTTP local con charset UTF-8 correcto, para probar el HTML
```

`dashboard/piratas_war.html` es exactamente el archivo que está publicado ahora mismo en el
Artifact de arriba. Si quieres volver a publicarlo sin cambios (por ejemplo, si el Artifact se
perdiera), usa la herramienta Artifact con `file_path` apuntando a este archivo y `url` apuntando
al link de arriba, para actualizar el mismo Artifact en vez de crear uno nuevo.

---

## 3. La API interna de lmb.com.mx (el hallazgo clave)

lmb.com.mx **no tiene una API pública documentada**, pero es una app Next.js que expone rutas
internas usadas por su propio frontend. Se descubrieron inspeccionando los chunks JS del sitio.

### 3.1 Estadísticas de jugadores

```
GET https://lmb.com.mx/estadisticas/api/player
```

Parámetros (todos van en query string):

| Parámetro | Valores | Notas |
|---|---|---|
| `categoryType` | `hitting` \| `pitching` | |
| `year` | ej. `2026` | temporadas disponibles: 2005–2026 |
| `gameType` | `R` (regular) \| `P` (postemporada) | |
| `page` | entero desde 1 | **el tamaño de página es fijo en 10**, el parámetro `size` se ignora |
| `playerPool` | `QUALIFIED` \| `ALL` \| `ROOKIES` \| `QUALIFIED_ROOKIES` \| `ALL_CURRENT` | `QUALIFIED` = solo los que superan el mínimo de turnos/entradas de la liga |
| `teamId` | ej. `523` para Piratas (ver tabla abajo) | opcional; si se omite, es toda la liga |
| `sortBy` | ej. `avg`, `era` | **hace falta también mandar `order` y `expanded`, si no la API regresa `[]` vacío** (bug/comportamiento raro del backend) |
| `order` | `asc` \| `desc` | |
| `expanded` | `0` \| `1` | `1` trae también `extendedStats` (BABIP, IBB, etc.) |

Petición mínima que SÍ funciona (probada):
```
/estadisticas/api/player?categoryType=hitting&year=2026&gameType=R&page=1&playerPool=QUALIFIED&sortBy=avg&order=desc&expanded=1
```

Respuesta: `{ topBanner, banner, meta:{page,size,total}, player_stats:[...], glossary }`. Cada
elemento de `player_stats` trae `permalink` (ver 3.3), `rank`, `name`, `team_name`,
`team_logo_url`, `player_image_url`, `position`, `stats:[{short_name,value}]` y (si `expanded=1`)
`extendedStats:[...]`.

IDs de equipo usados en este proyecto: **Piratas = 523**. Hay más equipos listados en el dropdown
de `/estadisticas` si se necesitan (Diablos Rojos, Sultanes, Águila, etc.) — se pueden sacar del
HTML de esa página (`<select>` de "Equipo").

### 3.2 Posiciones / carreras anotadas por equipo

No se encontró una API JSON limpia para esto. Se obtuvo leyendo el **texto renderizado** de
`https://lmb.com.mx/posiciones` (tabla de standings), que trae G, P, CA (carreras anotadas), CP,
etc. de las 20 novenas. Esto es lo que alimenta `league_standings.json` y de ahí el cálculo de
runs-por-victoria (sección 4).

### 3.3 Ficha individual de jugador (para nacionalidad)

Ruta: `https://lmb.com.mx/jugador/<id>` — el `<id>` es el mismo número que aparece en
`permalink` y en `player_image_url` de la API de estadísticas.

**Hallazgo importante:** ese `<id>` numérico **es el ID oficial de MLB Advanced Media (MLBAM)**.
Se verificó cruzándolo contra la API pública y gratuita de MLB Stats:
```
https://statsapi.mlb.com/api/v1/people?personIds=1,2,3,...
```
(acepta lote de hasta ~50 IDs por request cómodamente). El campo `birthCountry` da la
nacionalidad. **Siempre verificar que `fullName` de la respuesta coincida con el nombre de la
LMB antes de aceptar el país** — un ID que no corresponda a nadie real en MLBAM puede devolver
una persona distinta por coincidencia. En este proyecto, 234 de 235 jugadores del snapshot
verificaron correctamente por nombre (el único sin dato, un lanzador extranjero, tampoco tiene
`birthCountry` registrado en la propia base de MLB).

La ficha de jugador de lmb.com.mx (`/jugador/<id>`) en sí **no publica nacionalidad** — solo
posición, mano de bateo/lanzamiento, edad y fecha de nacimiento. Por eso hubo que ir a la fuente
externa.

### 3.4 Cómo se hicieron las llamadas

Todas las peticiones se hicieron con `fetch()` desde la consola del navegador (herramienta
`javascript_tool` del navegador Claude), navegando primero a `https://lmb.com.mx/estadisticas`
para tener el origen correcto (rutas relativas `/estadisticas/api/...`). La API de MLB Stats
(`statsapi.mlb.com`) sí acepta CORS desde cualquier origen, así que esa se pudo llamar incluso
desde `localhost` durante las pruebas.

**Gotcha:** la primera vez que se intentó, la API devolvía `[]` (vacío) con parámetros que
parecían correctos. La causa fue no mandar `sortBy`+`order`+`expanded` juntos — con esos tres
presentes, empezó a devolver datos reales.

---

## 4. Metodología del WAR/OPS+/ERA+/wRC+ aproximados

Todo el detalle con fórmulas exactas está en la sección `<details>` de metodología dentro del
propio dashboard (búscala en el HTML: `<details class="method">`). Resumen de las constantes:

### 4.1 Derivado 100% de datos reales de la LMB 2026 (NO de MLB)

| Constante | Valor | Cómo se derivó |
|---|---|---|
| `wOBA` de liga | 0.3701 | de los 130 bateadores calificados (`liga_hit.json` / `league_agg.json`) |
| `OBP`/`SLG` de liga | 0.3702 / 0.4711 | ídem, para OPS+ |
| `R/PA` de liga | 0.146 | ídem, para wRC+ (6,273 carreras / 42,965 turnos) |
| `ERA`/`FIP` de liga | 4.832 / 4.832 | de los 49 lanzadores calificados |
| Constante FIP | 3.864 | calibrada para que FIP de liga = ERA de liga (no es la constante de MLB) |
| **Runs por victoria** | **10.97** | fórmula de Tango (*The Book*): `10 × √(2 × runs/juego/equipo / 9)`, usando el runs/juego/equipo real de la LMB (5.42, sacado de `league_standings.json`) — MLB usa un 10.0 fijo basado en su propio ~4.5 runs/juego |
| Nivel de reemplazo (bateo) | 21.9 runs/600PA | `2.0 wins × 10.97 runs/win` (re-derivado con el runs/win de la LMB, no el de MLB) |
| Nivel de reemplazo (pitcheo) | +0.987 de FIP | misma convención de "2.0 wins" que el bateo, ya no un multiplicador arbitrario |
| Temporada LMB 2026 | **93 juegos** | confirmado en `/posiciones` (Piratas iba 52-41) |

### 4.2 Importado de la sabermetría estándar (no se pudo derivar con esta API)

- **Pesos del wOBA** (0.69 BB, 0.72 HBP, 0.89 1B, 1.27 2B, 1.62 3B, 2.10 HR): requieren tablas de
  expectativa de carreras por situación de bases/outs (datos jugada-por-jugada) que la API de la
  LMB no expone. Es la limitación más importante y honesta del proyecto.
- **Ajuste posicional** por posición defensiva (C +12.5, SS +7.5, 2B/3B/CF +2.5, LF/RF −7.5,
  1B −12.5, DH −17.5 por 600 PA): no hay métricas de fildeo individual disponibles.
- **wOBA scale** = 1.20: constante de conversión, valor típico moderno, no re-derivada.
- **"2.0 wins = titular promedio"**: el ancla de nivel de reemplazo. Sí se **validó** empíricamente
  contra los datos reales de la LMB — ver 4.3.
- No hay **factor de parque** (afecta a OPS+, ERA+, wRC+): no se encontraron datos de parques de
  la LMB.

### 4.3 Validación hecha (importante, no te la saltes si vuelves a tocar esto)

Se calculó el WAR de los 130 bateadores y 49 lanzadores calificados de TODA la liga (no solo
Piratas) y se promedió, ponderado por PA/IP, entre los que de verdad son titulares de tiempo
completo (bateadores ≥300 PA, lanzadores ≥60 IP):

- Bateo: WAR promedio real = **1.92–1.95** (vs. 2.0 asumido)
- Pitcheo: WAR promedio real = **1.97–2.00** (vs. 2.0 asumido)

Conclusión: el supuesto de "2.0 WAR = titular promedio" (importado de la sabermetría de MLB)
resultó, en la práctica, bastante acertado para la LMB. Está documentado así en el dashboard,
con este resultado como evidencia.

También se hizo una comprobación de sanidad para wRC+: el promedio ponderado por turnos de los
130 bateadores calificados da wRC+ = 99.9 (debe dar ~100 por construcción matemática si la
fórmula está bien implementada — y dio bien).

### 4.4 Fórmulas finales

```
wOBA = (0.69·BB + 0.72·HBP + 0.89·1B + 1.27·2B + 1.62·3B + 2.10·HR) / (AB + BB − IBB + SF + HBP)
wRAA = ((wOBA − wOBA_liga) / 1.20) × PA
wSB  = SB×0.2 − CS×0.4
WAR(bateo) = (wRAA + wSB + AjustePosicional + 21.9×(PA/600)) / 10.97

FIP = (13·HR + 3·(BB + HBP − IBB) − 2·K) / IP + 3.864
WAR(pitcheo) = ((FIP_liga + 0.987 − FIP_jugador) × IP/9) / 10.97

OPS+ = 100 × (OBP/OBP_liga + SLG/SLG_liga − 1)
ERA+ = 100 × ERA_liga / ERA   (con piso de ERA=0.10 y techo de 999, para evitar infinitos)
wRC+ = 100 × [ ((wOBA − wOBA_liga)/1.20) + R/PA_liga ] / (R/PA_liga)
```

Niveles por WAR (usados en toda la app, colores en `.tier-badge` del CSS):
`MVP ≥4.0` · `Sobre promedio 2.0–4.0` · `Promedio 1.0–2.0` · `Bajo promedio 0–1.0` · `Banca <0`.

---

## 5. Banderas de nacionalidad — por qué son SVG y no emoji

Al principio se usaron emoji de bandera (🇺🇸🇲🇽...). **En Windows se ven como códigos de letras**
("US", "MX") en vez de la imagen de la bandera — es una limitación real de la fuente del sistema,
no un bug del código. Para que se vea igual en cualquier dispositivo, se reemplazaron por **10
SVGs inline** hechos a mano (simplificados, sin escudos/emblemas, pero con los colores correctos),
definidos en `scripts/flag_svgs.py` e insertados en el HTML como `const FLAG_SVG = {...}`.

Los 10 países presentes en el snapshot actual: US, MX, DO, VE, PR, CU, CO, NI, PA, CA. Si en un
snapshot futuro aparece un país nuevo (por un fichaje), hay que:
1. Agregar su bandera SVG a `flag_svgs.py`.
2. Agregar el país nuevo al diccionario `countryToFlag`/`emoji_to_code` (ver histórico en
   `inject_flags2.py` — ojo, ese script ya asume que existe `name_to_code.json`; si aparece un
   país nuevo, ese mapeo de MLB Stats API → código de 2 letras hay que extenderlo a mano).

---

## 6. Cómo actualizar el dashboard con un snapshot más reciente

Esto es lo que haría una sesión futura si el usuario pide "actualiza el dashboard":

1. **Traer datos frescos** (navegar a `https://lmb.com.mx/estadisticas` con el navegador, usar
   `fetch()` en consola — ver sección 3):
   - Piratas: `categoryType=hitting|pitching`, `teamId=523`, `playerPool=ALL`, recorrer páginas.
   - Liga completa: mismos parámetros pero sin `teamId`, `playerPool=QUALIFIED`, recorrer páginas
     (13 para bateo ~130, 5 para pitcheo ~49 — el total exacto viene en `meta.total`).
   - Standings: `https://lmb.com.mx/posiciones`, leer texto renderizado (G/P/CA de las 20 novenas).
   - Guardar todo como JSON en `data/` (mismo formato que los archivos ya existentes, para que los
     scripts de `scripts/` los puedan leer sin cambios).
2. **Recalcular:**
   ```
   python scripts/compute_war.py        # Piratas -> data/war_output.json
   python scripts/compute_war_liga.py   # Liga completa -> data/war_liga_output.json (+ valida el 2.0 de reemplazo)
   ```
3. **Nacionalidad** (solo hace falta re-hacer esto si aparecen jugadores nuevos que no estén ya en
   `data/name_to_code.json` — si son los mismos 235 jugadores, se puede reusar el archivo tal cual):
   cruzar los IDs nuevos contra `https://statsapi.mlb.com/api/v1/people?personIds=...`, verificar
   por nombre, actualizar `name_to_code.json`.
4. **Inyectar todo en el HTML** — los scripts de inyección (`inject_liga.py`, `inject_flags2.py`,
   `inject_wrcplus.py`) leen `dashboard/piratas_war.html`, hacen el parse/edit de los `const
   BATTING/PITCHING/LIGA_BATTING/LIGA_PITCHING` (son JSON válido embebido en JS, se puede
   `json.loads`/`json.dumps` directo) y lo vuelven a guardar. **Ojo:** estos scripts tienen las
   rutas de archivo hardcodeadas al scratchpad de la sesión en la que se escribieron — si se
   reusan, hay que ajustar `SCRATCH`/`HTML_PATH` a `C:\Users\hp\OneDrive\Sergio Notaria Claude\CODE\LMB\dashboard\`
   y `C:\Users\hp\OneDrive\Sergio Notaria Claude\CODE\LMB\data\` (ver ruta real en sección 2).
5. **Probar localmente antes de publicar** — usar `scripts/serve.py` (sirve el HTML con charset
   UTF-8 correcto; el server HTTP nativo de Python sin esto corrompe los acentos) y revisar en el
   navegador antes de republicar.
6. **Publicar** — herramienta Artifact, `file_path` = `dashboard/piratas_war.html`, `url` = el
   link de la sección de arriba (para actualizar el mismo Artifact, no crear uno nuevo).

---

## 7. Historial de decisiones (por si alguien pregunta "por qué no...")

- **"WAR+"** existió brevemente como un índice de ritmo (no oficial, inventado para este panel) y
  **se eliminó** a pedido del usuario. La validación del nivel de reemplazo que se hizo de paso
  (sección 4.3) se conservó porque es un hallazgo real y útil, independiente de WAR+.
- **wRC+** sí se mantiene — es una métrica sabermétrica real y reconocida (FanGraphs, etc.), no
  inventada, y quedó calculada 100% con contexto de la LMB.
- Se **descartó** intentar factor de parque, defensa individual (fildeo) y apalancamiento de
  relevistas: ninguno tiene datos disponibles vía esta API.
- El emoji 🏴‍☠️ como favicon del Artifact se mantuvo estable entre republicaciones (regla de
  Artifacts: no cambiar el favicon salvo pivote de tema).

### Adición de columnas H/K (29-sep-2026)

El dashboard había crecido, en una sesión anterior no documentada aquí, a un selector de las **20
equipos** de la LMB (`OTHER_TEAMS` / `ZONA_NORTE_TEAMS` en el HTML), además de las pestañas
Piratas/Liga originales — este README no reflejaba esa estructura hasta ahora. Al pedir agregar
**Hits** a bateo y **Ponches (K)** a pitcheo:

- **K ya existía** en todos los datos de pitcheo (equipo y liga) — solo faltaba la columna en la
  tabla "Toda la liga" (`ligaPitTable`); en las tablas por equipo ya se mostraba (columna con
  encabezado `"P"`, de "Ponches").
- **H (Hits) no existía en ningún lado.** Para Piratas y para los 130 bateadores calificados de
  "Toda la liga" se pudo sacar de `data/piratas_hit.json` y `data/liga_hit.json` (ya guardados). Para
  los otros 18 equipos del selector no había datos crudos guardados, así que se volvió a consultar
  `GET /estadisticas/api/player?categoryType=hitting&playerPool=ALL&...` **sin filtro de equipo**
  (464 bateadores de toda la liga, 47 páginas) y se cruzó por nombre — el campo `team_name` de la
  API ya viene por jugador, así que no hizo falta descubrir `teamId` de cada equipo. Ese fetch quedó
  guardado en `data/hitting_all_teams_2026-09-29.csv` y el script de mezcla en
  `scripts/add_hits_k_columns.py`.
- **87 jugadores** habían cambiado de equipo entre el 19-ago y el 29-sep (normal, mes y medio de
  temporada) — el script de mezcla primero intenta emparejar por equipo+nombre, y si no encuentra,
  cae a una búsqueda por nombre en toda la liga (con chequeo de ambigüedad). Los `�` que se ven en
  nombres como "El Águila" al imprimir con Bash/PowerShell **no son corrupción real** — es la
  limitación de esas terminales para mostrar acentos (confirmado con `chr(0xFFFD)` count = 0 en el
  archivo); el HTML en sí está limpio.
- Se publicó el proyecto completo (dashboard, datos, scripts, este README) en un repositorio público
  de GitHub: https://github.com/Sergio-B94/LMB-WAR — para no perder el trabajo y tener base para la
  temporada 2027.

### Bug de codificación (mojibake) — cuidado si tocas el archivo con PowerShell

En algún punto se usó `Get-Content -Raw` + `-replace` + `Set-Content -Encoding utf8` de
PowerShell para un cambio rápido, y **corrompió los acentos y símbolos especiales** de todo el
archivo (dobles-codificación UTF-8→CP1252→UTF-8). Se reparó con un script Python
(`fix_mojibake3.py`, no copiado aquí porque ya no hace falta — el archivo actual está limpio).
**Lección: nunca uses PowerShell `Get-Content`/`-replace`/`Set-Content` en este HTML.** Usa
siempre Python (`encoding="utf-8"` explícito) o la herramienta `Edit` directamente.

---

## 8. Limitaciones que quedan pendientes (honestidad ante el usuario)

- No hay factor de parque para OPS+/ERA+/wRC+.
- No hay defensa individual (fildeo) en el WAR — confirmado que no hay forma de conseguirla, ver 8.1.
- Los pesos del wOBA siguen importados de MLB (no derivables sin datos jugada-por-jugada).
- Es un snapshot fijo — no se actualiza solo. Si pasa tiempo desde el 19-ago-2026, avisa al
  usuario que los números están desactualizados y ofrece refrescarlos (sección 6).

### 8.1 `categoryType=fielding` — probado, no funciona. Splits situacionales — SÍ FUNCIONAN (corregido 26-ago-2026)

- `categoryType=fielding` / `defense` / `defensive`: `fielding` responde 200 pero con un objeto de
  pitcheo con todos los campos en `null` (una plantilla por defecto, no datos reales); `defense` y
  `defensive` responden `[]` vacío. **No hay endpoint de fildeo real en esta API.** Esto sigue firme.

- **CORRECCIÓN IMPORTANTE — lo de abajo estaba mal, no lo repitas:** el 20-ago-2026 se concluyó
  aquí mismo que el selector "Elige una dividida" no filtraba nada, probando `split=risp` /
  `split=lc` contra `/estadisticas/api/player` y viendo que los totales no cambiaban. **El
  parámetro estaba mal adivinado.** El usuario capturó la petición real de su propio navegador
  (DevTools → Network) el 26-ago-2026 y el parámetro correcto es **`sitCodes`**, no `split`:
  ```
  /estadisticas/api/player?year=2026&playerPool=QUALIFIED&categoryType=hitting&expanded=0&page=1&sortBy=avg&order=desc&sitCodes=risp
  ```
  Verificado con `fetch()`: `sitCodes=risp` (Posición Anotadora) SÍ cambia los totales devueltos
  (menos juegos, AVG/OPS distintos) comparado con la misma consulta sin ese parámetro — no es un
  falso positivo. Los valores de `sitCodes` disponibles son los mismos que ya se habían leído del
  HTML del `<select>` en el intento anterior (ver los `<option value="...">` de "Elige una
  dividida" en `/estadisticas`): `risp` (posición anotadora), `risp2`, `ron` (corredores en base),
  `r123` (bases llenas), `r0` (bases limpias), `lc` (tarde/cierre — la definición sabermétrica
  real de "clutch"), `sah`/`sbh`/`sti` (equipo arriba/abajo/empatado), `vl`/`vr` (vs zurdos/vs
  derechos), `h`/`a` (casa/visita), meses, entradas, conteos de bola-strike, etc. — la lista
  completa está en la sección 3.4 original (`/estadisticas`, `<select>` "Elige una dividida").

- **Por qué el intento anterior no encontró esto solo:** no fue únicamente el nombre de parámetro
  equivocado — el `<select>` real de la página nunca llegó a interactuarse directamente en el
  navegador automatizado de esta sesión. Se investigó por qué: el contenedor de los filtros queda
  atrapado en un **boundary de Suspense de Next.js sin hidratar** (`<div hidden id="S:1">`, un
  placeholder de React Server Components que nunca se reemplaza por el contenido real) — se
  confirmó con `document.getElementById('S:1')` siguiendo `hidden=true` incluso después de
  esperar varios segundos con `document.readyState === "complete"` y cero errores en consola. En
  el navegador real del usuario esto hidrata sin problema; en el navegador automatizado de Claude
  (`mcp__Claude_Browser`), no. No se investigó la causa raíz (¿detección de automatización?
  ¿alguna API del navegador ausente?) — si hace falta interactuar con el `<select>` real de nuevo,
  hay que pedirle al usuario que capture la petición desde su propio DevTools (Network tab →
  Headers → Request URL), como se hizo aquí, en vez de perseguir la hidratación.

- **Impacto:** esto NO habilita un WPA real (Win Probability Added) — eso necesita tablas de
  probabilidad de victoria por estado exacto del juego (entrada/marcador/outs/corredores), que
  siguen sin existir en esta API. Pero SÍ habilita splits situacionales reales — en particular
  `lc` (tarde/cierre) y `risp` — que se pueden usar para una aproximación de "clutch" (comparar
  wOBA en esas situaciones contra el wOBA de temporada completa del mismo jugador/equipo). La
  defensa/fildeo sigue bloqueada de forma permanente; el clutch/secuenciación **ya no está
  bloqueado**, solo no se ha construido todavía. Pendiente de que el usuario decida si lo quiere.

### 8.2 Validación hecha: WAR vs. récord real de las 20 novenas (20-ago-2026)

Se calculó el WAR combinado (bateo+pitcheo, `playerPool=ALL`, roster completo) de las 19 novenas
restantes además de Piratas, y se regresionó contra su récord real de `/posiciones`:
**`victorias = 31.3 + 1.10 × WAR`, R²=0.68** (los 20 `teamId` están en el script de abajo si hace
falta repetirlo). Hallazgo: el nivel de reemplazo asumido (28 victorias/93 juegos, importado de la
convención de MLB) está calibrado un poco bajo — el que mejor ajusta a los datos reales de esta
liga es **31.3**. Esto explica buena parte (no toda) de por qué el récord real de los equipos suele
superar al que predice `reemplazo + WAR` de este panel.

### 8.3 Se intentó aplicar la recalibración (20-ago-2026) — se revirtió, con evidencia

El usuario pidió aplicar el 31.3 al WAR individual. Se reescaló `REPL_WINS_REFERENCE` de `2.0` a
`1.644` (razón de brechas promedio-reemplazo: `(46.5-31.3)/(46.5-28.0) = 0.822`, **no** la razón
directa 31.3/28 — ese fue un primer error de signo que se corrigió a media tarea) y se recalculó el
WAR combinado de las 20 novenas con la fórmula ya corregida, para verificar que quedara
autoconsistente. **No convergió:** al volver a correr la regresión con los números nuevos, el
intercepto subió de 31.3 a 35.2 en vez de estabilizarse — cada corrección pide otra corrección más
grande, sin llegar a un punto fijo. Y el hallazgo clave: el **R² no cambió** (0.675 en ambos casos)
— mover `REPL_WINS_REFERENCE` no reduce nada de la varianza sin explicar, solo reetiqueta dónde
está el cero (es casi una traslación uniforme del WAR de cada equipo, y OLS absorbe eso
íntegramente en el intercepto sin que la pendiente ni el ajuste cambien). Con solo 20
equipos-temporada, el nivel de reemplazo exacto no está bien determinado — el intervalo de
confianza del 95% ya daba [26.0, 36.6], amplio de por sí.

**Decisión final: se revirtió `REPL_WINS_REFERENCE` a `2.0` en ambos scripts** (con la nota
completa dejada como comentario ahí mismo) — el WAR individual de todos los jugadores en el
dashboard es idéntico al de antes de este intento, verificado corriendo `compute_war.py` de nuevo
y comparando contra los valores publicados. El hallazgo de la sección 8.2 (31.3 vs 28) sigue
documentado en el dashboard como validación honesta, junto con el intento de aplicarlo y por qué
no se quedó aplicado. Si en el futuro se acumulan más temporadas de datos (más equipos-temporada),
vale la pena repetir este ejercicio con una muestra más grande antes de intentar aplicarlo de nuevo.

---

## 9. Selector de equipo — Zona Sur (20-ago-2026)

**Estética:** también en esta fecha se cambió la identidad visual del dashboard a los colores reales
de Piratas de Campeche (negro `#1D1D1B` / rojo `#E10E17`, sacados muestreando el PNG del escudo, no
inventados) y se agregó el logo del equipo arriba del header, con una placa clara fija detrás (el
negro del logo se perdía contra el fondo en modo oscuro sin esa placa — si se vuelve a tocar la
paleta, cuidado con ese detalle). También se quitó el gráfico de barras divergentes de las secciones
de Piratas/equipo — solo quedan las tablas ordenables.

**El cambio funcional:** lo que antes era la pestaña fija "Piratas de Campeche" ahora es la pestaña
"Mi equipo" con un `<select id="teamSelect">` (con dos `<optgroup>`, Zona Sur y Zona Norte) que cambia
entre las **20 novenas de la LMB** — Zona Sur (Diablos Rojos, Olmecas, Piratas, Pericos, Bravos,
Guerreros, El Águila, Tigres, Conspiradores, Leones) y Zona Norte (Toros, Caliente, Sultanes, Charros,
Acereros, Algodoneros, Rieleros, Saraperos, Tecos, Dorados) — agrupación oficial sacada de
`lmb.com.mx/posiciones` (ver sección 3.5 para cómo). La Zona Norte se agregó el 21-ago-2026, mismo
patrón exacto que la Zona Sur (ver más abajo). Cada equipo tiene su roster completo (`playerPool=ALL`,
bateo + pitcheo) calculado con la **misma fórmula y el mismo contexto de liga** de la sección 4
(wOBA/RPW/nivel de reemplazo de las 20 novenas) — no se recalibró nada por zona ni por equipo, solo se
le dio a cada equipo su propia tabla en vez de que solo Piratas la tuviera. Con esto, el dashboard ya
cubre las 20/20 novenas — no queda ningún equipo pendiente.

### 3.5 Cómo se sacó la agrupación de zonas

`lmb.com.mx/posiciones` (mismo bug de layout que las demás páginas: hay que leer el DOM porque el
texto renderizado normal viene vacío) trae dos tablas con clase `table.StatsTable_entityTable__tDPxk`
dentro de contenedores `.StandingsLayout_zoneWrapper__PB8to` con un `<h2 class="StandingsLayout_zoneName__cSLhk">`
que dice "Norte" o "Sur" — hay 4 de cada uno por el duplicado mobile/desktop de siempre, pero las
tablas SÍ tienen filas (a diferencia de otras páginas donde el layout completo estaba vacío). Se leyó
con `document.querySelectorAll('table.StatsTable_entityTable__tDPxk')` y se tomó el primer nombre de
cada `tbody tr` como equipo. Bonus: esta tabla también trae **CP (carreras permitidas)** por equipo,
que no se había conseguido antes (solo teníamos CA) — útil si algún día se quiere calcular el récord
Pitagórico real para la validación de la sección 8.2/8.3.

### Cómo se generaron los datos de los 19 equipos nuevos (9 Zona Sur + 10 Zona Norte)

Mismo patrón que la validación de 20 equipos (sección 8.2), repetido dos veces (Zona Sur el
20-ago-2026, Zona Norte el 21-ago-2026): fetch de `playerPool=ALL` por `teamId` —
Zona Sur: Diablos Rojos=532, Olmecas=442, Pericos=520, Bravos=434, Guerreros=579, El Águila=5567,
Tigres=569, Conspiradores=6303, Leones=496.
Zona Norte: Toros=5010, Caliente=4444, Sultanes=562, Charros=6304, Acereros=560, Algodoneros=447,
Rieleros=528, Saraperos=502, Tecos=536, Dorados=575.
Calculado directo en JS del navegador (mismas fórmulas que `compute_war.py`, constantes
hardcodeadas del objeto `LEAGUE` del HTML) para evitar el viaje de ida y vuelta de guardar JSON
crudo y correr el script Python. En el HTML, los datos quedan en dos const separadas —
`OTHER_TEAMS` (Zona Sur) y `ZONA_NORTE_TEAMS` (Zona Norte) — que se combinan con `Object.assign`
en `TEAM_DATA` junto con Piratas. Las banderas de nacionalidad se reusaron del mapa nombre→código
ya construido (233 jugadores de Piratas + los calificados de toda la liga, que ya cubre jugadores
de las 20 novenas porque `LIGA_BATTING`/`LIGA_PITCHING` siempre fue liga completa) — los jugadores
nuevos que no calificaron antes (banca, relevo corto) se quedan sin bandera, igual que el patrón ya
establecido en la sección 5 (se degrada con gracia, no rompe nada).

## 10. Jugadores traspasados a media temporada (22-ago-2026)

**El problema:** cada pestaña de equipo se calcula con un fetch independiente (`playerPool=ALL` por
`teamId`). Un jugador traspasado a media temporada aparece en los rosters de AMBOS equipos, pero
cada uno solo trae las estadísticas que acumuló mientras estuvo ahí — nunca su temporada completa.
La tabla "Toda la liga" (`LIGA_BATTING`/`LIGA_PITCHING`) no tiene este problema porque viene del
`playerPool=QUALIFIED` de la propia LMB, que ya suma la temporada completa bajo el equipo actual del
jugador.

**Cómo se detecta un traspaso real (no un homónimo):** cruzar el mismo nombre en dos equipos NO basta
— hay nombres comunes que se repiten entre jugadores distintos (ej. "Ali Castillo" vs "Jesse
Castillo" en Tecos). Hay que comparar el campo `permalink` de la respuesta de la API (el ID único de
jugador, ej. `/477399`) entre ambos equipos. Si el `permalink` coincide, es la misma persona.

**Qué se hizo:** el usuario pidió el tratamiento para 3 jugadores puntuales, verificados uno por uno
contra la API:
- **Jesse Castillo** (Tecos → Piratas, confirmado por permalink `/477399`): 181 PA con Piratas + 214
  con Tecos = 395 PA, coincide exacto con `LIGA_BATTING`.
- **Roberto Valenzuela** (El Águila → Diablos Rojos, permalink `/672438`): 358 PA + 6 PA = 364 PA,
  también coincide exacto con `LIGA_BATTING`.
- **Abraham Almonte** (Piratas + Conspiradores, permalink `/501659`): SÍ es el mismo jugador (244 PA
  combinados), pero NO aparece en el `playerPool=QUALIFIED` en vivo de la LMB — no clasifica. Por
  regla del usuario ("si es jugador clasificado"), se queda sin este tratamiento, y con razón: no
  debe aparecer en "Toda la liga" en absoluto, con o sin traspaso.

**Cómo se implementó:** a los objetos de `Jesse Castillo` y `Roberto Valenzuela` dentro de
`LIGA_BATTING` se les agregó un campo `"teams": ["Equipo anterior", "Equipo actual"]` (el orden se
infirió por PA — el equipo con MENOS PA acumulados es presumiblemente donde llegó más tarde/está
ahora; no se verificó con fecha exacta de transacción, así que es una inferencia razonable, no un
hecho confirmado). `renderLigaBatTable` revisa si `d.teams` existe y tiene más de un elemento — si sí,
muestra `"Equipo A → Equipo B 🔁"` en vez del nombre plano de un solo equipo. Las pestañas por equipo
("Mi equipo") **no se tocaron** — a propósito, el usuario quiere que ahí siga mostrando solo lo que
el jugador hizo con ese equipo específico, no la temporada completa.

### Barrido completo (22-ago-2026) — ya hecho, no queda pendiente

El usuario pidió el barrido completo. Se hizo así:

1. Se jalaron los 20 rosters completos (`playerPool=ALL`, hitting + pitching) **con `permalink`
   incluido** (el primer jalón de Zona Sur/Norte no lo había guardado — el `flatten()` de esos
   scripts solo se quedaba con `name`+stats, no con `permalink`, así que hubo que re-fetchear todo).
2. Se agruparon por nombre a través de los 20 equipos. Salieron **79 nombres duplicados en bateo y
   94 en pitcheo** — mucho más de lo esperado, pero la LMB mueve bastante roster a media temporada
   (llamadas, salidas de extranjeros, etc.).
3. **Filtro clave: NO basta con que el nombre se repita.** Hay que comparar el `permalink` (ID único
   de jugador) entre las apariciones — si difiere, son dos personas distintas con el mismo nombre, no
   un traspaso. Se encontraron exactamente 2 falsos positivos así: **"Luis Medina"** y **"Carlos
   Pérez"** (cada uno con dos `permalink` distintos en dos equipos) — se descartaron, no son
   traspasos, son homónimos.
4. De los duplicados con `permalink` idéntico (traspaso real confirmado), se cruzó cada nombre
   contra `LIGA_BATTING`/`LIGA_PITCHING` — si el jugador no está ahí, no está clasificado, y por la
   regla del usuario no le toca el tratamiento (se descarta sin tocar nada, igual que Abraham
   Almonte). Para los que sí están clasificados, se sumó su PA/IP entre equipos y se comparó contra
   el PA/IP que ya trae `LIGA_BATTING`/`LIGA_PITCHING` como control de calidad — **las 39 coincidencias
   dieron exactas** (± 0.1 IP de redondeo en pitcheo), cero descartadas por no cuadrar.
5. **Resultado: 29 bateadores + 10 lanzadores clasificados con campo `"teams": [equipo anterior,
   equipo actual]`** agregado a sus objetos en `LIGA_BATTING`/`LIGA_PITCHING`. El equipo "actual" (el
   último del arreglo) es el que ya trae el campo `team` original — no es una suposición, es el que
   la propia LMB le asigna en el pool de calificados. El orden de los equipos ANTERIORES a ese sí es
   una inferencia (por PA/IP ascendente — menos acumulado se asume más reciente), no un hecho
   confirmado con fecha de transacción real; no se encontró una fuente de fechas de trades en la API.
6. `renderLigaBatTable` y `renderLigaPitTable` (antes solo el de bateo tenía el tratamiento) muestran
   `"Equipo A → Equipo B 🔁"` cuando `d.teams` existe con 2+ elementos. Las pestañas por equipo
   ("Mi equipo") siguen sin tocarse — muestran solo lo que el jugador hizo con ese equipo específico,
   a propósito.

**No queda nada pendiente de este barrido** — se cubrieron los 130+49 clasificados completos, no una
muestra. Si en un snapshot futuro hay más traspasos, hay que repetir los pasos 1-5 desde cero (no hay
manera de detectar traspasos nuevos sin volver a jalar los 20 rosters).

## 11. Clutch (Tarde/Cierre) — construido el 26-ago-2026

Después de corregir el hallazgo de `sitCodes` (ver sección 8.1), el usuario pidió construir algo con
esto. Se hizo:

**Fórmula:** `Clutch = ((wOBA_tarde/cierre − wOBA_temporada) / 1.20) × PA_tarde/cierre`, usando
`sitCodes=lc` (7ma entrada en adelante, marcador empatado/diferencia de 1/carrera del empate al menos
en el círculo de espera — la definición estándar de "clutch" en sabermetría, no una que se inventó
aquí). Compara al jugador contra **su propio** wOBA de temporada, no contra el promedio de liga —
mide si rindió mejor o peor que su propio nivel específicamente en los momentos de más presión.

**Por qué solo bateo, no pitcheo:** se probó con los 49 lanzadores calificados y la entrada máxima
acumulada en tarde/cierre fue de **4.0 IP en toda la temporada** (la mayoría, menos de 2). Los
calificados son abridores de alto volumen, y un abridor casi nunca sigue en el montículo para cuando
un partido llega a "tarde y cerrado" — eso es terreno de relevistas, que no acumulan suficiente IP
total para calificar. No hay forma honesta de calcularlo con estos datos. Para bateo el rango de PA en
tarde/cierre fue 11–51 — chico pero utilizable.

**Muestra mínima:** 20 PA en tarde/cierre para mostrar un número; por debajo, la celda muestra "—"
con tooltip ("muestra insuficiente"), no un valor fabricado. Con ese corte, 127 de 130 bateadores
calificados sí tienen dato.

**Dónde vive:** columna nueva "Clutch (T/C)" en la tabla de bateo de "Toda la liga" únicamente (no en
las pestañas por equipo — esto solo aplica a los clasificados, con el mismo alcance que la sección
10). Datos: `sitCodes=lc`, `playerPool=QUALIFIED`, `categoryType=hitting`, cruzado por nombre contra
`LIGA_BATTING` (mismo pool, no hizo falta verificar por `permalink` porque no es un cruce entre
equipos distintos, es el mismo jugador en el mismo pool con y sin el filtro situacional).

**Bug encontrado y corregido de paso:** los ~3 jugadores sin muestra suficiente (`clutchRuns`
`undefined`) rompían el `sort()` de **toda la tabla**, no solo esas filas — `undefined - número` da
`NaN`, y el comparador de `setupSort` no lo manejaba, dejando el arreglo mal ordenado de forma
silenciosa (sin error en consola). Se corrigió en `setupSort` (aplica a cualquier columna futura con
valores faltantes, no solo esta): los valores faltantes ahora siempre quedan al final,
independientemente de si el orden es ascendente o descendente.
