# Del orbital al espacio químico

> Manual de prácticas de química computacional  
> Eduardo Gabriel Guzmán-López · Miguel Reina  
> UNAM · Facultad de Química · Grupo Dra. Annia Galano

[![Deploy](https://github.com/Eduardo-Gabriel-Guzman-Lopez/computational-chemistry-book/actions/workflows/deploy-book.yml/badge.svg)](https://github.com/Eduardo-Gabriel-Guzman-Lopez/computational-chemistry-book/actions/workflows/deploy-book.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Libro en línea:** https://eduardo-gabriel-guzman-lopez.github.io/computational-chemistry-book/intro.html

---

## Estructura del repositorio

```
del-orbital-al-espacio-quimico/
│
├── tex/                    ← FUENTE DE VERDAD (archivos LaTeX)
│   ├── practica-01.tex
│   ├── practica-02.tex
│   └── ...practica-55.tex
│
├── notebooks/              ← GENERADO AUTOMÁTICAMENTE (no editar)
│   ├── p01.ipynb           ←  generado por tex2ipynb.py
│   ├── bloque01.md         ←  generado por gen_bloque_pages.py
│   └── ...
│
├── scripts/
│   ├── tex2ipynb.py        ← conversor LaTeX → Jupyter Notebook
│   └── gen_bloque_pages.py ← genera páginas intro de bloques
│
├── assets/                 ← imágenes, logo, favicon
├── anexos/                 ← Anexo A y B en Markdown
│   ├── anexo_a.md
│   ├── anexo_b.md
│   ├── glosario.md
│   └── referencias.md
│
├── _config.yml             ← configuración de Jupyter Book
├── _toc.yml                ← tabla de contenidos
├── intro.md                ← página de inicio del libro
├── prefacio.md             ← prefacio (generado desde prefacio.tex)
├── environment.yml         ← entorno conda para desarrollo local
│
└── .github/
    └── workflows/
        └── deploy.yml      ← GitHub Action: build + deploy automático
```

## Flujo de trabajo

**La fuente de verdad son los archivos `.tex` en `tex/`.**  
Los notebooks se generan automáticamente. Nunca edites los `.ipynb`
directamente; los cambios se perderán en el siguiente build.

```
# Editar una práctica
vim tex/practica-04.tex

# Probar la conversión localmente
python scripts/tex2ipynb.py tex/practica-04.tex -o notebooks/p04.ipynb

# Hacer push → el GitHub Action hace el resto
git add tex/practica-04.tex
git commit -m "P04: mejorar sección de análisis de resultados"
git push
```

El deploy tarda ~3 minutos. Puedes ver el progreso en la pestaña
**Actions** del repositorio.

## Desarrollo local

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/Eduardo-Gabriel-Guzman-Lopez/computational-chemistry-book.git
cd computational-chemistry-book
conda env create -f environment.yml
conda activate qcmanual-book
```

### 2. Convertir los .tex a notebooks

```bash
# Una práctica
python scripts/tex2ipynb.py tex/practica-01.tex -o notebooks/p01.ipynb

# Todas las prácticas de golpe
python scripts/tex2ipynb.py --all tex/ notebooks/
```

### 3. Build local del libro

```bash
jupyter-book build .
# Abrir en el navegador:
open _build/html/index.html    # macOS
xdg-open _build/html/index.html  # Linux
```

### 4. Limpiar el build

```bash
jupyter-book clean .
```

## Agregar una nueva práctica

1. Crear `tex/practica-NN.tex` siguiendo la plantilla en
   `tex/plantilla-practica-v2.tex`
2. Añadir la entrada correspondiente en `_toc.yml`
3. Actualizar `scripts/gen_bloque_pages.py` si es un bloque nuevo
4. Hacer push → el CI/CD hace el resto

## Convención de código dual ORCA / Gaussian

Para bloques de input que tienen versión dual, usar en el `.tex`:

```latex
\begin{orcablock}
! B3LYP def2-TZVP Opt
* xyz 0 1
O  0.000  0.000  0.000
...
\end{orcablock}

\begin{g16block}
# B3LYP/def2TZVP Opt
0 1
O  0.000  0.000  0.000
...
\end{g16block}
```

El conversor genera automáticamente las pestañas sincronizadas en el libro.

## Licencia

El contenido de este manual está bajo licencia
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
El código (scripts y notebooks) está bajo licencia MIT.

## Citar este trabajo

```bibtex
@book{guzman_reina_2025,
  title     = {Del orbital al espacio qu{\'i}mico:
               Manual de pr{\'a}cticas de qu{\'i}mica computacional},
  author    = {Guzm{\'a}n-L{\'o}pez, Eduardo Gabriel and Reina, Miguel},
  year      = {2025},
  publisher = {UNAM · Facultad de Qu{\'i}mica},
  url       = {https://eduardo-gabriel-guzman-lopez.github.io/computational-chemistry-book/intro.html}
}
```


# Computational Chemistry Laboratory Manual

A hands-on laboratory manual designed to teach modern computational
chemistry workflows.

## Overview

Computational Chemistry Laboratory Manual is a practical,
research-oriented guide designed to introduce students and researchers
to modern computational chemistry workflows.

Rather than focusing solely on how to operate specific software, the
manual emphasizes how computational calculations become part of a
broader chemical investigation.

## Structure of the Manual

The manual is organized as a sequence of guided practices that move
from fundamental tasks—such as molecular structure generation and
format conversion—to advanced topics including:

- electronic structure methods
- conformational exploration
- dataset construction
- chemical interpretation of computational results

## Pedagogical Approach

Each practice combines:

- a chemical problem or research question
- a seed computational experiment
- reproducible calculation inputs for programs such as Gaussian and ORCA
- automation scripts to explore chemical space
- dataset construction and analysis using Python

By scaling a single calculation into dozens or hundreds of related
calculations, the manual reflects the reality of contemporary
computational chemistry, where meaningful insights emerge from
systematic exploration of chemical space rather than isolated
simulations.

## Audience

The material is designed for:

- advanced undergraduate students
- graduate students
- researchers entering computational chemistry

## Tools Used

The practices make use of common computational chemistry tools,
including:

- Gaussian
- ORCA
- Python scientific libraries
- open-source cheminformatics software

## License

This work is licensed under the Creative Commons
Attribution–NonCommercial 4.0 International License.
