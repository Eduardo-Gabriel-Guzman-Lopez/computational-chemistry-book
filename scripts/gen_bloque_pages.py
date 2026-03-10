#!/usr/bin/env python3
"""
gen_bloque_pages.py
===================
Genera automáticamente los archivos notebooks/bloqueXX.md
que sirven como páginas de introducción de cada bloque en
el Jupyter Book. Extrae el título y descripción del bloque
desde el _toc.yml para mantener consistencia.

Se ejecuta durante el GitHub Action, antes del build.
"""

import re, yaml
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Descripciones cortas de cada bloque
# (editar aquí si cambia el contenido del manual)
BLOQUES = {
    1:  ("Generación de estructuras y espacio conformacional",
         "Transforma SMILES en geometrías 3D ejecutables, explora "
         "tautomería y microespacio de protonación, y genera el "
         "bosque conformacional con CREST/GFN2-xTB."),
    2:  ("Métodos de estructura electrónica",
         "Compara HF y DFT en sistemas pequeños, analiza el efecto "
         "del funcional sobre propiedades observables, y diagnostica "
         "problemas de convergencia SCF en capa abierta."),
    3:  ("Conjuntos de base y precisión computacional",
         "Construye curvas de convergencia con familias Pople, Dunning "
         "y Karlsruhe, introduce pseudopotenciales para elementos pesados, "
         "y cuantifica el error BSSE en complejos moleculares."),
    4:  ("Topología de la superficie de energía potencial",
         "Optimiza mínimos y estados de transición, valida con "
         "análisis frecuencial, y escanea la coordenada de reacción "
         "para construir perfiles de energía."),
    5:  ("Diagnóstico de fallas electrónicas",
         "Detecta contaminación de espín en radicales, evalúa ruptura "
         "de simetría, y realiza una introducción operativa a CASSCF "
         "para sistemas multireferenciales."),
    6:  ("Correlación electrónica post-HF",
         "Ejecuta benchmarks metodológicos MP2/CCSD(T) vs DFT, construye "
         "curvas de error en series homólogas, y comprende la relación "
         "exactitud–costo computacional."),
    7:  ("Análisis de la función de onda",
         "Aplica NBO para cuantificar transferencia de carga, QTAIM "
         "para topología de densidad electrónica, y NCI para "
         "visualizar interacciones no covalentes."),
    8:  ("Reactividad y descriptores DFT conceptual",
         "Calcula índices de Fukui, dureza y blandura globales, "
         "descriptores de electrofilia/nucleofilia local, y "
         "aplica el concepto de doble reactividad."),
    9:  ("Espectroscopía computacional",
         "Asigna modos normales en espectros IR/Raman, predice "
         "desplazamientos químicos de RMN, y simula espectros "
         "UV-Vis mediante TD-DFT."),
    10: ("Termodinámica y solvatación",
         "Calcula entalpías y energías de Gibbs de reacción, "
         "estima pKa computacional, y evalúa energías de "
         "solvatación con modelos PCM y SMD."),
    11: ("Cinética computacional",
         "Aplica la Teoría del Estado de Transición para obtener "
         "constantes de velocidad, incluye la corrección túnel "
         "de Eckart, y calcula el índice de eficiencia catalítica "
         "de Kozuch–Shaik."),
    12: ("Catálisis organometálica",
         "Caracteriza ligandos mediante el ángulo de cono de Tolman "
         "y el volumen sepultado %V_bur, y construye perfiles "
         "energéticos de ciclos catalíticos completos."),
    13: ("Catálisis heterogénea con DFT periódico",
         "Calcula energías de adsorción en superficies con VASP/QE, "
         "construye diagramas de Brønsted–Evans–Polanyi, "
         "y modela difusión con CI-NEB."),
    14: ("Complejos de metales de transición",
         "Genera automáticamente geometrías de complejos con "
         "molSimplify, analiza el campo ligante y el splitting d, "
         "y estudia energías de cruce entre estados de espín."),
    15: ("Dinámica molecular clásica",
         "Ejecuta el protocolo completo de MD con GROMACS "
         "(parametrización AMBER ff14SB/GAFF2, equilibración, "
         "producción), analiza trayectorias con MDAnalysis "
         "y realiza clustering conformacional de Daura."),
    16: ("Docking molecular",
         "Prepara receptor y ligando con Meeko, ejecuta docking "
         "con AutoDock Vina 1.2, valida poses con criterios "
         "de RMSD y puentes de hidrógeno, y realiza cribado "
         "virtual sobre una biblioteca de candidatos."),
    17: ("Exploración del espacio químico",
         "Enumera bibliotecas virtuales por sustitución sistemática "
         "de scaffolds, filtra con reglas ADMET, y proyecta el "
         "espacio químico en mapas UMAP interactivos."),
    18: ("Quimioinformática aplicada",
         "Calcula y limpia descriptores moleculares 2D, genera "
         "fingerprints ECFP4 y MACCS, aplica similitud "
         "Tanimoto y clustering jerárquico para análisis "
         "de diversidad estructural."),
    19: ("Aprendizaje automático aplicado a química",
         "Aplica PCA para interpretar el espacio de descriptores, "
         "construye modelos QSAR/QSPR con validación cruzada "
         "y gráfico de Williams, y entrena una GNN para "
         "predicción de afinidad proteína–ligando."),
    20: ("Diseño molecular asistido por inteligencia artificial",
         "Prioriza candidatos con función de desirabilidad "
         "multicriterio y frontera de Pareto, y genera "
         "moléculas de novo con modelos REINVENT (Prior RNN + "
         "RL) filtrando con score compuesto y docking real."),
}

SECCIONES = {
    range(1,  7):  "Parte I · Fundamentos y estructura electrónica",
    range(7,  11): "Parte II · Análisis de propiedades y reactividad",
    range(11, 17): "Parte III · Mecanismos y sistemas complejos",
    range(17, 21): "Parte IV · Espacio químico e inteligencia artificial",
}

def seccion_de(n):
    for rng, sec in SECCIONES.items():
        if n in rng:
            return sec
    return ""

def practicas_del_bloque(n):
    """Devuelve los números de práctica de un bloque."""
    # Mapa fijo basado en la arquitectura del manual
    mapa = {
        1:[1,2,3], 2:[4,5,6], 3:[7,8,9], 4:[10,11,12],
        5:[13,14,15], 6:[16,17,18], 7:[19,20,21], 8:[22,23,24],
        9:[25,26,27], 10:[28,29,30], 11:[31,32,33], 12:[34,35,36],
        13:[37,38,39], 14:[40,41,42], 15:[43,44,45], 16:[46],
        17:[47,48], 18:[49,50], 19:[51,52,53], 20:[54,55],
    }
    return mapa.get(n, [])

def bloques_en_toc():
     toc_path = REPO_ROOT / '_toc.yml'
     if not toc_path.exists():
          return []

     data = yaml.safe_load(toc_path.read_text(encoding='utf-8')) or {}
     found = set()

     def walk(node):
          if isinstance(node, dict):
               file_ref = node.get('file')
               if isinstance(file_ref, str):
                    m = re.search(r'notebooks/bloque(\d{2})$', file_ref)
                    if m:
                         found.add(int(m.group(1)))
               for key in ('parts', 'chapters', 'sections'):
                    if key in node:
                         walk(node[key])
          elif isinstance(node, list):
               for item in node:
                    walk(item)

     walk(data)
     return sorted(found)

def generar_pagina_bloque(n, titulo, descripcion):
    practicas = practicas_del_bloque(n)
    links_md = '\n'.join(
        f'- {{doc}}`P{p:02d} <p{p:02d}>`' for p in practicas)
    seccion = seccion_de(n)
    return f"""\
# Bloque {n}: {titulo}

> **{seccion}**

{descripcion}

## Prácticas de este bloque

{links_md}

---

```{{admonition}} Modelo Semilla y Bosque
:class: tip

Cada práctica de este bloque sigue el mismo patrón:
un **cálculo semilla** ejecutado por el estudiante
que valida el nivel de teoría, seguido de la expansión
a un **bosque** de datos pre-calculado para análisis estadístico.
```
"""

def main():
     out_dir = REPO_ROOT / 'notebooks'
     out_dir.mkdir(exist_ok=True)

     bloques_objetivo = bloques_en_toc()
     if not bloques_objetivo:
          print('ℹ No hay bloques `notebooks/bloqueXX` en _toc.yml; no se generan páginas de bloque.')
          return

     generados = 0

     for n in bloques_objetivo:
          if n not in BLOQUES:
               print(f'⚠ Bloque {n:02d} aparece en _toc.yml pero no está definido en BLOQUES.')
               continue

          titulo, desc = BLOQUES[n]
          contenido = generar_pagina_bloque(n, titulo, desc)
          ruta = out_dir / f'bloque{n:02d}.md'
          ruta.write_text(contenido, encoding='utf-8')
          print(f'✓  {ruta}')
          generados += 1

     print(f'\n{generados} páginas de bloque generadas (según _toc.yml).')

if __name__ == '__main__':
    main()
