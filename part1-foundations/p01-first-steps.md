# Práctica 1: De SMILES a coordenadas 3D – Grafos moleculares y representaciones químicas

```{admonition} Resumen de la práctica
:class: tip
**Bloque temático**: 1 – Generación de estructuras y espacio conformacional  
**Nivel de dificultad**: Básico  
**Tiempo estimado**: 1h (semilla) + 2h (bosque y análisis)  
**Flujo central**: SMILES → grafo molecular → geometría 3D (ETKDG) → pre-opt FF → opt semiempírica (GFN2-xTB) → dataset estructural
```

## Introducción

Antes de realizar cualquier cálculo cuántico, una molécula debe existir como un objeto computacional con coordenadas tridimensionales explícitas. Este paso, aparentemente trivial, encierra decisiones metodológicas con consecuencias directas sobre la calidad de todos los cálculos posteriores: una geometría inicial mal construida puede converger a un mínimo incorrecto, producir frecuencias imaginarias espurias o generar resultados numéricos que no corresponden a ninguna especie química real.

La representación más común en quimioinformática es el **SMILES** (*Simplified Molecular Input Line Entry System*), una cadena de texto que codifica la conectividad de una molécula mediante reglas gramaticales precisas. Un SMILES como `CC(=O)Nc1ccccc1` describe sin ambigüedad la acetanilida; sin embargo, no contiene información alguna sobre los ángulos de enlace, las longitudes de enlace o la disposición espacial de los átomos. Pasar de esa cadena lineal a un conjunto de coordenadas cartesianas $(x_i, y_i, z_i)$ es el problema que resuelve esta práctica.

Las herramientas modernas —principalmente RDKit y OpenBabel— implementan algoritmos de incrustación tridimensional que combinan reglas geométricas empíricas, campos de fuerza y, en el caso del algoritmo ETKDG (*Experimental-Torsion distance geometry with basic Knowledge*), distribuciones de ángulos diedros extraídas de la Cambridge Structural Database.

## Marco teórico

### Representaciones moleculares: De lo lineal a lo tridimensional

Una molécula puede codificarse en distintos niveles de detalle:

- **0D (Fórmula molecular)**: Solo composición, sin conectividad  
- **1D (SMILES, InChI)**: Conectividad lineal y orden de enlace  
- **2D (Grafo)**: Topología 2D, incluye estereoquímica plana  
- **3D (Coordenadas cartesianas)**: Posición espacial de cada átomo  

Cada nivel es una proyección: al bajar de 3D a 1D se pierde información irreversiblemente. Las coordenadas cartesianas 3D son las **únicas** que permiten calcular propiedades que dependen de la geometría (energías, frecuencias, densidades electrónicas).

### Algoritmo ETKDG: Geometría de distancias

El algoritmo ETKDG convierte un grafo molecular en coordenadas cartesianas resolviendo un problema de optimización sobre matrices de distancias interatómicas. Los límites de cada distancia se obtienen de tres fuentes:

1. **Reglas de enlace covalente**: distancias esperadas para cada tipo de enlace  
2. **Restricciones van der Waals**: impedimentos de no-penetración  
3. **Estadísticas cristalográficas**: distribuciones de ángulos diedros extraídas de la CSD  

El resultado **no es único**: distintas semillas aleatorias producen geometrías diferentes, todas igualmente válidas como punto de inicio.

### Campo de fuerza MMFF94

Un campo de fuerza es una función de energía potencial **empírica** que describe la energía como suma de:
- Contribuciones de enlace ($\propto (r - r_0)^2$)  
- Ángulos ($\propto (\theta - \theta_0)^2$)  
- Torsiones (diedros, $\cos(n\phi)$)  
- Interacciones no covalentes (van der Waals, Coulomb)  

MMFF94 está parametrizado para moléculas orgánicas pequeñas y es adecuado para corregir geometrías iniciales ETKDG. **No es apropiado** para reacciones, rupturas de enlace o sistemas con metales de transición.

### Métodos semiempíricos: GFN2-xTB

GFN2-xTB es un método de enlace fuerte autoconsistente (*tight-binding*) parametrizado para reproducir geometrías y energías de conformación con precisión comparable a DFT/def2-SVP, pero con costo computacional **3–4 órdenes de magnitud menor**.

La energía total contiene:
- Contribución electrónica (Hamiltoniano efectivo)  
- Dispersión (D4)  
- Repulsión nuclear  

GFN2-xTB es apropiado para **optimización geométrica de moléculas orgánicas**. **No es apropiado** para excitaciones electrónicas ni propiedades que requieren descripción explícita de la función de onda.

## Objetivos de aprendizaje

### Conceptuales
- Distinguir entre representaciones moleculares 0D, 1D, 2D y 3D, e identificar qué información contiene y qué omite cada una.
- Explicar el principio del algoritmo ETKDG y por qué produce geometrías diferentes con distintas semillas aleatorias.
- Justificar el protocolo FF → xTB como un compromiso entre velocidad y calidad geométrica para cálculos posteriores.

### Procedimentales
- Utilizar RDKit desde un script en Python.
- Convertir entre formatos moleculares (`.smi`, `.mol2`, `.xyz`, `.sdf`).
- Ejecutar una optimización con GFN2-xTB y verificar la convergencia.
- Visualizar estructuras 3D con py3Dmol.

## Sistema modelo: cafeína

La molécula semilla para esta práctica es la **cafeína** (`Cn1cnc2c1c(=O)n(c(=O)n2C)C`, CAS 58-08-2), una molécula con un núcleo heterocíclico de purina, tres grupos metilo y dos carbonilos. Se eligió porque:

1. Es pequeña pero no trivial (24 átomos pesados).
2. Posee un sistema aromático y grupos polares que ponen a prueba el campo de fuerza.
3. Su estructura cristalina está bien determinada, permitiendo validar la geometría.
4. ¡Es una molécula que todos conocen!

### Pregunta de investigación

> ¿La geometría generada automáticamente por ETKDG + MMFF94 + GFN2-xTB reproduce las longitudes y ángulos de enlace del cristal de cafeína con un error menor al 2 %? ¿Qué átomos o regiones de la molécula muestran la mayor desviación?

## Flujo de la práctica

```{mermaid}
flowchart LR
    A["SMILES<br/>(cadena texto)"] --> B["Grafo molecular<br/>(RDKit)"]
    B --> C["Geometría 3D<br/>(ETKDG)"]
    C --> D["Pre-opt FF<br/>(MMFF94)"]
    D --> E["Opt semiempírica<br/>(GFN2-xTB)"]
    E --> F["Dataset estructural<br/>(análisis)"]
    
    style A fill:#e1f5ff
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
    style F fill:#f1f8e9
```

## Protocolo computacional

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

La geometría optimizada con el campo de fuerza puede refinarse aún más utilizando GFN2-xTB, un método semiempírico que proporciona geometrías de calidad cercana a DFT a una fracción del costo computacional.

::::{tab-set}

:::{tab-item} GFN2-xTB (Recomendado)
```bash
# Guardar archivo XYZ para optimización con xTB
# Desde Python:
from rdkit.Chem import rdmolfiles
rdmolfiles.MolToXYZFile(mol_h, 'cafeina_FF.xyz')

# Luego ejecuta desde terminal:
xtb cafeina_FF.xyz --opt tight --chrg 0 --uhf 0 --gfn 2 > cafeina_xtb.out

# Verifica convergencia:
grep "GEOMETRY OPTIMIZATION CONVERGED" cafeina_xtb.out

# Geometría optimizada guardada en: xtbopt.xyz
```

**Parámetros clave:**
- `--opt tight`: Criterio de convergencia más estricto (recomendado para puntos de partida DFT)
- `--chrg 0`: Carga molecular total
- `--uhf 0`: Número de electrones sin aparear (0 para capa cerrada)
- `--gfn 2`: Solicita explícitamente el método GFN2-xTB
:::

:::{tab-item} Gaussian
```
%chk=cafeina.chk
%mem=4GB
%nproc=4
# PM7 Opt

Cafeina optimización semiempírica

0 1
[coordenadas del archivo XYZ]
```

**Notas:**
- PM7 es el método semiempírico más preciso de Gaussian
- Usa `geom=allcheck` para leer la geometría del archivo de chequeo
:::

:::{tab-item} ORCA
```
! PM3 Opt
%pal nprocs 4 end

* xyzfile 0 1 cafeina_FF.xyz
```

**Notas:**
- ORCA incluye PM3, pero se recomienda GFN2-xTB para moléculas orgánicas
- Instala xtb por separado para mejores resultados con ORCA
:::

::::

### Paso 7: Extraer coordenadas cartesianas

```{code-cell} ipython3
import numpy as np

def leer_xyz(mol_h):
    """Extraer coordenadas del objeto molecular RDKit."""
    conf = mol_h.GetConformer()
    atomos = []
    coords = []
    for i, atomo in enumerate(mol_h.GetAtoms()):
        atomos.append(atomo.GetSymbol())
        pos = conf.GetAtomPosition(i)
        coords.append([pos.x, pos.y, pos.z])
    return atomos, np.array(coords)

atomos, coords = leer_xyz(mol_h)

# Mostrar primeros átomos
print("Átomo    X        Y        Z")
print("-" * 35)
for i in range(min(10, len(atomos))):
    print(f"{atomos[i]:4s}  {coords[i,0]:8.4f} {coords[i,1]:8.4f} {coords[i,2]:8.4f}")
print(f"... ({len(atomos)} átomos en total)")
```

## Control de calidad

### Longitudes de enlace esperadas

Después de la optimización, verifica que los parámetros estructurales clave coincidan con los valores esperados:

| Enlace | Esperado (Å) | Rango aceptable |
|--------|------------|-----------------|
| C=O (carbonilo) | 1.22 | 1.20 – 1.24 |
| C–N (aromático) | 1.33 | 1.30 – 1.36 |
| C–N (alifático) | 1.46 | 1.44 – 1.48 |

```{code-cell} ipython3
def calcular_distancia(coords, i, j):
    """Calcular distancia entre dos átomos."""
    return np.linalg.norm(coords[i] - coords[j])

# Calcular todas las distancias C-N y C-O
print("Distancias de enlace seleccionadas:")
for i, atomo_i in enumerate(atomos):
    for j, atomo_j in enumerate(atomos):
        if i < j:
            d = calcular_distancia(coords, i, j)
            # Solo mostrar enlaces (aproximadamente)
            if d < 1.8:
                print(f"{atomo_i}{i+1}-{atomo_j}{j+1}: {d:.3f} Å")
```

## Expandir el espacio químico: el bosque

El dataset del bosque contiene 50 moléculas orgánicas seleccionadas para cubrir diversidad estructural:

| Categoría | Ejemplos | Cantidad |
|-----------|----------|----------|
| Aromáticos carbocíclicos | benceno, naftaleno, pireno | 10 |
| Heteroaromáticos | piridina, imidazol, indol | 10 |
| Moléculas flexibles | alcanos, aminoácidos | 10 |
| Puentes de H intramolecular | salicilaldehído, ácido 2-aminobenzoico | 10 |
| Casos difíciles | cubano, espiro-compuestos | 10 |

### Variables del dataset

```{code-cell} ipython3
import pandas as pd

# Crear estructura de datos del bosque de ejemplo
columnas_bosque = {
    'id': 'Identificador de molécula (nombre IUPAC)',
    'smiles': 'Cadena SMILES',
    'clase': 'Categoría estructural',
    'n_heavy': 'Número de átomos pesados',
    'n_rot_bonds': 'Número de enlaces rotativos',
    'mw': 'Peso molecular (Da)',
    'embed_ok': 'Éxito de incrustación (True/False)',
    'e_ff_kcalmol': 'Energía MMFF94 (kcal/mol)',
    'e_xtb_hartree': 'Energía GFN2-xTB (Hartree)',
    't_xtb_s': 'Tiempo de optimización xTB (s)'
}

print("Columnas del dataset:")
for col, desc in columnas_bosque.items():
    print(f"  {col:15s} : {desc}")
```

### Script de automatización

```{code-cell} ipython3
def procesar_molecula(smiles, nombre, clase_mol):
    """Procesar una sola molécula a través del flujo."""
    resultado = {
        'id': nombre,
        'smiles': smiles,
        'clase': clase_mol
    }
    
    # Analizar SMILES
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        resultado['embed_ok'] = False
        return resultado
    
    # Calcular descriptores
    resultado['n_heavy'] = mol.GetNumHeavyAtoms()
    resultado['n_rot_bonds'] = rdMolDescriptors.CalcNumRotatableBonds(mol)
    resultado['mw'] = rdMolDescriptors.CalcExactMolWt(mol)
    
    # Incrustación 3D
    mol_h = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    ok = AllChem.EmbedMolecule(mol_h, params)
    
    if ok == -1:
        resultado['embed_ok'] = False
        return resultado
    resultado['embed_ok'] = True
    
    # Optimización con campo de fuerza
    ff = AllChem.MMFFGetMoleculeForceField(
        mol_h, AllChem.MMFFGetMoleculeProperties(mol_h))
    if ff is None:
        ff = AllChem.UFFGetMoleculeForceField(mol_h)
    ff.Minimize(maxIts=2000)
    resultado['e_ff_kcalmol'] = ff.CalcEnergy()
    
    return resultado

# Procesar cafeína como ejemplo
resultado_cafeina = procesar_molecula(
    'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
    'cafeina',
    'heteroaromatico'
)

print("Resultado del procesamiento de cafeína:")
for k, v in resultado_cafeina.items():
    print(f"  {k}: {v}")
```

## Análisis

### Código de análisis de ejemplo

```{code-cell} ipython3
import matplotlib.pyplot as plt

# Crear dataset de ejemplo para visualización
datos_muestra = pd.DataFrame([
    {'id': 'benceno', 'n_heavy': 6, 't_xtb_s': 0.5, 'n_rot_bonds': 0},
    {'id': 'naftaleno', 'n_heavy': 10, 't_xtb_s': 1.2, 'n_rot_bonds': 0},
    {'id': 'cafeina', 'n_heavy': 14, 't_xtb_s': 2.1, 'n_rot_bonds': 3},
    {'id': 'aspirina', 'n_heavy': 13, 't_xtb_s': 1.8, 'n_rot_bonds': 3},
    {'id': 'dopamina', 'n_heavy': 11, 't_xtb_s': 1.5, 'n_rot_bonds': 4},
])

fig, ax = plt.subplots(figsize=(8, 5))
scatter = ax.scatter(
    datos_muestra['n_heavy'], 
    datos_muestra['t_xtb_s'],
    c=datos_muestra['n_rot_bonds'], 
    cmap='viridis',
    s=100, edgecolors='k', linewidths=0.5
)
ax.set_xlabel('Número de átomos pesados', fontsize=12)
ax.set_ylabel('Tiempo de optimización xTB (s)', fontsize=12)
ax.set_title('Costo computacional vs tamaño molecular', fontsize=14)
plt.colorbar(scatter, label='Enlaces rotativos')
plt.tight_layout()
plt.show()
```

## Ejercicios

```{admonition} Ejercicio 1: Nueva molécula
:class: note
Elige una molécula de tu interés (fármaco, producto natural, etc.) y ejecútala en el flujo completo. Compara sus parámetros estructurales con valores de la literatura.
```

```{admonition} Ejercicio 2: Fallas de incrustación
:class: note
Encuentra una molécula que falle al incrustarse. ¿Qué características estructurales la hacen difícil? ¿Cómo lo solucionarías?
```

```{admonition} Ejercicio 3: Comparación de campos de fuerza
:class: note
Compara los resultados de MMFF94 y UFF para la misma molécula. ¿Cuál produce mejor geometría para tu clase de moléculas?
```

## Resumen

En esta práctica aprendiste:

1. **Representaciones moleculares**: Las diferencias entre representaciones 0D, 1D, 2D y 3D
2. **Incrustación 3D**: Cómo ETKDG genera coordenadas 3D iniciales a partir de SMILES
3. **Optimización por campo de fuerza**: Pre-optimización con MMFF94 para obtener geometrías iniciales razonables
4. **Métodos semiempíricos**: GFN2-xTB ofrece calidad cercana a DFT con bajo costo computacional
5. **Automatización del flujo**: Construir flujos reproducibles para procesar múltiples moléculas

```{admonition} Pasos siguientes
:class: tip
En la Práctica 2 usaremos estas geometrías optimizadas como puntos de partida para el muestreo conformacional y explorar el espacio conformacional de moléculas flexibles.
```

## Referencias

1. Landrum, G. *RDKit: Quimioinformática de código abierto*. https://www.rdkit.org/
2. Bannwarth, C. et al. *GFN2-xTB—Un método de enlace fuerte autoconsistente ampliamente parametrizado*. J. Chem. Theory Comput. 2019, 15, 1652–1671.
3. Riniker, S.; Landrum, G.A. *Geometría de distancias mejor informada*. J. Chem. Inf. Model. 2015, 55, 2562–2574.
