#!/usr/bin/env python3
"""Convert ENVI hyperspectral image files directly to HDF5."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import h5py
import numpy as np
from spectral import envi


def _metadata_value(value: Any) -> Any:
    if isinstance(value, list):
        try:
            return np.asarray([float(item) for item in value])
        except (TypeError, ValueError):
            return np.asarray([str(item) for item in value], dtype=h5py.string_dtype())
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _find_dat_path(hdr_path: Path, dat_path: str | Path | None = None) -> Path:
    if dat_path:
        return Path(dat_path)

    candidates = [
        hdr_path.with_suffix(".dat"),
        hdr_path.with_suffix(""),
        hdr_path.with_name(hdr_path.stem + ".raw"),
        hdr_path.with_name(hdr_path.stem + ".img"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Could not find binary ENVI data file for {hdr_path}")


def convert_envi_to_h5(
    hdr_path: str | Path,
    output_path: str | Path | None = None,
    *,
    dat_path: str | Path | None = None,
    dataset_name: str = "hyperspectral",
    scaled: bool = False,
    min_x: int = 0,
    max_x: int | None = None,
    max_bands: int | None = None,
    compression: str | None = "gzip",
) -> Path:
    """Convert one ENVI .hdr/.dat pair to HDF5."""
    hdr = Path(hdr_path)
    dat = _find_dat_path(hdr, dat_path)
    dst = Path(output_path) if output_path else hdr.with_suffix(".h5")

    if not hdr.exists():
        raise FileNotFoundError(f"Missing header file: {hdr}")
    if not dat.exists():
        raise FileNotFoundError(f"Missing data file: {dat}")

    img = envi.open(str(hdr), str(dat))
    if scaled:
        cube = np.asarray(img.load()).squeeze()
    else:
        cube = np.asarray(img.open_memmap()).copy()

    if max_bands is not None:
        cube = cube[:, :, :max_bands]

    x_stop = max_x if max_x is not None else cube.shape[1]
    cube = cube[:, min_x:x_stop, :]

    dst.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(dst, "w") as h5_file:
        h5_file.create_dataset(dataset_name, data=cube, chunks=True, compression=compression)

        metadata = dict(img.metadata)
        if max_bands is not None:
            for key in ("wavelength", "fwhm", "band names", "bbl"):
                if key in metadata:
                    metadata[key] = metadata[key][:max_bands]
            metadata["bands"] = str(cube.shape[2])

        for key, value in metadata.items():
            try:
                h5_file.attrs[key] = _metadata_value(value)
            except TypeError:
                h5_file.attrs[key] = str(value)

    return dst


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ENVI .hdr/.dat files to .h5.")
    parser.add_argument("hdr", type=Path, help="Input ENVI .hdr file")
    parser.add_argument("-o", "--output", type=Path, help="Output .h5 path")
    parser.add_argument("--dat", type=Path, help="Input binary ENVI file; defaults to same stem as .hdr")
    parser.add_argument("--dataset-name", default="hyperspectral", help="Dataset name inside the .h5 file")
    parser.add_argument("--scaled", action="store_true", help="Save scaled reflectance values")
    parser.add_argument("--min-x", type=int, default=0, help="Minimum x value for cropping")
    parser.add_argument("--max-x", type=int, help="Maximum x value for cropping")
    parser.add_argument("--max-bands", type=int, help="Keep only the first N bands")
    parser.add_argument("--compression", choices=["gzip", "lzf", "none"], default="gzip")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    compression = None if args.compression == "none" else args.compression
    output = convert_envi_to_h5(
        args.hdr,
        args.output,
        dat_path=args.dat,
        dataset_name=args.dataset_name,
        scaled=args.scaled,
        min_x=args.min_x,
        max_x=args.max_x,
        max_bands=args.max_bands,
        compression=compression,
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
