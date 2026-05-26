#!/usr/bin/env python3
"""Convert ENVI image pairs to MATLAB .mat files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import scipy.io
from spectral import envi


def _metadata_value_to_matlab(value: Any) -> Any:
    """Convert simple ENVI metadata values to scipy.io.savemat friendly values."""
    if isinstance(value, list):
        converted: list[Any] = []
        all_numeric = True
        for item in value:
            try:
                converted.append(float(item))
            except (TypeError, ValueError):
                all_numeric = False
                converted.append(str(item))
        if all_numeric:
            return np.asarray(converted)
        return np.asarray(converted, dtype=object)

    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value

    return value


def _safe_metadata_key(key: str) -> str:
    return key.replace(" ", "_").replace("-", "_")


def find_envi_pairs(input_dir: str | Path) -> list[tuple[Path, Path]]:
    """Return all .hdr/.dat pairs in a directory."""
    input_dir = Path(input_dir)
    pairs: list[tuple[Path, Path]] = []
    for hdr_path in sorted(input_dir.glob("*.hdr")):
        dat_path = hdr_path.with_suffix(".dat")
        if dat_path.exists():
            pairs.append((hdr_path, dat_path))
    return pairs


def convert_envi_to_mat(
    hdr_path: str | Path,
    dat_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    dataset_name: str = "data",
    scaled: bool = False,
    max_bands: int | None = None,
    compression: bool = True,
) -> Path:
    """Convert one ENVI image pair to a .mat file.

    Parameters
    ----------
    hdr_path:
        Path to the ENVI header file.
    dat_path:
        Path to the ENVI binary file. If omitted, uses the same stem as
        ``hdr_path`` with a ``.dat`` suffix.
    output_path:
        Output .mat path. If omitted, writes beside the input with a .mat suffix.
    dataset_name:
        Name of the array variable saved inside the .mat file.
    scaled:
        Save scaled reflectance values from Spectral Python instead of raw values.
    max_bands:
        Optional number of leading bands to keep.
    compression:
        Enable MATLAB file compression.
    """
    hdr = Path(hdr_path)
    dat = Path(dat_path) if dat_path else hdr.with_suffix(".dat")
    out = Path(output_path) if output_path else hdr.with_suffix(".mat")

    if not hdr.exists():
        raise FileNotFoundError(f"Missing header file: {hdr}")
    if not dat.exists():
        raise FileNotFoundError(f"Missing data file: {dat}")

    img = envi.open(str(hdr), str(dat))
    if scaled:
        data = np.asarray(img.load()).squeeze()
    else:
        data = np.asarray(img.open_memmap()).copy()

    if max_bands is not None:
        data = data[:, :, :max_bands]

    metadata = {
        _safe_metadata_key(key): _metadata_value_to_matlab(value)
        for key, value in img.metadata.items()
    }

    if max_bands is not None:
        for key in ("wavelength", "fwhm", "band_names", "bbl"):
            if key in metadata:
                metadata[key] = metadata[key][:max_bands]
        metadata["bands"] = np.asarray([data.shape[2]])

    out.parent.mkdir(parents=True, exist_ok=True)
    scipy.io.savemat(
        out,
        {
            dataset_name: data,
            "metadata": metadata,
            "samples": np.asarray([img.ncols]),
            "lines": np.asarray([img.nrows]),
            "bands": np.asarray([data.shape[2] if data.ndim >= 3 else 1]),
        },
        do_compression=compression,
    )
    return out


# Backward-compatible alias for older imports.
convert_dat_to_mat = convert_envi_to_mat


def convert_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    name: str | None = None,
    dataset_name: str = "data",
    scaled: bool = False,
    max_bands: int | None = None,
    compression: bool = True,
) -> list[Path]:
    """Convert one named pair or every .hdr/.dat pair in a directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if name:
        pairs = [(input_dir / f"{name}.hdr", input_dir / f"{name}.dat")]
    else:
        pairs = find_envi_pairs(input_dir)

    if not pairs:
        raise FileNotFoundError(f"No .hdr/.dat pairs found in {input_dir}")

    outputs: list[Path] = []
    for hdr_path, dat_path in pairs:
        outputs.append(
            convert_envi_to_mat(
                hdr_path,
                dat_path,
                output_dir / f"{hdr_path.stem}.mat",
                dataset_name=dataset_name,
                scaled=scaled,
                max_bands=max_bands,
                compression=compression,
            )
        )
    return outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ENVI .hdr/.dat files to .mat.")
    parser.add_argument("input", type=Path, help="Input .hdr file or directory")
    parser.add_argument("-o", "--output", type=Path, help="Output .mat file or directory")
    parser.add_argument("--dat", type=Path, help="Input .dat file when converting one .hdr")
    parser.add_argument("--name", help="Dataset name without extension when input is a directory")
    parser.add_argument("--dataset-name", default="data", help="MATLAB variable name for the image array")
    parser.add_argument("--scaled", action="store_true", help="Save scaled reflectance values")
    parser.add_argument("--max-bands", type=int, help="Keep only the first N bands")
    parser.add_argument("--no-compression", action="store_true", help="Disable .mat compression")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = args.input

    if source.is_dir():
        outputs = convert_directory(
            source,
            args.output or Path("mat"),
            name=args.name,
            dataset_name=args.dataset_name,
            scaled=args.scaled,
            max_bands=args.max_bands,
            compression=not args.no_compression,
        )
    else:
        output = args.output or source.with_suffix(".mat")
        outputs = [
            convert_envi_to_mat(
                source,
                args.dat,
                output,
                dataset_name=args.dataset_name,
                scaled=args.scaled,
                max_bands=args.max_bands,
                compression=not args.no_compression,
            )
        ]

    for output in outputs:
        print(f"Wrote {output}")


if __name__ == "__main__":
    main()
