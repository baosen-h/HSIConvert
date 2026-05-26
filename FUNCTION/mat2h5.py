#!/usr/bin/env python3
"""Convert MATLAB .mat variables to HDF5 .h5 datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np
import scipy.io


MAT_METADATA_KEYS = {"__header__", "__version__", "__globals__"}


def list_mat_variables(path: str | Path) -> list[str]:
    """Return user variable names inside a MATLAB file."""
    path = Path(path)
    try:
        data = scipy.io.loadmat(path)
        return [name for name in data if name not in MAT_METADATA_KEYS and not name.startswith("__")]
    except NotImplementedError:
        with h5py.File(path, "r") as h5_file:
            return [name for name in h5_file if not name.startswith("#")]


def _pick_key(names: list[str], key: str | None) -> str:
    if key:
        if key not in names:
            raise KeyError(f"Key '{key}' not found. Available keys: {names}")
        return key
    if len(names) != 1:
        raise ValueError(f"Please specify --key. Available keys: {names}")
    return names[0]


def load_mat_array(path: str | Path, key: str | None = None) -> tuple[str, np.ndarray]:
    """Load a variable from v7.2-or-earlier or v7.3 MATLAB files."""
    path = Path(path)
    try:
        data = scipy.io.loadmat(path)
        names = [name for name in data if name not in MAT_METADATA_KEYS and not name.startswith("__")]
        selected_key = _pick_key(names, key)
        return selected_key, np.asarray(data[selected_key])
    except NotImplementedError:
        with h5py.File(path, "r") as h5_file:
            names = [name for name in h5_file if not name.startswith("#")]
            selected_key = _pick_key(names, key)
            return selected_key, np.asarray(h5_file[selected_key][()])


def convert_mat_to_h5(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    key: str | None = None,
    dataset_name: str | None = None,
    axes: tuple[int, ...] | list[int] | None = None,
    compression: str | None = None,
) -> Path:
    """Convert one .mat variable to one dataset in a .h5 file."""
    src = Path(input_path)
    dst = Path(output_path) if output_path else src.with_suffix(".h5")
    selected_key, array = load_mat_array(src, key)

    if axes is not None:
        axes_tuple = tuple(axes)
        if sorted(axes_tuple) != list(range(array.ndim)):
            raise ValueError(f"axes must be a permutation of {list(range(array.ndim))}")
        array = np.transpose(array, axes_tuple)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(dst, "w") as h5_file:
        h5_file.create_dataset(dataset_name or selected_key, data=array, compression=compression)

    return dst


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert .mat to .h5, with optional axis reorder.")
    parser.add_argument("input", type=Path, help="Input .mat file")
    parser.add_argument("-o", "--output", type=Path, help="Output .h5 path")
    parser.add_argument("-k", "--key", help="Variable name inside the .mat file")
    parser.add_argument("--dataset-name", help="Dataset name inside the .h5 file")
    parser.add_argument("--axes", nargs="*", type=int, help="Axis order, for example --axes 2 1 0")
    parser.add_argument("--compression", choices=["gzip", "lzf"], help="Optional HDF5 compression")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    key, array = load_mat_array(args.input, args.key)

    if args.axes:
        axes = tuple(args.axes)
        if sorted(axes) != list(range(array.ndim)):
            raise ValueError(f"--axes must be a permutation of {list(range(array.ndim))}")
        array = np.transpose(array, axes)

    dst = args.output or args.input.with_suffix(".h5")
    dst.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(dst, "w") as h5_file:
        h5_file.create_dataset(args.dataset_name or key, data=array, compression=args.compression)

    print(f"Input : {args.input.resolve()}")
    print(f"Key   : {key}")
    print(f"Shape : {array.shape}")
    print(f"Saved : {dst.resolve()}")


if __name__ == "__main__":
    main()
