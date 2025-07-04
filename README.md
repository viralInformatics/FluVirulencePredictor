# 🧬 FluVirulencePredictor: Influenza Virulence Prediction Tool

[![Python](./README.assets/Python-3.6+-blue.svg+xml)](https://python.org/) [![Diamond](./README.assets/Diamond-2.1.11-orange.svg+xml)](https://github.com/bbuchfink/diamond)

`FluVirulencePredictor` (`fluvp`) is a comprehensive command-line utility for influenza sequence annotation, biomarker extraction, and virulence prediction. The tool processes individual FASTA files or entire directories containing influenza sequence data, utilizing machine learning models for virulence prediction.

## 📋 Overview

The `FluVirulencePredictor` pipeline consists of three primary modules:

| Module           | Function  | Description                                                  |
| ---------------- | --------- | ------------------------------------------------------------ |
| 🏷️ **Annotation** | `anno`    | Protein/gene type determination and sequence standardization |
| 🔍 **Extraction** | `extract` | Mammalian pathogenicity marker identification and processing |
| 🎯 **Prediction** | `predv`   | Virulence level classification using ensemble machine learning models |

**Input Format**: Individual FASTA files containing all sequences of a single influenza virus strain, or directories where each file represents sequences from separate influenza virus strains.

------

## ⚙️ Prerequisites

### System Dependencies

#### Diamond Installation

Diamond is a high-performance sequence alignment tool required for protein sequence comparison. Install using one of the following methods:

**Conda Installation (Recommended):**

```bash
conda install -c bioconda diamond=2.1.11
```

**Direct Binary Download:** Visit the [Diamond official website](https://github.com/bbuchfink/diamond) to download the appropriate version for your system. This tool has been validated with diamond-2.1.11.

#### Git LFS Installation

Git LFS (Large File Storage) is essential for downloading the pre-trained machine learning models and large datasets stored in the repository. Without Git LFS, the tool will not function properly.

**Conda Installation (Recommended):**

```bash
conda install -c conda-forge git-lfs
```

**Initialize Git LFS after installation:**

```bash
git lfs install
```

------

## 🔧 Installation

### Environment Setup

```bash
conda create -n fluvp-env python=3.6
conda activate fluvp-env

# Install required dependencies
conda install -c bioconda diamond=2.1.11
conda install -c conda-forge git-lfs

# Initialize Git LFS
git lfs install

# Clone the repository
git clone https://github.com/viralInformatics/FluVirulencePredictor
cd FluVirulencePredictor

# Install the package
pip install .
```

------

## 🚀 Usage

The `FluVirulencePredictor` tool provides three subcommands: `anno`, `extract`, and `predv`.

> **💡 Tip**: The three modules should be executed sequentially: `anno` → `extract` → `predv`

### 1. Sequence Annotation (`anno`)

Performs protein/gene type annotation for input sequences using DIAMOND BLAST against the influenza reference database. Sequences are standardized and nucleotide sequences are translated to amino acids.

**Syntax:**

```bash
fluvp anno -i <input> -o <output_directory> [options]
```

**Parameters:**

- `-i, --input` (required): Input FASTA file or directory containing FASTA files
- `-o, --output_directory`: Output directory for annotation results (default: `result/`)
- `-u, --updated_directory`: Directory for standardized FASTA files (default: `standardized_fasta/`)

**Example:**

```bash
cd test/
fluvp anno -i test_files/ -o annotation_results/ -u standardized_sequences/
```

### 2.  Marker Extraction (`extract`)

Identifies and processes mammalian pathogenicity-related molecular markers from annotated sequences. This step requires both standardized sequences and annotation files generated from the previous `anno` step.

**Syntax:**

```bash
fluvp extract -i <input> -a <annotation_path> -o <output_directory> [options]
```

**Parameters:**

- `-i, --input` (required): Directory containing standardized FASTA sequences (must match the `-u, --updated_directory` path from the `anno` step)
- `-a, --anno_path` (required): Directory containing annotation CSV files (must match the `-o, --output_directory` path from the `anno` step) or single annotation file
- `-o, --output_directory`: Output directory for marker extraction results (default: `virulence/`)
- `-p, --prefix`: Optional prefix for output filenames

**Example:**

```bash
# Following the anno step output directories
fluvp anno -i test_files/ -o annotation_results/ -u standardized_sequences/
fluvp extract -i standardized_sequences/ -a annotation_results/ -o virulence_markers/ -p strain1
```

### 3. Virulence Prediction (`predv`)

Performs virulence level prediction using pre-trained ensemble machine learning models. This step analyzes the molecular markers extracted from the previous `extract` step to classify virulence level.

**Syntax:**

```bash
fluvp predv -i <input> [options]
```

**Parameters:**

- `-i, --input` (required): Input CSV file containing marker data or directory containing marker files (should be the output from the `extract` step)
- `-t, --threshold`: Probability threshold for classification (default: 0.5)
- `-o, --output_directory`: Output directory for predictions (default: `virulence_predictions/`)
- `-p, --prefix`: Optional prefix for output prediction files

**Input Requirements:**

- Marker data files from the `extract` step output directory
- Files can be individual CSV files or entire directory containing multiple marker files

**Example:**

```bash
# Complete pipeline workflow
fluvp anno -i test_files/ -o annotation_results/ -u standardized_sequences/
fluvp extract -i standardized_sequences/ -a annotation_results/ -o virulence_markers/ -p strain1
fluvp predv -i virulence_markers/ -t 0.5 -o prediction_results/ -p experiment1

# Or predicting from a specific marker file
fluvp predv -i virulence_markers/strain1_test1_markers.csv -t 0.5 -o prediction_results/ -p experiment1
```

------

## 📊 Output Formats

### Annotation Output

- Annotated FASTA files with protein/gene type classifications
- Standardized amino acid sequences
- Annotation summary files (CSV format)

### Marker Extraction Output

- CSV files with extracted markers containing key columns: `Strain ID`, `Virulence Markers`, `Protein Type`,`, `Source`, `PMID` (additional supplementary columns may be included)
- Comprehensive marker annotation tables with detailed molecular information

### Prediction Output

- Virulence level prediction labels for each input strain
- Prediction probability scores for each input strain
- Feature matrix used for model prediction (original input features processed for machine learning analysis)

------



## 🤖 Model Information

The prediction module employs ensemble machine learning models trained on curated influenza sequence datasets. 

------

## 📦 Dependencies

All Python dependencies are specified in the `requirements.txt` file and are automatically installed during the package installation process. Key dependencies include:

- BioPython for sequence processing
- Pandas and NumPy for data manipulation
- Scikit-learn for machine learning components
- Diamond for sequence alignment

------

## 📝 Notes

> ⚠️ **Important**: It is essential to use the same versions of the software and model for consistency and accuracy.

For further assistance or to report issues, please visit the [GitHub Issues](https://github.com/viralInformatics/FluVirulencePredictor/issues) section of the project repository.

