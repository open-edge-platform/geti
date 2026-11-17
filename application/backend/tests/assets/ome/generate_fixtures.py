# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import numpy as np
import tifffile


def generate(destination: Path) -> None:
    """Write synthetic fixtures whose pixels encode T, Z, C, Y and X."""
    t, z, c, y, x = np.indices((2, 2, 3, 32, 48))
    data = (t * 10000 + z * 1000 + c * 100 + y * 48 + x).astype(np.uint16)
    for name, array, axes in (
        ("xyc", data[0, 0], "CYX"),
        ("xycz", data[0], "ZCYX"),
        ("xyczt", data, "TZCYX"),
        ("alternate_order", data.transpose(2, 0, 1, 3, 4), "CTZYX"),
        ("single_channel", data[0, 0, 0], "YX"),
    ):
        tifffile.imwrite(
            destination / f"{name}.ome.tiff",
            array,
            ome=True,
            photometric="minisblack",
            metadata={"axes": axes},
            compression="deflate",
            rowsperstrip=8,
        )
    tifffile.imwrite(
        destination / "bigtiff.ome.tiff",
        data[0, 0],
        ome=True,
        bigtiff=True,
        photometric="minisblack",
        metadata={"axes": "CYX"},
    )
    with tifffile.TiffWriter(destination / "pyramidal.ome.tiff", ome=True) as writer:
        writer.write(data, subifds=2, photometric="minisblack", tile=(16, 16), metadata={"axes": "TZCYX"})
        for scale in (2, 4):
            writer.write(data[..., ::scale, ::scale], subfiletype=1, photometric="minisblack", tile=(16, 16))
    for planar in (False, True):
        tifffile.imwrite(
            destination / ("rgb_planar.ome.tiff" if planar else "rgb.ome.tiff"),
            data[0, 0] if planar else data[0, 0].transpose(1, 2, 0),
            ome=True,
            photometric="rgb",
            planarconfig="separate" if planar else "contig",
            metadata={"axes": "SYX" if planar else "YXS"},
        )
    tifffile.imwrite(destination / "not_ome.tiff", data[0, 0, 0], metadata=None)
    tifffile.imwrite(destination / "malformed.ome.tiff", data[0, 0, 0], description="<OME><Image></OME>", metadata=None)


if __name__ == "__main__":
    generate(Path(__file__).parent)
