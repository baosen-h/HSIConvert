#!/usr/bin/env python3
"""Convert an ENVI image pair to a MATLAB .mat file."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import scipy.io
from spectral import envi


def find_data_file(hdr_path: Path, data_path: Path | None = None) -> Path:
    if data_path is not None:
        return data_path

    for candidate in (
        hdr_path.with_suffix(".dat"),
        hdr_path.with_suffix(""),
        hdr_path.with_suffix(".raw"),
        hdr_path.with_suffix(".img"),
    ):
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"Could not find data file for {hdr_path}")


def convert_envi_to_mat(
    hdr_path: str | Path,
    output_path: str | Path,
    data_path: str | Path | None = None,
    dataset_name: str = "data",
    max_bands: int | None = None,
) -> Path:
    hdr = Path(hdr_path)
    data = find_data_file(hdr, Path(data_path) if data_path else None)
    output = Path(output_path)

    image = envi.open(str(hdr), str(data))
    cube = image.open_memmap()
    if max_bands is not None:
        cube = cube[:, :, :max_bands]

    output.parent.mkdir(parents=True, exist_ok=True)
    scipy.io.savemat(
        output,
        {
            dataset_name: np.asarray(cube).copy(),
            "samples": np.asarray([image.ncols]),
            "lines": np.asarray([image.nrows]),
            "bands": np.asarray([cube.shape[2] if cube.ndim == 3 else 1]),
        },
        do_compression=True,
    )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ENVI .hdr data to MAT.")
    parser.add_argument("hdr", type=Path, help="Input ENVI .hdr file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .mat file")
    parser.add_argument("--dat", type=Path, help="Input ENVI data file")
    parser.add_argument("--dataset-name", default="data", help="MATLAB variable name")
    parser.add_argument("--max-bands", type=int, help="Keep only the first N bands")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = convert_envi_to_mat(
        args.hdr,
        args.output,
        data_path=args.dat,
        dataset_name=args.dataset_name,
        max_bands=args.max_bands,
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
