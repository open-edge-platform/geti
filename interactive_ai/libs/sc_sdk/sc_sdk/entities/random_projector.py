# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""This module contains the RandomProject class"""

import numpy as np
from scipy.linalg import orth


def gen_projector_array(ndim: int, odim: int = 32) -> np.ndarray:
    """
    Generate projector array with given shape
    """

    for _ in range(100):
        # try to get an orthonormal projection matrix
        projector = orth(np.random.uniform(-1, 1, (ndim, ndim)))[:, :odim]
        if (projector is not None) and (projector.shape[1] == odim):
            return projector.astype(np.float32)

    raise RuntimeError("Failed to produce a projector array.")


class RandomProjector:
    """
    This is Random Projector to create hexadecimal string key from the input feature
    """

    @staticmethod
    def project(projector: np.ndarray, feat: np.ndarray) -> list[str]:
        """
        Project feat to odim space and create hexadecimal string key

        :param feat: gradient to project and make hash feature
        :return: a list of hash feature after projection
        """
        ndim, odim = projector.shape

        if ndim < odim:
            raise ValueError(f"{ndim} is smaller than odim({odim})")

        if odim > 100:
            raise RuntimeError(f"odim size {odim} is bigger than 100")

        # simple binarization
        # compute dot product between each feature and each projection basis,
        # then use its sign for the binarization
        feat_binary = np.dot(feat, projector) >= 0

        # generate hash key strings
        # assign hex string from each consecutive 16 bits and concatenate
        _all_key = np.packbits(feat_binary, axis=-1)
        return ["".join([f"{r:02x}" for r in row]) for row in _all_key]
