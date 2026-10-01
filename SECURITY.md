# Política de seguridad

## Reportar una vulnerabilidad
No abras un issue público. Escríbeme por GitHub (perfil DiegoFranciscoG) o por LinkedIn con los pasos para reproducir el problema. Respondo en un máximo de 7 días.

## Prácticas aplicadas en este repositorio
- El script de estadísticas solo usa la biblioteca estándar de Python y solo acepta URL de `https://api.github.com`.
- El token es opcional y llega por variable de entorno: en GitHub Actions es el `GITHUB_TOKEN` temporal del workflow, nunca uno personal.
- Las tarjetas son SVG estáticos generados en el repositorio: el perfil no depende de widgets externos ni expone tokens.
- Workflows con `permissions` mínimos y acciones fijadas por SHA; Dependabot las mantiene al día.
- Escaneo de secretos con gitleaks en cada push y pull request.
- Las imágenes no llevan metadatos EXIF ni de ubicación.
