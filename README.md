# HyperspectralFormatConverter

HyperspectralFormatConverter is a Python tool for hyperspectral data format
conversion between ENVI, MATLAB MAT, and HDF5.

## What It Converts

This project provides three conversion scripts:

- `FUNCTION/envi2mat.py`: convert ENVI `.hdr + data file` pairs to MATLAB `.mat`.
- `FUNCTION/envi2h5.py`: convert ENVI `.hdr + data file` pairs to HDF5 `.h5`.
- `FUNCTION/mat2h5.py`: convert a variable inside a MATLAB `.mat` file to HDF5 `.h5`.

For ENVI data, the input usually has two files:

```text
hsi.hdr  -> header file, stores image metadata
hsi.dat  -> data file, stores the real pixel values
```

The data file may use `.dat`, `.raw`, `.img`, or no extension. The `.hdr`
file describes how to read that data file, including:

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

The data file may also be extensionless, `.raw`, or `.img`.

Convert one ENVI image to MAT:

```bash
python FUNCTION/envi2mat.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat -o DATA/OUTPUT/hsi.mat
```

For an extensionless data file:

```text
python FUNCTION/envi2mat.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi -o DATA/OUTPUT/hsi.mat
```

If the data file is one of the default names, this also works:

```bash
python FUNCTION/envi2mat.py DATA/INPUT/hsi.hdr -o DATA/OUTPUT/hsi.mat
```

Keep only the first N bands:

```bash
python FUNCTION/envi2mat.py DATA/INPUT/hsi.hdr -o DATA/OUTPUT/hsi.mat --max-bands 76
```

The `.mat` output stores:

- image data
- samples
- lines
- bands

## ENVI To H5

Put input files here:

```text
DATA/INPUT/hsi.hdr
DATA/INPUT/hsi.dat
```

The data file does not have to be named `.dat`. If `--dat` is omitted,
`envi2h5.py` tries these names next to the `.hdr` file:

```text
hsi.dat
hsi
hsi.raw
hsi.img
```

Convert one ENVI image to H5:

```bash
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi.dat -o DATA/OUTPUT/hsi.h5
```

For an extensionless data file:

```text
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr --dat DATA/INPUT/hsi -o DATA/OUTPUT/hsi.h5
```

If the data file is one of the default names above, this also works:

```bash
python FUNCTION/envi2h5.py DATA/INPUT/hsi.hdr -o DATA/OUTPUT/hsi.h5
```

The `.h5` output stores the hyperspectral cube as one dataset. The default
dataset name is:

```text
hyperspectral
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

The output dataset name is `hyperspectral` by default, matching `envi2h5.py`.

Reorder axes when needed so the H5 shape is:

```text
lines x samples x bands
```

For example, convert `bands x lines x samples` to `lines x samples x bands`:

```bash
python FUNCTION/mat2h5.py DATA/INPUT/hsi.mat --key data --axes 1 2 0 -o DATA/OUTPUT/hsi.h5
```

This creates a clean HDF5 file that ENVI can open as a generic HDF5 raster
dataset. Choose the correct RGB bands in ENVI when displaying it.


## Python API

The scripts can also be imported as Python functions:

```python
from FUNCTION.envi2mat import convert_envi_to_mat
from FUNCTION.envi2h5 import convert_envi_to_h5
from FUNCTION.mat2h5 import convert_mat_to_h5

convert_envi_to_mat(
    "DATA/INPUT/hsi.hdr",
    "DATA/OUTPUT/hsi.mat",
    data_path="DATA/INPUT/hsi.dat",
)

convert_envi_to_h5(
    "DATA/INPUT/hsi.hdr",
    "DATA/OUTPUT/hsi.h5",
    data_path="DATA/INPUT/hsi.dat",
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
