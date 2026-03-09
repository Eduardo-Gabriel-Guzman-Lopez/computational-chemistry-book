# Práctica 1: De SMILES a coordenadas 3D – Grafos moleculares y representaciones químicas

```{admonition} Resumen de la práctica
:class: tip
**Thematic Block**: 1 - Structure Generation and Conformational Space  
**Difficulty Level**: Basic  
**Estimated Time**: 1h (seed) + 2h (forest and analysis)  
**Pipeline**: SMILES → molecular graph → 3D geometry (ETKDG) → FF pre-optimization → semiempirical optimization (GFN2-xTB) → structural dataset
```

## Introducción

Antes de realizar cualquier cálculo cuántico, una molécula debe existir como un objeto computacional con coordenadas tridimensionales explícitas. Este paso, aparentemente trivial, encierra decisiones metodológicas con consecuencias directas sobre la calidad de todos los cálculos posteriores: una geometría inicial mal construida puede converger a un mínimo incorrecto, producir frecuencias imaginarias espurias o generar resultados numéricos que no corresponden a ninguna especie química real.

La representación más común en quimioinformática es el **SMILES** (*Simplified Molecular Input Line Entry System*), una cadena de texto que codifica la conectividad de una molécula mediante reglas gramaticales precisas. Un SMILES como `CC(=O)Nc1ccccc1` describe sin ambigüedad la acetanilida; sin embargo, no contiene información alguna sobre los ángulos de enlace, las longitudes de enlace o la disposición espacial de los átomos. Pasar de esa cadena lineal a un conjunto de coordenadas cartesianas $(x_i, y_i, z_i)$ es el problema que resuelve esta práctica.

Las herramientas modernas —principalmente RDKit y OpenBabel— implementan algoritmos de incrustación tridimensional que combinan reglas geométricas empíricas, campos de fuerza y, en el caso del algoritmo ETKDG (*Experimental-Torsion distance geometry with basic Knowledge*), distribuciones de ángulos diedros extraídas de la Cambridge Structural Database.

## Objetivos de aprendizaje

### Conceptuales
- Distinguir entre representaciones moleculares 0D (fórmula), 1D (SMILES, InChI), 2D (grafo) y 3D (coordenadas cartesianas) y entender qué información contienen y qué omiten.
- Comprender el funcionamiento de los algoritmos de incrustación basados en geometría de distancias (DG) y por qué producen geometrías diferentes en cada ejecución.
- Justificar el protocolo FF → xTB como un compromiso entre velocidad y calidad geométrica para cálculos posteriores.

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

> ¿La geometría generada automáticamente por ETKDG + MMFF94 + GFN2-xTB reproduce las longitudes y ángulos de enlace del cristal de cafeína con un error menor al 2 %? ¿Qué átomos o regiones de la molécula muestran la mayor desviación?

## Protocolo computacional

### Paso 1: Construir el grafo molecular

```{code-cell} ipython3
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from rdkit.Chem import rdMolDescriptors

# SMILES for caffeine
smiles = 'Cn1cnc2c1c(=O)n(c(=O)n2C)C'
name = 'caffeine'

# Create mol object and verify
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    raise ValueError(f'Invalid SMILES: {smiles}')

# Basic graph information
print(f'Total atoms: {mol.GetNumAtoms()}')
print(f'Heavy atoms: {mol.GetNumHeavyAtoms()}')
print(f'Formula: {rdMolDescriptors.CalcMolFormula(mol)}')
print(f'Molecular weight: {rdMolDescriptors.CalcExactMolWt(mol):.4f} Da')
print(f'Rotatable bonds: {rdMolDescriptors.CalcNumRotatableBonds(mol)}')
```

### Paso 2: Visualizar la estructura 2D

```{code-cell} ipython3
# Generate 2D depiction
Draw.MolToImage(mol, size=(400, 300))
```

### Paso 3: Incrustación 3D con ETKDG

```{code-cell} ipython3
import random
random.seed(42)  # Reproducibility

# Add explicit hydrogens
mol_h = Chem.AddHs(mol)

# Embedding with ETKDG
params = AllChem.ETKDGv3()
params.randomSeed = 42
result = AllChem.EmbedMolecule(mol_h, params)

if result == -1:
    raise RuntimeError('3D embedding failed. '
                       'Check SMILES or use maxAttempts=200.')

print('Embedding successful!')
print(f'Number of atoms (with H): {mol_h.GetNumAtoms()}')
```

### Paso 4: Pre‑optimización con el campo de fuerza MMFF94

```{code-cell} ipython3
# Pre-optimization with MMFF94
props = AllChem.MMFFGetMoleculeProperties(mol_h)
ff = AllChem.MMFFGetMoleculeForceField(mol_h, props)

if ff is None:
    # Fallback to UFF if MMFF94 is not parameterized
    print('MMFF94 not available, using UFF.')
    ff = AllChem.UFFGetMoleculeForceField(mol_h)

conv = ff.Minimize(maxIts=2000)
e_ff = ff.CalcEnergy()
print(f'MMFF94 energy after optimization: {e_ff:.4f} kcal/mol')
print(f'Convergence (0=OK): {conv}')
```

### Paso 5: Visualización 3D con py3Dmol

```{code-cell} ipython3
import py3Dmol
from rdkit.Chem import rdmolfiles

# Convert to mol block for visualization
mol_block = rdmolfiles.MolToMolBlock(mol_h)

# Create 3D viewer
viewer = py3Dmol.view(width=500, height=400)
viewer.addModel(mol_block, 'mol')
viewer.setStyle({'stick': {'colorscheme': 'Jmol'}})
viewer.setBackgroundColor('white')
viewer.zoomTo()
viewer.show()
```

### Paso 6: Exportar para optimización semiempírica

The force field optimized geometry can be further refined using GFN2-xTB, a semiempirical method that provides near-DFT quality geometries at a fraction of the computational cost.

::::{tab-set}

:::{tab-item} GFN2-xTB (Recommended)
```bash
# Save XYZ file for xTB optimization
# From Python:
from rdkit.Chem import rdmolfiles
rdmolfiles.MolToXYZFile(mol_h, 'caffeine_FF.xyz')

# Then run from terminal:
xtb caffeine_FF.xyz --opt tight --chrg 0 --uhf 0 --gfn 2 > caffeine_xtb.out

# Verify convergence:
grep "GEOMETRY OPTIMIZATION CONVERGED" caffeine_xtb.out

# Optimized geometry saved in: xtbopt.xyz
```

**Key parameters:**
- `--opt tight`: Stricter convergence criterion (recommended for DFT starting points)
- `--chrg 0`: Total molecular charge
- `--uhf 0`: Number of unpaired electrons (0 for closed shell)
- `--gfn 2`: Requests GFN2-xTB method explicitly
:::

:::{tab-item} Gaussian
```
%chk=caffeine.chk
%mem=4GB
%nproc=4
# PM7 Opt

Caffeine semiempirical optimization

0 1
[coordinates from XYZ file]
```

**Notes:**
- PM7 is Gaussian's most accurate semiempirical method
- Use `geom=allcheck` to read geometry from checkpoint
:::

:::{tab-item} ORCA
```
! PM3 Opt
%pal nprocs 4 end

* xyzfile 0 1 caffeine_FF.xyz
```

**Notes:**
- ORCA includes PM3, but GFN2-xTB is recommended for organic molecules
- Install xtb separately for best results with ORCA
:::

::::

### Paso 7: Extraer coordenadas XYZ

```{code-cell} ipython3
import numpy as np

def read_xyz(mol_h):
    """Extract coordinates from RDKit mol object."""
    conf = mol_h.GetConformer()
    atoms = []
    coords = []
    for i, atom in enumerate(mol_h.GetAtoms()):
        atoms.append(atom.GetSymbol())
        pos = conf.GetAtomPosition(i)
        coords.append([pos.x, pos.y, pos.z])
    return atoms, np.array(coords)

atoms, coords = read_xyz(mol_h)

# Display first few atoms
print("Atom  X        Y        Z")
print("-" * 35)
for i in range(min(10, len(atoms))):
    print(f"{atoms[i]:4s} {coords[i,0]:8.4f} {coords[i,1]:8.4f} {coords[i,2]:8.4f}")
print(f"... ({len(atoms)} atoms total)")
```

## Quality Control

### Expected Bond Lengths

After optimization, verify that key structural parameters match expected values:

| Bond | Expected (Å) | Acceptable Range |
|------|-------------|------------------|
| C=O (carbonyl) | 1.22 | 1.20 - 1.24 |
| C-N (aromatic) | 1.33 | 1.30 - 1.36 |
| C-N (aliphatic) | 1.46 | 1.44 - 1.48 |

```{code-cell} ipython3
def calculate_distance(coords, i, j):
    """Calculate distance between two atoms."""
    return np.linalg.norm(coords[i] - coords[j])

# Calculate all C-N and C-O bond distances
print("Selected bond distances:")
for i, atom_i in enumerate(atoms):
    for j, atom_j in enumerate(atoms):
        if i < j:
            d = calculate_distance(coords, i, j)
            # Only show bonds (approximate bond length)
            if d < 1.8:
                print(f"{atom_i}{i+1}-{atom_j}{j+1}: {d:.3f} Å")
```

## Expanding Chemical Space: The Forest

The forest dataset contains 50 organic molecules selected to cover structural diversity:

| Category | Examples | Count |
|----------|----------|-------|
| Carbocyclic aromatics | benzene, naphthalene, pyrene | 10 |
| Heteroaromatics | pyridine, imidazole, indole | 10 |
| Flexible molecules | alkanes, amino acids | 10 |
| Intramolecular H-bonds | salicylaldehyde, 2-aminobenzoic acid | 10 |
| Challenging cases | cubane, spiro compounds | 10 |

### Dataset Variables

```{code-cell} ipython3
import pandas as pd

# Create sample forest data structure
forest_columns = {
    'id': 'Molecule identifier (IUPAC name)',
    'smiles': 'SMILES string',
    'class': 'Structural category',
    'n_heavy': 'Number of heavy atoms',
    'n_rot_bonds': 'Number of rotatable bonds',
    'mw': 'Molecular weight (Da)',
    'embed_ok': 'Embedding success (True/False)',
    'e_ff_kcalmol': 'MMFF94 energy (kcal/mol)',
    'e_xtb_hartree': 'GFN2-xTB energy (Hartree)',
    't_xtb_s': 'xTB optimization time (s)'
}

print("Dataset columns:")
for col, desc in forest_columns.items():
    print(f"  {col:15s} : {desc}")
```

### Automation Script

```{code-cell} ipython3
def process_molecule(smiles, name, mol_class):
    """Process a single molecule through the pipeline."""
    result = {
        'id': name,
        'smiles': smiles,
        'class': mol_class
    }
    
    # Parse SMILES
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        result['embed_ok'] = False
        return result
    
    # Calculate descriptors
    result['n_heavy'] = mol.GetNumHeavyAtoms()
    result['n_rot_bonds'] = rdMolDescriptors.CalcNumRotatableBonds(mol)
    result['mw'] = rdMolDescriptors.CalcExactMolWt(mol)
    
    # 3D embedding
    mol_h = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    ok = AllChem.EmbedMolecule(mol_h, params)
    
    if ok == -1:
        result['embed_ok'] = False
        return result
    result['embed_ok'] = True
    
    # Force field optimization
    ff = AllChem.MMFFGetMoleculeForceField(
        mol_h, AllChem.MMFFGetMoleculeProperties(mol_h))
    if ff is None:
        ff = AllChem.UFFGetMoleculeForceField(mol_h)
    ff.Minimize(maxIts=2000)
    result['e_ff_kcalmol'] = ff.CalcEnergy()
    
    return result

# Process caffeine as example
caffeine_result = process_molecule(
    'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
    'caffeine',
    'heteroaromatic'
)

print("Caffeine processing result:")
for k, v in caffeine_result.items():
    print(f"  {k}: {v}")
```

## Analysis

### Sample Analysis Code

```{code-cell} ipython3
import matplotlib.pyplot as plt

# Create sample dataset for visualization
sample_data = pd.DataFrame([
    {'id': 'benzene', 'n_heavy': 6, 't_xtb_s': 0.5, 'n_rot_bonds': 0},
    {'id': 'naphthalene', 'n_heavy': 10, 't_xtb_s': 1.2, 'n_rot_bonds': 0},
    {'id': 'caffeine', 'n_heavy': 14, 't_xtb_s': 2.1, 'n_rot_bonds': 3},
    {'id': 'aspirin', 'n_heavy': 13, 't_xtb_s': 1.8, 'n_rot_bonds': 3},
    {'id': 'dopamine', 'n_heavy': 11, 't_xtb_s': 1.5, 'n_rot_bonds': 4},
])

fig, ax = plt.subplots(figsize=(8, 5))
scatter = ax.scatter(
    sample_data['n_heavy'], 
    sample_data['t_xtb_s'],
    c=sample_data['n_rot_bonds'], 
    cmap='viridis',
    s=100, edgecolors='k', linewidths=0.5
)
ax.set_xlabel('Number of Heavy Atoms', fontsize=12)
ax.set_ylabel('xTB Optimization Time (s)', fontsize=12)
ax.set_title('Computational Cost vs Molecular Size', fontsize=14)
plt.colorbar(scatter, label='Rotatable Bonds')
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
3. **Optimización por campo de fuerza**: Pre‑optimización con MMFF94 para obtener geometrías iniciales razonables
4. **Métodos semiempericos**: GFN2-xTB ofrece calidad cercana a DFT con bajo costo computacional
5. **Automatización del flujo**: Construir flujos reproducibles para procesar múltiples moléculas

```{admonition} Pasos siguientes
:class: tip
En la Práctica 2 usaremos estas geometrías optimizadas como puntos de partida para el muestreo conformacional y explorar el espacio conformacional de moléculas flexibles.
```

## References

1. Landrum, G. *RDKit: Open-source cheminformatics*. https://www.rdkit.org/
2. Bannwarth, C. et al. *GFN2-xTB—An Accurate and Broadly Parametrized Self-Consistent Tight-Binding Quantum Chemical Method*. J. Chem. Theory Comput. 2019, 15, 1652–1671.
3. Riniker, S.; Landrum, G.A. *Better Informed Distance Geometry: Using What We Know To Improve Conformation Generation*. J. Chem. Inf. Model. 2015, 55, 2562–2574.
