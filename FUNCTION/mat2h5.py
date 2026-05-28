#!/usr/bin/env python3
"""Convert a MATLAB array to a simple HDF5 cube."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import scipy.io


MAT_METADATA_KEYS = {"__header__", "__version__", "__globals__"}


def choose_variable(names: list[str], name: str | None) -> str:
    if name is not None:
        if name not in names:
            raise KeyError(f"Variable '{name}' not found. Available variables: {names}")
        return name
    if len(names) != 1:
        raise ValueError(f"Please specify --key. Available variables: {names}")
    return names[0]


def load_mat_array(mat_path: str | Path, key: str | None = None) -> tuple[str, np.ndarray]:
    path = Path(mat_path)
    try:
        data = scipy.io.loadmat(path)
        names = [name for name in data if name not in MAT_METADATA_KEYS]
        selected = choose_variable(names, key)
        return selected, np.asarray(data[selected])
    except NotImplementedError:
        with h5py.File(path, "r") as h5_file:
            names = [name for name in h5_file if not name.startswith("#")]
            selected = choose_variable(names, key)
            return selected, np.asarray(h5_file[selected][()])


def reorder_axes(array: np.ndarray, axes: list[int] | None) -> np.ndarray:
    if axes is None:
        return array
    if sorted(axes) != list(range(array.ndim)):
        raise ValueError(f"--axes must be a permutation of {list(range(array.ndim))}")
    return np.transpose(array, tuple(axes))


def convert_mat_to_h5(
    input_path: str | Path,
    output_path: str | Path,
    key: str | None = None,
    dataset_name: str = "hyperspectral",
    axes: list[int] | None = None,
) -> Path:
    _, array = load_mat_array(input_path, key)
    array = reorder_axes(array, axes)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output, "w") as h5_file:
        h5_file.create_dataset(dataset_name, data=array, compression="gzip")

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a MAT array to HDF5.")
    parser.add_argument("input", type=Path, help="Input .mat file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="Output .h5 file")
    parser.add_argument("-k", "--key", help="Variable name inside the .mat file")
    parser.add_argument("--dataset-name", default="hyperspectral", help="HDF5 dataset name")
    parser.add_argument("--axes", nargs="+", type=int, help="Axis order, for example --axes 1 2 0")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    key, array = load_mat_array(args.input, args.key)
    array = reorder_axes(array, args.axes)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(args.output, "w") as h5_file:
        h5_file.create_dataset(args.dataset_name, data=array, compression="gzip")

    print(f"Input : {args.input.resolve()}")
    print(f"Key   : {key}")
    print(f"Shape : {array.shape}")
    print(f"Saved : {args.output.resolve()}")


if __name__ == "__main__":
    main()
