# Práctica 47: Generación de bibliotecas moleculares con RDKit

```{admonition} Practice Overview
:class: tip
**Thematic Block**: 17 - Chemical Space Exploration  
**Difficulty Level**: Intermediate  
**Estimated Time**: 1h (seed) + 3h (forest and analysis)  
**Pipeline**: SMILES scaffold → derivative enumeration → 3D generation → Lipinski/Veber filtering → energy screening → structured dataset
```

## Introducción

El espacio químico de las moléculas orgánicas estables con hasta 30 átomos no-hidrógeno se estima en $10^{60}$ compuestos. Ningún laboratorio puede sintetizar y ensayar esa cantidad, pero la química computacional puede **enumerar virtualmente** una región acotada de ese espacio —por ejemplo, todos los derivados de un cabezal bioactivo con un conjunto fijo de sustituyentes— y **cribar** los candidatos generados con criterios fisicoquímicos antes de comprometer tiempo de síntesis o cálculo DFT.

Este flujo de trabajo —*generar y luego filtrar*— es el punto de entrada del diseño molecular asistido por IA:

```
Enumeración (P47) → Representación y similitud (P49-P50)
    → Aprendizaje automático (P51-P53) → Diseño de novo (P54-P55)
```

## Marco teórico

### 1. SMILES y SMARTS: el lenguaje del espacio químico

SMILES (*Simplified Molecular Input Line Entry System*) encodes molecular connectivity as a text string. SMARTS (*SMILES arbitrary target specification*) extends SMILES for substructure searching and reaction pattern definition.

### 2. Regla de los cinco de Lipinski

The Lipinski criteria (1997) identify molecules with low probability of oral bioavailability:

| Property | Threshold |
|----------|-----------|
| Molecular Weight | ≤ 500 Da |
| LogP | ≤ 5 |
| H-bond Donors | ≤ 5 |
| H-bond Acceptors | ≤ 10 |

**Veber's additions:** Rotatable bonds ≤ 10 and Polar Surface Area (PSA) ≤ 140 Å²

### 3. GFN2-xTB para cribado energético

The semiempirical GFN2-xTB method calculates total energy with sufficient accuracy for screening: mean error in formation enthalpies < 3 kcal/mol, calculation time ~1s per molecule (up to 50 heavy atoms).

## Protocolo computacional

### Paso 1: Definir el cabezal y los sustituyentes

```{code-cell} ipython3
from rdkit import Chem
from rdkit.Chem import AllChem, Draw, Descriptors, Lipinski
from rdkit.Chem import rdMolDescriptors
import pandas as pd
import numpy as np

# Quinazoline scaffold (kinase inhibitor core)
scaffold_smiles = 'c1ccc2c(n1)cnc(n2)[*]'
scaffold = Chem.MolFromSmiles('c1ccc2ncnc(c2c1)N')
print(f"Scaffold: Quinazoline-4-amine")

# Define substituent library (5 fragments)
substituents = {
    'R1': ['C', 'CC', 'C(C)C', 'c1ccccc1', 'c1ccc(F)cc1'],
    'R2': ['N', 'NC', 'NCC', 'NC(=O)C', 'NS(=O)(=O)C'],
    'R3': ['O', 'OC', 'OCC', 'Oc1ccccc1', 'OCc1ccccc1']
}

print("\nSubstituent library:")
for pos, subs in substituents.items():
    print(f"  {pos}: {len(subs)} fragments")

print(f"\nTotal combinations: {np.prod([len(v) for v in substituents.values()])}")
```

### Step 2: Enumerate Derivatives

```{code-cell} ipython3
def generate_derivatives(core_smiles, substituents_dict):
    """
    Generate molecular derivatives by combining substituents.
    
    Parameters:
    -----------
    core_smiles : str
        SMILES of the core scaffold
    substituents_dict : dict
        Dictionary with position names as keys and lists of SMILES as values
    
    Returns:
    --------
    list of dicts with 'smiles' and substituent information
    """
    from itertools import product
    
    derivatives = []
    
    # Get all combinations
    positions = list(substituents_dict.keys())
    all_subs = [substituents_dict[k] for k in positions]
    
    for combo in product(*all_subs):
        # Build derivative name
        sub_dict = {pos: sub for pos, sub in zip(positions, combo)}
        
        # Simple combination approach: append substituents to SMILES
        # In practice, you would use SMARTS-based reaction transformations
        mol_smiles = core_smiles
        
        # For this example, we'll generate simpler test molecules
        # Real enumeration would use AllChem.ReplaceSubstructs
        derivative = {
            'smiles': mol_smiles,
            'R1': sub_dict.get('R1', ''),
            'R2': sub_dict.get('R2', ''),
            'R3': sub_dict.get('R3', '')
        }
        derivatives.append(derivative)
    
    return derivatives

# For demonstration, use a simpler enumeration
# Generate aniline derivatives with different substituents
base_smiles = 'Nc1ccc(cc1)'
simple_subs = ['C', 'CC', 'OC', 'F', 'Cl', 'Br', 'CF3', 'CN', 'NC', 'C(=O)C']

library = []
for sub in simple_subs:
    try:
        smiles = f'Nc1ccc({sub})cc1'
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            library.append({
                'smiles': smiles,
                'substituent': sub,
                'name': f'4-substituted-aniline-{sub}'
            })
    except:
        continue

print(f"Generated {len(library)} valid derivatives")
```

### Step 3: Calculate Lipinski and Veber Descriptors

```{code-cell} ipython3
def calculate_descriptors(smiles):
    """Calculate drug-likeness descriptors for a molecule."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    return {
        'MW': Descriptors.MolWt(mol),
        'LogP': Descriptors.MolLogP(mol),
        'HBD': Lipinski.NumHDonors(mol),
        'HBA': Lipinski.NumHAcceptors(mol),
        'RotBonds': Descriptors.NumRotatableBonds(mol),
        'TPSA': Descriptors.TPSA(mol),
        'NumHeavyAtoms': mol.GetNumHeavyAtoms(),
        'RingCount': Descriptors.RingCount(mol)
    }

# Calculate descriptors for all library molecules
results = []
for entry in library:
    desc = calculate_descriptors(entry['smiles'])
    if desc:
        results.append({**entry, **desc})

df = pd.DataFrame(results)
print("Descriptor summary:")
print(df[['MW', 'LogP', 'HBD', 'HBA', 'TPSA']].describe().round(2))
```

### Step 4: Apply Drug-Likeness Filters

```{code-cell} ipython3
def check_lipinski(row, max_violations=1):
    """Check if molecule passes Lipinski's Rule of Five."""
    violations = 0
    if row['MW'] > 500: violations += 1
    if row['LogP'] > 5: violations += 1
    if row['HBD'] > 5: violations += 1
    if row['HBA'] > 10: violations += 1
    return violations <= max_violations

def check_veber(row):
    """Check if molecule passes Veber criteria."""
    return row['RotBonds'] <= 10 and row['TPSA'] <= 140

# Apply filters
df['Lipinski_Pass'] = df.apply(check_lipinski, axis=1)
df['Veber_Pass'] = df.apply(check_veber, axis=1)
df['DrugLike'] = df['Lipinski_Pass'] & df['Veber_Pass']

print(f"\nFiltering results:")
print(f"  Total molecules: {len(df)}")
print(f"  Pass Lipinski: {df['Lipinski_Pass'].sum()}")
print(f"  Pass Veber: {df['Veber_Pass'].sum()}")
print(f"  Drug-like (both): {df['DrugLike'].sum()}")
print(f"  Success rate: {df['DrugLike'].mean()*100:.1f}%")
```

### Step 5: 3D Generation and Visualization

```{code-cell} ipython3
import py3Dmol

def generate_3d_conformer(smiles, seed=42):
    """Generate 3D conformer using ETKDGv3."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, None
    
    mol_h = Chem.AddHs(mol)
    
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    
    result = AllChem.EmbedMolecule(mol_h, params)
    if result == -1:
        return mol_h, None
    
    # Optimize with MMFF94
    try:
        props = AllChem.MMFFGetMoleculeProperties(mol_h)
        ff = AllChem.MMFFGetMoleculeForceField(mol_h, props)
        if ff:
            ff.Minimize(maxIts=500)
            energy = ff.CalcEnergy()
        else:
            energy = None
    except:
        energy = None
    
    return mol_h, energy

# Generate 3D for first few molecules
df_subset = df[df['DrugLike']].head(5).copy()
energies = []

for idx, row in df_subset.iterrows():
    mol_3d, energy = generate_3d_conformer(row['smiles'])
    energies.append(energy)

df_subset['Energy_FF'] = energies
print("3D Generation results:")
print(df_subset[['name', 'MW', 'LogP', 'Energy_FF']])
```

### Step 6: Visualize Selected Molecules

```{code-cell} ipython3
# Visualize a drug-like molecule
selected_smiles = df[df['DrugLike']].iloc[0]['smiles']
mol_3d, _ = generate_3d_conformer(selected_smiles)

if mol_3d:
    from rdkit.Chem import rdmolfiles
    mol_block = rdmolfiles.MolToMolBlock(mol_3d)
    
    viewer = py3Dmol.view(width=500, height=400)
    viewer.addModel(mol_block, 'mol')
    viewer.setStyle({'stick': {'colorscheme': 'Jmol'}})
    viewer.setBackgroundColor('white')
    viewer.zoomTo()
    viewer.show()
```

### Step 7: Energy Screening (GFN2-xTB)

For high-throughput screening, GFN2-xTB provides accurate energies at low computational cost.

::::{tab-set}

:::{tab-item} GFN2-xTB (Recommended)
```bash
# Batch optimization script
for xyz in library/*.xyz; do
    name=$(basename "$xyz" .xyz)
    xtb "$xyz" --opt crude --chrg 0 --uhf 0 --gfn 2 > "${name}_xtb.out" 2>&1
    # Extract energy
    grep "TOTAL ENERGY" "${name}_xtb.out" | tail -1 >> energies.dat
done
```

**Parameters for screening:**
- `--opt crude`: Fast convergence, suitable for filtering
- Typical time: ~1s per molecule (< 50 atoms)
:::

:::{tab-item} Gaussian
```
%chk=derivative.chk
%mem=2GB
%nproc=2
# PM7 Opt=(MaxCycles=50)

Derivative screening

0 1
[coordinates]
```
:::

:::{tab-item} ORCA
```
! PM3 Opt
%maxcore 2000

* xyzfile 0 1 derivative.xyz
```
:::

::::

### Step 8: Analyze the Library

```{code-cell} ipython3
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(10, 8))

# MW distribution
axes[0, 0].hist(df['MW'], bins=15, edgecolor='black', alpha=0.7, color='steelblue')
axes[0, 0].axvline(500, color='red', linestyle='--', label='Lipinski limit')
axes[0, 0].set_xlabel('Molecular Weight (Da)')
axes[0, 0].set_ylabel('Count')
axes[0, 0].set_title('MW Distribution')
axes[0, 0].legend()

# LogP distribution
axes[0, 1].hist(df['LogP'], bins=15, edgecolor='black', alpha=0.7, color='seagreen')
axes[0, 1].axvline(5, color='red', linestyle='--', label='Lipinski limit')
axes[0, 1].set_xlabel('LogP')
axes[0, 1].set_ylabel('Count')
axes[0, 1].set_title('LogP Distribution')
axes[0, 1].legend()

# TPSA vs MW colored by drug-likeness
scatter = axes[1, 0].scatter(
    df['MW'], df['TPSA'],
    c=df['DrugLike'].map({True: 'green', False: 'red'}),
    alpha=0.7, edgecolors='black', linewidths=0.5
)
axes[1, 0].axhline(140, color='red', linestyle='--', alpha=0.5)
axes[1, 0].axvline(500, color='red', linestyle='--', alpha=0.5)
axes[1, 0].set_xlabel('Molecular Weight (Da)')
axes[1, 0].set_ylabel('TPSA (Å²)')
axes[1, 0].set_title('Chemical Space: MW vs TPSA')

# Drug-like pie chart
drug_like_counts = df['DrugLike'].value_counts()
axes[1, 1].pie(
    drug_like_counts.values, 
    labels=['Drug-like', 'Not drug-like'],
    autopct='%1.1f%%',
    colors=['lightgreen', 'lightcoral']
)
axes[1, 1].set_title('Drug-likeness Summary')

plt.tight_layout()
plt.show()
```

### Step 9: Export Results

```{code-cell} ipython3
# Select drug-like compounds for further study
drug_like_df = df[df['DrugLike']].copy()
drug_like_df = drug_like_df.sort_values('LogP')  # Sort by lipophilicity

print(f"\nDrug-like compounds selected: {len(drug_like_df)}")
print("\nTop candidates:")
print(drug_like_df[['name', 'smiles', 'MW', 'LogP', 'TPSA']].head(10).to_string(index=False))

# Export to CSV
# drug_like_df.to_csv('drug_like_library.csv', index=False)
```

## Success Index

The **enumeration success index** $I_s$ measures library quality:

$$I_s = \frac{N_{\text{valid with 3D}}}{N_{\text{enumerated}}} \times 100\%$$

- $I_s > 80\%$: Well-designed library
- $I_s < 50\%$: Substitution positions or fragments introduce geometric conflicts

```{code-cell} ipython3
# Calculate success index for our library
total_enumerated = len(library)
valid_3d = len(df[df['DrugLike']])

success_index = (valid_3d / total_enumerated) * 100
print(f"Success Index: {success_index:.1f}%")
```

## Exercises

```{admonition} Exercise 1: Custom Scaffold
:class: note
Choose a different scaffold (e.g., indole, pyrimidine) and generate a library of 100+ derivatives. Calculate the success index.
```

```{admonition} Exercise 2: Expanded Substituents
:class: note
Add 10 more substituents to the library. How does this affect the drug-likeness percentage?
```

```{admonition} Exercise 3: Energy Filtering
:class: note
Generate 3D conformers for all drug-like molecules and filter out those with unusually high MMFF94 energy (outliers > mean + 2σ).
```

## Summary

In this practice, you learned:

1. **Virtual enumeration**: Generating combinatorial libraries from a scaffold
2. **Drug-likeness filtering**: Applying Lipinski and Veber rules
3. **Property calculation**: Computing molecular descriptors with RDKit
4. **3D generation**: Using ETKDGv3 for conformer generation
5. **Energy screening**: Using GFN2-xTB for fast energy filtering

```{admonition} Next Steps
:class: tip
In Practice 49-50, we'll learn molecular fingerprints and similarity calculations to cluster and analyze these libraries.
```

## References

1. Lipinski, C.A. et al. *Experimental and computational approaches to estimate solubility and permeability in drug discovery and development settings*. Adv. Drug Deliv. Rev. 1997, 23, 3-25.
2. Veber, D.F. et al. *Molecular properties that influence the oral bioavailability of drug candidates*. J. Med. Chem. 2002, 45, 2615-2623.
3. Bannwarth, C. et al. *GFN2-xTB—An Accurate and Broadly Parametrized Self-Consistent Tight-Binding Quantum Chemical Method*. J. Chem. Theory Comput. 2019, 15, 1652-1671.
