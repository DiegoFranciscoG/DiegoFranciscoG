# Investigación y fuentes

| # | Fuente (oficial / confiable) | URL | Consultada | Qué se tomó de aquí |
|---|---|---|---|---|
| 1 | GitHub Docs: Managing your profile README | https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-github-profile/customizing-your-profile/managing-your-profile-readme | 2026-09-27 | El README se muestra si el repo se llama igual que el usuario, es público y tiene `README.md` en la raíz. |
| 2 | GitHub Docs: Basic writing and formatting syntax | https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax | 2026-09-27 | `<picture>` con `prefers-color-scheme` para imágenes de tema claro y oscuro; rutas relativas para imágenes del repo. |
| 3 | GitHub Docs: Viewing a project's contributors | https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-a-projects-contributors | 2026-09-27 | Los contribuidores salen de los commits de la rama por defecto e incluyen a los coautores declarados en el mensaje del commit; tras reescribir historial los datos tardan unas 24 horas en refrescarse. |
| 4 | GitHub Docs: Creating a commit with multiple authors | https://docs.github.com/en/pull-requests/committing-changes-to-your-project/creating-and-editing-commits/creating-a-commit-with-multiple-authors | 2026-09-27 | Cada línea de coautor en el mensaje acredita a otra cuenta; por eso los commits se firman solo con la identidad del autor y sin líneas de coautor. |
| 5 | GitHub Docs: Rate limits for the REST API | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api | 2026-09-27 | 60 peticiones por hora sin autenticar; 1000 por hora por repositorio con `GITHUB_TOKEN` en Actions. El script usa una petición por repo más la lista. |
| 6 | GitHub Docs: Disabling and enabling a workflow | https://docs.github.com/en/actions/managing-workflow-runs-and-deployments/managing-workflow-runs/disabling-and-enabling-a-workflow | 2026-09-27 | En repos públicos los workflows programados se desactivan tras 60 días sin actividad; se puede reactivar o lanzar a mano (`workflow_dispatch`). |
| 7 | github-linguist: languages.yml | https://github.com/github-linguist/linguist/blob/main/lib/linguist/languages.yml | 2026-09-30 | Colores por lenguaje para que la tarjeta coincida con la barra de GitHub. |
| 8 | Releases oficiales de actions/checkout y actions/setup-python | https://github.com/actions/checkout/releases · https://github.com/actions/setup-python/releases | 2026-09-30 | Versiones estables v7.0.1 y v7.0.0, fijadas por SHA. |
| 9 | PyPI: pytest, pytest-cov y ruff | https://pypi.org/project/pytest/ · https://pypi.org/project/pytest-cov/ · https://pypi.org/project/ruff/ | 2026-09-30 | Versiones estables 9.1.1, 7.1.0 y 0.16.9. |
| 10 | RENAFIPSE | https://renafipse.ec/ | 2026-09-30 | Nombre oficial de la institución de las prácticas: Red Nacional de Finanzas Populares y Solidarias del Ecuador. |

## Supuestos (no verificados)
- Ninguno. Los datos de proyectos, formación y certificaciones salen de los repositorios y del CV del autor; cada certificación enlaza a su verificación oficial.
