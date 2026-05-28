#!/usr/bin/env python3
"""Convert an ENVI image pair to a simple HDF5 cube."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
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


def convert_envi_to_h5(
    hdr_path: str | Path,
    output_path: str | Path,
    data_path: str | Path | None = None,
    dataset_name: str = "hyperspectral",
) -> Path:
    hdr = Path(hdr_path)
    data = find_data_file(hdr, Path(data_path) if data_path else None)
    output = Path(output_path)

    image = envi.open(str(hdr), str(data))
    cube = image.open_memmap()

    output.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output, "w") as h5_file:
        dataset = h5_file.create_dataset(
            dataset_name,
            shape=cube.shape,
            dtype=cube.dtype,
            chunks=(min(64, cube.shape[0]), cube.shape[1], min(16, cube.shape[2])),
            compression="gzip",
        )

        rows_per_chunk = dataset.chunks[0]
        for row_start in range(0, cube.shape[0], rows_per_chunk):
            row_stop = min(row_start + rows_per_chunk, cube.shape[0])
            dataset[row_start:row_stop, :, :] = cube[row_start:row_stop, :, :]

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ENVI .hdr data to HDF5.")
    parser.add_argument("hdr", type=Path, help="Input ENVI .hdr file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .h5 file")
    parser.add_argument("--dat", type=Path, help="Input ENVI data file")
    parser.add_argument("--dataset-name", default="hyperspectral", help="HDF5 dataset name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = convert_envi_to_h5(
        args.hdr,
        args.output,
        data_path=args.dat,
        dataset_name=args.dataset_name,
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
