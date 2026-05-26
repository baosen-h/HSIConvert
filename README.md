# HyperspectralFormatConverter

HyperspectralFormatConverter is a Python tool for hyperspectral data format
conversion between ENVI, MATLAB MAT, and HDF5.

## What It Converts

This project provides three conversion scripts:

- `FUNCTION/envi2mat.py`: convert ENVI `.hdr + .dat` files to MATLAB `.mat`.
- `FUNCTION/envi2h5.py`: convert ENVI `.hdr + .dat` files to HDF5 `.h5`.
- `FUNCTION/mat2h5.py`: convert a variable inside a MATLAB `.mat` file to HDF5 `.h5`.

For ENVI data, the input usually has two files:

```text
hsi.hdr  -> header file, stores image metadata
hsi.dat  -> data file, stores the real pixel values
```

The `.hdr` file describes how to read the `.dat` file, including:

- image width
- image height
- number of bands
- data type
- interleave format
- byte order

For hyperspectral data, the loaded image is usually a 3D cube:

```text
height x width x bands
```

## Project Structure

```text
HyperspectralFormatConverter
├─ DATA
│  ├─ INPUT
│  └─ OUTPUT
├─ FUNCTION
│  ├─ envi2h5.py
│  ├─ envi2mat.py
│  └─ mat2h5.py
├─ LICENSE
├─ README.md
└─ requirements.txt
```

Use the project like this:

```text
put source files in DATA/INPUT
run one script in FUNCTION
get converted files in DATA/OUTPUT
```

## Install

```bash
pip install -r requirements.txt
```

## ENVI To MAT

Put input files here:

```text
DATA/INPUT/hsi.hdr
DATA/INPUT/hsi.dat
```

Convert one ENVI image to MAT:

```bash
python FUNCTION/envi2mat.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat -o DATA/OUTPUT/hsi.mat
```

Batch convert all `.hdr + .dat` pairs in `DATA/INPUT`:

```bash
python FUNCTION/envi2mat.py DATA/INPUT -o DATA/OUTPUT
```

The `.mat` output stores:

- image data
- metadata
- samples
- lines
- bands

## ENVI To H5

Put input files here:

```text
DATA/INPUT/hsi.hdr
DATA/INPUT/hsi.dat
```

Convert one ENVI image to H5:

```bash
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat -o DATA/OUTPUT/hsi.h5
```

The `.h5` output stores the hyperspectral cube as a dataset. The default
dataset name is:

```text
hyperspectral
```

Keep only the first N bands:

```bash
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat --max-bands 76 -o DATA/OUTPUT/hsi.h5
```

Crop columns:

```bash
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat --min-x 100 --max-x 600 -o DATA/OUTPUT/hsi.h5
```

## MAT To H5

Put input file here:

```text
DATA/INPUT/hsi.mat
```

Convert one MAT variable to H5:

```bash
python FUNCTION/mat2h5.py DATA/INPUT/hsi.mat --key data -o DATA/OUTPUT/hsi.h5
```

If the `.mat` file has multiple variables, use `--key` to choose which variable
to convert.

Reorder axes when needed:

```bash
python FUNCTION/mat2h5.py DATA/INPUT/hsi.mat --key data --axes 2 0 1 -o DATA/OUTPUT/hsi.h5
```

Example:

```text
H x W x C -> C x H x W
```

This is useful when preparing data for deep learning frameworks.

## Python API

The scripts can also be imported as Python functions:

```python
from FUNCTION.envi2mat import convert_envi_to_mat
from FUNCTION.envi2h5 import convert_envi_to_h5
from FUNCTION.mat2h5 import convert_mat_to_h5

convert_envi_to_mat(
    "DATA/INPUT/hsi.hdr",
    "DATA/INPUT/hsi.dat",
    "DATA/OUTPUT/hsi.mat",
)

convert_envi_to_h5(
    "DATA/INPUT/hsi.hdr",
    "DATA/OUTPUT/hsi.h5",
    dat_path="DATA/INPUT/hsi.dat",
)

convert_mat_to_h5(
    "DATA/INPUT/hsi.mat",
    "DATA/OUTPUT/hsi.h5",
    key="data",
)
```

## Repository Description

Python tool for hyperspectral data format conversion between ENVI, MATLAB MAT,
and HDF5.

## License

MIT. See [LICENSE](LICENSE).
