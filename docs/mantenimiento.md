# Mantenimiento del perfil

## Estructura
| Ruta | Contenido |
|---|---|
| `README.md` | Lo que GitHub muestra en el perfil. |
| `assets/banner-*.svg` | Encabezado en tema claro y oscuro. |
| `assets/projects/` | Capturas de cada proyecto (800×500, sin metadatos) y portadas SVG de los que aún no tienen interfaz. |
| `assets/languages-*.svg` | Tarjetas de lenguajes generadas por `scripts/profile_stats.py`. |
| `.github/workflows/stats.yml` | Regenera las tarjetas cada lunes y hace commit solo si cambian los datos. |

## Regenerar las tarjetas en local
```bash
python -m venv .venv && .venv/Scripts/activate      # en Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python -m scripts.profile_stats --out-dir assets   # opcional: GITHUB_TOKEN para más límite
```
`--exclude "HTML,CSS"` omite lenguajes si alguna vez se quiere mostrar solo código de aplicación.

## Tests y calidad
```bash
ruff check . && ruff format --check .
pytest            # cobertura mínima 90 % del script
```

## Agregar un proyecto destacado
1. Guarda una captura 800×500 en `assets/projects/<repo>.jpg` sin metadatos.
2. Añade una celda a la tabla de «Proyectos destacados» con la imagen, el enlace, una frase de valor y el stack.
3. Mantén un número par de celdas para que la tabla quede alineada.

## Si el workflow programado se detiene
GitHub desactiva los workflows programados de repos públicos tras 60 días sin actividad. Reactívalo en **Actions → Estadísticas del perfil → Enable workflow** o ejecútalo con **Run workflow**.
