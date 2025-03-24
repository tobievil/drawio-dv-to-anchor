# Data Vault to Anchor DrawIO Converter

This simple script converts a Data Vault database model to Anchor. It was created for personal use.

## Requirements for DV Model

1. Data Vault 2.0 entities are unsupported.
2. Transactional Links are unsupported. Links can only have primary keys (PKs) for linked entities and system columns, and nothing more.
3. Hubs must be prefixed with `h_`.
4. Links must be prefixed with `l_`.
5. Satellites must be prefixed with `s_`.
6. No foreign keys are allowed.

Check out examples in the `./examples` directory.

## Installation

```bash
git clone https://github.com/tobievil/drawio-dv-to-anchor.git
cd ./drawio-dv-to-anchor
python3 -m venv venv
source ./venv/bin/activate
pip3 install .
```

## Usage

```bash
source ./venv/bin/activate
python3 -m drawio_db ./examples/data-vault.xml
```

## Preview

### Data Vault Model

<img src="./examples/data-vault.svg" alt="Data Vault Model" width="300">

### Output of this script

<img src="./examples/data-vault_anchor.svg" alt="Output of this script" width="300">

### Output of this script after manual edit

<img src="./examples/data-vault_anchor_edited.svg" alt="Output of this script after manual edit" width="300">
