# Práctica 1: Transformación de formatos a coordenadas tridimensionales. Grafos moleculares y representaciones químicas

```{admonition} Metadatos de la práctica
:class: note
**Bloque temático**: 1 – Generación de estructuras y espacio conformacional  
**Número de práctica**: 1  
**Nivel de dificultad**: Básico  
**Tiempo estimado**: 1 h (semilla) + 2 h (bosque y análisis)  
**Modalidad**: Individual  
**Pipeline central**: SMILES → grafo molecular → geometría 3D (ETKDG) → pre-opt FF (MMFF94) → opt semiempírica (GFN2-xTB) → dataset estructural  
**Hardware mínimo**: 2 GB RAM, procesador de doble núcleo ≥ 1.5 GHz (laptop de 2012 o posterior)  
**Modo sin conexión**: Parcial — internet requerida solo para instalación inicial  
**Acceso en nube**: [Colab P01](https://colab.research.google.com/drive/p01_cafeina)
```

## Introducción

Antes de realizar cualquier cálculo cuántico, una molécula debe existir como un objeto computacional con coordenadas tridimensionales explícitas. Este paso, aparentemente trivial, encierra decisiones metodológicas con consecuencias directas sobre la calidad de todos los cálculos posteriores: una geometría inicial mal construida puede converger a un mínimo incorrecto, producir frecuencias imaginarias espurias o generar resultados numéricos que no corresponden a ninguna especie química real.

La representación más común en quimioinformática es el **SMILES** (*Simplified Molecular Input Line Entry System*), una cadena de texto que codifica la conectividad molecular mediante reglas gramaticales precisas. Un SMILES como `CC(=O)Nc1ccccc1` describe sin ambigüedad la acetanilida; sin embargo, no contiene información sobre los ángulos de enlace, las longitudes de enlace ni la disposición espacial de los átomos. Pasar de esa cadena lineal a un conjunto de coordenadas cartesianas $(x_i, y_i, z_i)$ es el problema que resuelve esta práctica.

Las herramientas modernas —principalmente RDKit y OpenBabel— implementan algoritmos de incrustación tridimensional que combinan reglas geométricas empíricas, campos de fuerza y, en el caso del algoritmo ETKDG (*Experimental-Torsion distance geometry with basic Knowledge*), distribuciones de ángulos diedros extraídas de la Cambridge Structural Database. El resultado es una geometría de partida razonable en pocos milisegundos, sin importar el tamaño de la molécula.

Una vez disponible la geometría inicial, la práctica introduce el primer pipeline del manual: pre-optimización con un campo de fuerza (MMFF94) seguida de optimización semiempírica con GFN2-xTB. Este protocolo de dos pasos es suficiente para la mayoría de las moléculas orgánicas pequeñas y medianas, y constituye el punto de partida estándar para los cálculos de estructura electrónica del Bloque 2.

En términos del modelo Semilla–Bosque: la **semilla** es la construcción y optimización de una molécula sencilla que el estudiante ejecuta por sí mismo. El **bosque** es un dataset de 50 moléculas orgánicas con diversidad estructural —aromáticos, heteroaromáticos, sistemas flexibles y casos difíciles— para los cuales el mismo pipeline ya fue ejecutado. El análisis del bosque permite identificar qué características estructurales hacen que la incrustación 3D sea más o menos confiable, y cómo la energía de pre-optimización se correlaciona con descriptores topológicos básicos.

## Marco teórico

### Conceptos clave

**1. Representaciones moleculares y su jerarquía informacional.**  
Una molécula puede codificarse en distintos niveles de detalle. La fórmula molecular (0D) sólo indica composición. El SMILES o InChI (1D) codifican la conectividad y el orden de enlace. El grafo 2D añade estereoquímica plana. Las coordenadas cartesianas 3D son las únicas que permiten calcular propiedades que dependen de la geometría (energías, frecuencias, densidades electrónicas). Cada nivel es una proyección: al bajar de 3D a 1D se pierde información irreversiblemente.

**2. Geometría de distancias (DG) e incrustación 3D.**  
El algoritmo ETKDG convierte un grafo molecular en coordenadas cartesianas resolviendo un problema de optimización sobre matrices de distancias interatómicas. Los límites de cada distancia se obtienen de tres fuentes: reglas de enlace covalente, restricciones de no-penetración van der Waals, y distribuciones estadísticas de ángulos diedros extraídas de estructuras cristalinas. El resultado no es único: distintas semillas aleatorias producen geometrías de partida diferentes, todas igualmente válidas como punto de inicio.

**3. Campos de fuerza (FF) y su rol como pre-optimizadores.**  
Un campo de fuerza es una función de energía potencial empírica que describe la energía como suma de contribuciones de enlace, ángulo, torsión e interacciones no covalentes. MMFF94 está parametrizado para moléculas orgánicas pequeñas y es adecuado para corregir geometrías iniciales ETKDG. No es apropiado para describir reacciones, rupturas de enlace o sistemas con metales de transición.

**4. Métodos semiempíricos ajustados (GFN2-xTB).**  
GFN2-xTB es un método de enlace fuerte autoconsistente (*tight-binding*) parametrizado para reproducir geometrías y energías de conformación de moléculas orgánicas e inorgánicas con precisión comparable a DFT/def2-SVP, pero con un costo computacional 3–4 órdenes de magnitud menor. La energía total contiene contribuciones electrónicas, de dispersión (D4) y de repulsión nuclear. No es apropiado para excitaciones electrónicas ni para propiedades que requieren descripción explícita de la función de onda.

**5. RMSD como métrica de similitud geométrica.**  
El RMSD (*Root Mean Square Deviation*) entre dos geometrías se define como:

$$\mathrm{RMSD} = \sqrt{\frac{1}{N}\sum_{i=1}^{N}\left|\mathbf{r}_i^{(A)} - \mathbf{r}_i^{(B)}\right|^2}$$

donde $N$ es el número de átomos y los vectores $\mathbf{r}_i$ son las coordenadas de cada átomo tras la superposición óptima. Un RMSD < 0.5 Å entre la geometría calculada y el cristal indica reproducción aceptable.

### Preguntas previas

Responde estas preguntas **en tu cuaderno** antes de leer las secciones posteriores. No existe una única respuesta correcta; el objetivo es registrar tu razonamiento previo y compararlo después con los resultados reales.

1. **(Conceptual)** El SMILES de la cafeína no contiene coordenadas. Sin embargo, tú ya sabes que la cafeína tiene un anillo purínico. ¿Cómo "sabe" el algoritmo ETKDG que ese anillo debe ser plano? ¿Qué pasaría si la molécula tuviera un anillo que no aparece frecuentemente en la CSD?

2. **(Predictivo)** El campo de fuerza MMFF94 fue desarrollado principalmente para moléculas orgánicas con C, H, N, O, S. La cafeína tiene cuatro átomos de nitrógeno en distintos entornos. ¿Esperas que MMFF94 describa bien todos esos entornos? ¿Cuál crees que será el enlace con mayor error antes de la corrección xTB?

3. **(Crítico)** El bosque de esta práctica incluye diez "casos difíciles": moléculas muy tensionadas como el cubano o espiro-compuestos. ¿Por qué crees que la incrustación automática podría fallar en esos sistemas? ¿Qué alternativa propondrías para construir su geometría?

### Recursos de consulta rápida

- **RDKit Getting Started (en línea, inglés):** https://www.rdkit.org/docs/GettingStartedInPython.html — cubre los módulos `Chem`, `AllChem` y `rdMolDescriptors`.

- **Tutorial xTB (en línea, inglés):** https://xtb-docs.readthedocs.io/en/latest/setup.html — instalación, opciones de línea de comandos y ejemplos.

- **Química computacional sin matemáticas, Lewars (2024):** Capítulo 2 (representaciones moleculares) y Capítulo 3 (campos de fuerza).

- **Dataset público QM9:** https://doi.org/10.6084/m9.figshare.978904 — 133,885 moléculas orgánicas pequeñas con geometrías DFT.

## Objetivos de aprendizaje

### Conceptuales

- Distinguir entre representaciones moleculares 0D, 1D, 2D y 3D, e identificar qué información contiene y qué omite cada una.
- Explicar el principio del algoritmo ETKDG y por qué produce geometrías diferentes con distintas semillas aleatorias.
- Justificar el protocolo FF → xTB como compromiso entre velocidad y calidad para el punto de partida de cálculos DFT.

### Procedimentales

- Instalar y usar RDKit y xtb desde un script de Python y desde la línea de comandos.
- Convertir entre formatos moleculares (`.smi`, `.xyz`, `.sdf`) usando RDKit y OpenBabel.
- Ejecutar una optimización GFN2-xTB, verificar la convergencia en el log y extraer la geometría resultante.
- Visualizar y comparar estructuras 3D en Avogadro2 o py3Dmol.

### Investigación y datos

- Construir un dataset de 50 moléculas con variables: SMILES, número de átomos pesados, enlaces rotativos, energía GFN2-xTB, tiempo de optimización y éxito/fallo de incrustación.
- Identificar qué clases estructurales presentan mayor tasa de fallo en la incrustación 3D automática.
- Correlacionar la energía de la geometría optimizada con descriptores topológicos del bosque.

## Recursos y prerrequisitos

### Conocimientos previos

- **(Necesario)** Nomenclatura IUPAC de orgánicos bás icos.
- **(Necesario)** Enlace covalente, hibridación y geometría molecular (TRPEV/VSEPR).
- **(Necesario)** Terminal de Linux/macOS: navegar directorios, ejecutar scripts, redirigir salida.
- **(Necesario)** Python: variables, listas, bucles `for`, importar módulos.
- **(Recomendable)** Haber leído el Capítulo 1 del manual (Estructura y flujos de trabajo).

```{admonition} Primera práctica del manual
**No se asumen conocimientos previos de química computacional.** Si nunca has usado la terminal, completa primero el tutorial `docs/terminal_basica.md` del repositorio del curso (tiempo estimado: 30 min).
```

### Software

- **Python** ≥ 3.10 con `rdkit` ≥ 2023.03, `numpy`, `pandas`, `matplotlib`, `seaborn`.
  ```bash
  conda env create -f environment_p01.yml
  conda activate qc-manual
  ```

- **xtb** ≥ 6.6 — open-source, gratuito (LGPL-3).
  ```bash
  conda install -c conda-forge xtb
  ```

- **OpenBabel** ≥ 3.1 — open-source, gratuito (GPL-2).
  ```bash
  conda install -c conda-forge openbabel
  ```

- **Avogadro2** o **py3Dmol** — visualización 3D, ambos gratuitos y multiplataforma.

```{admonition} No requiere software comercial
**Esta práctica no requiere Gaussian, ORCA ni ningún software comercial.** Todo el pipeline (ETKDG + MMFF94 + GFN2-xTB) se ejecuta con herramientas completamente open-source.
```

```{admonition} ¿Sin acceso a software local?
El notebook de Google Colab incluye toda la instalación automatizada. No requiere configuración previa: https://colab.research.google.com/drive/p01_cafeina
```

### Archivos proporcionados

- `p01_semilla.py` — script base para la semilla.
- `p01_bosque_smiles.csv` — 50 SMILES con nombre y clase estructural.
- `p01_bosque_resultados.csv` — dataset pre-calculado.
- `p01_analisis.py` — script base de análisis.
- `environment_p01.yml` — entorno conda reproducible.
- `p01_colab.ipynb` — notebook para Google Colab.

### Recursos computacionales y accesibilidad

```{admonition} Especificaciones técnicas
**Semilla — CPU**: < 2 min en 1 núcleo (laptop estándar)  
**Bosque — CPU**: ≈ 15 min en 1 núcleo (pre-calculado)  
**RAM mínima absoluta**: 2 GB  
**Espacio en disco**: < 50 MB  
**Modo sin conexión**: Sí, una vez instalado el entorno conda  
**Acceso en nube**: [Colab P01](https://colab.research.google.com/drive/p01_cafeina)
```

```{admonition} Accesibilidad
**Todos los scripts de análisis generan figuras con etiquetas textuales en ejes y títulos descriptivos, compatibles con lectores de pantalla.** Las tablas de resultados se exportan como CSV con nombres de columna en español. Para adaptaciones específicas (discapacidad visual, daltonismo, etc.), consulta `docs/accesibilidad.md` en el repositorio del curso.
```

## Experimento semilla

### Sistema modelo

La semilla de esta práctica es la **cafeína** (`Cn1cnc2c1c(=O)n(c(=O)n2C)C`, CAS 58-08-2), elegida por cuatro razones simultáneas:

1. Tiene 24 átomos pesados — pequeña pero no trivial.
2. Posee un núcleo heterocíclico aromático y grupos carbonilo que ponen a prueba el campo de fuerza.
3. Su estructura cristalina está bien determinada por difracción de rayos X, permitiendo validación cuantitativa.
4. Es una molécula que todos los estudiantes conocen, facilitando la conexión con la intuición química previa.

### Pregunta química concreta

> ¿La geometría generada automáticamente mediante ETKDG + MMFF94 + GFN2-xTB reproduce las longitudes y ángulos de enlace del cristal de cafeína con un error medio < 1.5 %? ¿Qué región de la molécula muestra la mayor desviación, y a qué se debe?

### Nivel de teoría

```{admonition} Teoría y métodos
**Método de incrustación**: ETKDG v3 (RDKit 2023)  
**Campo de fuerza**: MMFF94 (pre-optimización)  
**Método semiempírico**: GFN2-xTB (optimización final)  
**Solvente**: Vacío (fase gas)  
**Convergencia**: Gradiente RMS < 5 × 10⁻⁴ a.u. (`--opt tight`)  

GFN2-xTB reproduce longitudes de enlace de orgánicos con error medio < 0.01 Å respecto a DFT/def2-SVP, con costo 3–4 órdenes de magnitud menor.
```

### Hipótesis inicial

Basándome en las preguntas previas, espero que el anillo purínico sea plano (o casi plano) en la geometría GFN2-xTB, porque los sistemas aromáticos están sobrerrepresentados en la CSD y el algoritmo ETKDG los reconoce bien. El mayor error debería aparecer en los grupos metilo ($-$CH₃), cuya posición rotacional tiene energía plana y el algoritmo puede colocar en una orientación sub-óptima. Esta hipótesis será verificable comparando el RMSD de los C del anillo frente al RMSD de los carbonos de los metilos respecto al cristal.

## Protocolo computacional

El protocolo consta de **6 pasos principales** que transforman una cadena SMILES en una geometría 3D optimizada:

![Pipeline: SMILES → Geometría 3D optimizada](../assets/images/diagram_P01.png)

### Detalles de cada paso:

### Paso 1: Construir el grafo molecular

```{code-cell} ipython3
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from rdkit.Chem import rdMolDescriptors

# SMILES para cafeína
smiles = 'Cn1cnc2c1c(=O)n(c(=O)n2C)C'
nombre = 'cafeina'

# Crear objeto molecular y verificar
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise ValueError(f'SMILES inválido: {smiles}')

# Información del grafo
print(f'Átomos totales:    {mol.GetNumAtoms()}')
print(f'Átomos pesados:    {mol.GetNumHeavyAtoms()}')
print(f'Fórmula:           {rdMolDescriptors.CalcMolFormula(mol)}')
print(f'Peso molecular:    {rdMolDescriptors.CalcExactMolWt(mol):.4f} Da')
print(f'Enlaces rotativos: {rdMolDescriptors.CalcNumRotatableBonds(mol)}')
```

### Paso 2: Visualizar la estructura 2D

```{code-cell} ipython3
# Generar representación 2D
Draw.MolToImage(mol, size=(400, 300))
```

### Paso 3: Incrustación 3D con ETKDG

```{code-cell} ipython3
import random
random.seed(42)  # Reproducibilidad

# Añadir hidrógenos explícitos
mol_h = Chem.AddHs(mol)

# Incrustación con ETKDG
params = AllChem.ETKDGv3()
params.randomSeed = 42
resultado = AllChem.EmbedMolecule(mol_h, params)

if resultado == -1:
    raise RuntimeError('Falló la incrustación 3D. '
                       'Verifica SMILES o usa maxAttempts=200.')

print('¡Incrustación exitosa!')
print(f'Número de átomos (con H): {mol_h.GetNumAtoms()}')
```

### Paso 4: Pre-optimización con campo de fuerza MMFF94

```{code-cell} ipython3
# Pre-optimización con MMFF94
props = AllChem.MMFFGetMoleculeProperties(mol_h)
ff = AllChem.MMFFGetMoleculeForceField(mol_h, props)

if ff is None:
    # Alternativa si MMFF94 no está parametrizado
    print('MMFF94 no disponible, usando UFF.')
    ff = AllChem.UFFGetMoleculeForceField(mol_h)

conv = ff.Minimize(maxIts=2000)
e_ff = ff.CalcEnergy()
print(f'Energía MMFF94 tras optimización: {e_ff:.4f} kcal/mol')
print(f'Convergencia (0=OK): {conv}')
```

### Paso 5: Visualización 3D con py3Dmol

```{code-cell} ipython3
import py3Dmol
from rdkit.Chem import rdmolfiles

# Convertir a bloque MOL para visualización
mol_block = rdmolfiles.MolToMolBlock(mol_h)

# Crear visor 3D
visor = py3Dmol.view(width=500, height=400)
visor.addModel(mol_block, 'mol')
visor.setStyle({'stick': {'colorscheme': 'Jmol'}})
visor.setBackgroundColor('white')
visor.zoomTo()
visor.show()
```

### Paso 6: Exportar para optimización semiempírica

```{code-cell} ipython3
# Guardar archivo XYZ para optimización xTB
from rdkit.Chem import rdmolfiles
rdmolfiles.MolToXYZFile(mol_h, 'cafeina_FF.xyz')
print("Archivo cafeina_FF.xyz guardado")
```

Luego, desde terminal:

```bash
xtb cafeina_FF.xyz --opt tight --chrg 0 --uhf 0 --gfn 2 > cafeina_xtb.out
```

Para verificar convergencia:

```bash
grep "GEOMETRY OPTIMIZATION CONVERGED" cafeina_xtb.out
```

La geometría optimizada se guarda en `xtbopt.xyz`. Parámetros clave:

- `--opt tight`: Criterio de convergencia más estricto (recomendado para puntos de partida DFT)
- `--chrg 0`: Carga molecular total
- `--uhf 0`: Número de electrones sin aparear (0 para capa cerrada)
- `--gfn 2`: Solicita explícitamente el método GFN2-xTB

## Control de calidad y validación

### Criterios de convergencia

```{admonition} Convergencia xTB
**Mensaje de convergencia**: `GEOMETRY OPTIMIZATION CONVERGED` en el log  
**Gradiente RMS (tight)**: < 2 × 10⁻⁴ Hartree/Bohr  
**Desplazamiento RMS**: < 4 × 10⁻⁴ Bohr  
**Frecuencias imaginarias**: 0 (verificar opcionalmente con `xtb --hess`)
```

### Diagnósticos estructurales

Verificar que la geometría optimizada satisfaga:

- **Planaridad del anillo**: RMSD de los átomos del anillo respecto al plano de mínimos cuadrados < 0.05 Å.
- **Longitudes de enlace características**:
  - C=O carbonilo: 1.20 ± 0.02 Å
  - C–N aromático: 1.33 ± 0.03 Å
  - C–N metilo: 1.46 ± 0.02 Å
- **Sin colisiones**: distancia mínima entre no enlazados > 2.0 Å.
- **Hidrógenos en posición escalonada** respecto al enlace C–N adyacente.

### Validación frente a la estructura cristalina

La estructura cristalina de la cafeína monohidrato fue determinada por difracción de rayos X (CSD: CAFINE01). Completar la tabla y calcular el error porcentual:

| Enlace | Exp. (Å) | Calc. (Å) | Error (%) |
|--------|----------|-----------|-----------|
| C8=O1  | 1.235    | …         | …         |
| C2=O3  | 1.239    | …         | …         |
| N1–C8  | 1.374    | …         | …         |
| N3–C4  | 1.327    | …         | …         |
| **Error medio** | | | … |

Se acepta el resultado si el error medio < 1.5 %.

## Expansión del espacio químico (el bosque)

### Estrategia de expansión

El bosque contiene 50 moléculas orgánicas en cinco clases:

- **Aromáticos carbocíclicos** (10): benceno, naftaleno, antraceno, pireno y derivados sustituidos.
- **Heteroaromáticos** (10): piridina, imidazol, tiofeno, indol, quinolina y análogos.
- **Moléculas flexibles** (10): alcanos lineales C₆–C₁₂, aminoácidos, dipéptidos.
- **Sistemas con puentes de H intramolecular** (10): salicilaldehído, ácido 2-aminobenzoico y análogos.
- **Casos difíciles** (10): espiro-compuestos, cubano, biciclo[1.1.0]butano y sistemas con estereoquímica compleja.

### Dataset pre-calculado

El bosque completo se proporciona en `p01_bosque_resultados.csv`. El dataset incluye columnas:

```python
columnas = {
    'id': 'Identificador de molécula',
    'smiles': 'Cadena SMILES',
    'clase': 'Categoría estructural',
    'n_heavy': 'Número de átomos pesados',
    'n_rot_bonds': 'Número de enlaces rotativos',
    'mw': 'Peso molecular (Da)',
    'embed_ok': 'Éxito de incrustación (1/0)',
    'e_ff_kcalmol': 'Energía MMFF94 (kcal/mol)',
    'e_xtb_hartree': 'Energía GFN2-xTB (Hartree)',
    't_xtb_s': 'Tiempo de optimización xTB (s)'
}
```

## Construcción del dataset

Integrar la semilla (cafeína) con el bosque:

```{code-cell} ipython3
import pandas as pd

df = pd.read_csv('p01_bosque_resultados.csv')

semilla = {
    'id': 'cafeina',
    'smiles': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
    'clase': 'heteroaromatico',
    'n_heavy': 24,
    'n_rot_bonds': 3,
    'mw': 194.0804,
    'embed_ok': 1,
    'e_ff_kcalmol': ...,  # Completar con tu valor
    'e_xtb_hartree': ..., # Completar con tu valor
    't_xtb_s': ...,       # Completar con tu valor
}

df_final = pd.concat([df, pd.DataFrame([semilla])], ignore_index=True)
df_final.to_csv('p01_dataset_final.csv', index=False)
print(df_final.tail(3))
```

## Análisis de resultados

### Estadística descriptiva

```{code-cell} ipython3
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('p01_dataset_final.csv')
print(df[['n_heavy','n_rot_bonds','e_xtb_hartree','t_xtb_s']].describe().round(4))
print(f"Tasa de éxito: {df['embed_ok'].mean()*100:.1f}%")

# Gráfico: tiempo vs tamaño
df_ok = df[df['embed_ok'] == 1]
fig, ax = plt.subplots(figsize=(6, 4))
sc = ax.scatter(df_ok['n_heavy'], df_ok['t_xtb_s'],
                c=df_ok['n_rot_bonds'], cmap='viridis',
                edgecolors='k', linewidths=0.4)
ax.set_xlabel('Número de átomos pesados')
ax.set_ylabel('Tiempo GFN2-xTB (s)')
fig.colorbar(sc, label='Enlaces rotativos')
plt.tight_layout()
plt.savefig('p01_tiempo_vs_natom.pdf')
```

## Interpretación química

La comparación de la geometría semilla con el cristal de cafeína permite evaluar directamente la calidad del protocolo ETKDG + MMFF94 + GFN2-xTB. Los valores calculados de C=O y C–N deberían estar dentro del 1–2 % de los valores cristalográficos, confirmando que GFN2-xTB es adecuado como punto de partida para DFT.

En el bosque, las moléculas de la clase "casos difíciles" deberían mostrar la mayor tasa de fallo en la incrustación, porque ETKDG fue parametrizado con distribuciones de la CSD, donde las geometrías muy tensionadas están estadísticamente subrepresentadas.

El análisis de correlaciones debería revelar que el tiempo de optimización xTB escala aproximadamente como $O(N^{2.5\text{–}3})$ con el número de átomos, teniendo implicaciones directas para diseño de pipelines masivos.

```{admonition} Conexión con prácticas posteriores
**La geometría `cafeina_GFN2.xyz` es el input directo de la Práctica 4** (optimización B3LYP/6-31G(d)). Guárdala. El bosque de esta práctica es la base del análisis de espacio conformacional de la Práctica 3.
```

## Entregables

### Datos

- **D1**: `cafeina_GFN2.xyz` — geometría semilla optimizada.
- **D2**: `p01_dataset_final.csv` — bosque con la fila de la semilla añadida.
- **D3**: `cafeina_xtb.out` — log de xTB sin modificar.

### Figuras

- **F1**: `p01_tiempo_vs_natom.pdf` — dispersión tiempo vs átomos.
- **F2**: `p01_energia_por_clase.pdf` — boxplot de energía por clase.
- **F3**: `p01_correlaciones.pdf` — mapa de calor de correlaciones.

### Texto

- **T1**: Reporte (≤ 2 páginas): tabla de validación geométrica vs cristal, figuras comentadas.
- **T2**: Respuestas a las preguntas de discusión (≤ 150 palabras por pregunta).

## Preguntas de discusión

1. **(Comprensión)** El SMILES de la cafeína es `Cn1cnc2c1c(=O)n(c(=O)n2C)C`. Escribe el SMILES de la teobromina (7-metilxantina) y la teofilina (1,3-dimetilxantina). ¿Qué diferencia estructural codifica cada SMILES respecto al de la cafeína?

2. **(Comprensión)** ¿Qué significan `--chrg 0` y `--uhf 0` en el comando xTB? ¿Qué ocurriría química y numéricamente si ejecutaras el cálculo con `--uhf 2`?

3. **(Análisis)** Examina el log de xTB e identifica: (a) el número de ciclos de optimización, (b) la energía en el primer y en el último ciclo, y (c) el cambio geométrico entre MMFF94 y GFN2-xTB. ¿Fue útil la pre-optimización?

4. **(Análisis)** Del bosque, identifica las tres moléculas con mayor RMSD de planaridad de anillo y las tres con menor. ¿Qué factor estructural parece determinante?

5. **(Metodológico)** ¿Por qué es importante fijar `randomSeed = 42`? ¿Qué consecuencia tendría para la reproducibilidad si cada estudiante usara una semilla diferente?

6. **(Metodológico)** GFN2-xTB es un método semiempírico. ¿En qué práctica del Bloque 2 aprenderás la diferencia entre métodos semiempíricos y de primeros principios? ¿Qué limitaciones específicas de GFN2-xTB esperas?

## Extensiones del ejercicio

- **Familia de xantinas**: repetir el pipeline para teobromina, teofilina, paraxantina y adenina. Construir un dataset de los 20 derivados más simples.

- **Recuperar fallos**: para moléculas donde `embed_ok = False`, intentar recuperar usando `AllChem.EmbedMultipleConfs` con 100 conformaciones.

- **Fragmento de ChEMBL**: descargar 1000 SMILES de ChEMBL con MW < 300 Da y ejecutar el pipeline. Analizar tasa de éxito.

- **GFN1 vs GFN2**: repetir la optimización semilla con `--gfn 1`. Comparar geometrías y tiempos.

- **Puerta a DFT**: usar `cafeina_GFN2.xyz` como input de la Práctica 4 (B3LYP/6-31G(d)) y cuantificar cambios geométricos.

## Referencias

1. Landrum, G. *RDKit: Open-Source Cheminformatics*. https://www.rdkit.org/

2. Bannwarth, C.; Ehlert, S.; Grimme, S. *GFN2-xTB — An Accurate and Broadly Parametrized Self-Consistent Tight-Binding Quantum Chemical Method*. J. Chem. Theory Comput. **15**(3), 1652–1671, 2019.

3. Riniker, S.; Landrum, G.A. *Better Informed Distance Geometry: Using What We Know To Improve Conformation Generation*. J. Chem. Inf. Model. **55**(12), 2562–2574, 2015.
