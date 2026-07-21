# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Constant-velocity Kalman filter for bounding-box tracking.

State space (8-dim): ``(x, y, a, h, vx, vy, va, vh)`` where ``(x, y)`` is
the box center, ``a`` is width/height, ``h`` is height, and the rest are
per-frame velocities. Internal state is ``xyah``; convert to and from ``xyxy``
with `getitrack.utils.xyxy_to_xyah` / `xyah_to_xyxy`.

`MotionConfig` scales the process and measurement noise and sets a per-frame
velocity-decay factor (1.0 applies no damping; values below 1.0 damp velocity).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import numpy as np
import scipy.linalg

if TYPE_CHECKING:
    from getitrack.config import MotionConfig


class KalmanFilter:
    """Constant-velocity Kalman filter operating on ``xyah`` measurements.

    The filter is stateless. Callers pass ``(mean, covariance)`` tuples
    through `predict` and `update` and persist them per-track externally,
    so a single `KalmanFilter` instance can serve any number of tracks.

    Attributes:
        process_noise: Multiplier on the predict-step process-noise
            covariance (Q matrix).
        measurement_noise: Multiplier on the update-step measurement-noise
            covariance (R matrix).
        velocity_decay: Per-frame velocity damping in ``(0, 1]``.
    """

    _NDIM: ClassVar[int] = 4
    _STATE_DIM: ClassVar[int] = 2 * _NDIM
    _STD_WEIGHT_POSITION: ClassVar[float] = 1.0 / 20.0
    _STD_WEIGHT_VELOCITY: ClassVar[float] = 1.0 / 160.0
    _DEFAULT_VELOCITY_DECAY: ClassVar[float] = 1.0

    def __init__(
        self,
        process_noise: float = 1.0,
        measurement_noise: float = 1.0,
        velocity_decay: float | None = None,
    ) -> None:
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.velocity_decay = self._DEFAULT_VELOCITY_DECAY if velocity_decay is None else velocity_decay

        self._motion_mat = np.eye(self._STATE_DIM, self._STATE_DIM)
        for i in range(self._NDIM):
            self._motion_mat[i, self._NDIM + i] = 1.0
        if self.velocity_decay != self._DEFAULT_VELOCITY_DECAY:
            for i in range(self._NDIM):
                self._motion_mat[self._NDIM + i, self._NDIM + i] = self.velocity_decay

        self._update_mat = np.eye(self._NDIM, self._STATE_DIM)

    @classmethod
    def from_config(cls, config: MotionConfig) -> KalmanFilter:
        """Construct a `KalmanFilter` from a validated `MotionConfig`."""
        return cls(
            process_noise=config.process_noise,
            measurement_noise=config.measurement_noise,
            velocity_decay=config.velocity_decay,
        )

    def initiate(self, measurement: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Initialise a track's state from one ``xyah`` measurement.

        Args:
            measurement: ``(4,)`` ``[x, y, a, h]`` array.

        Returns:
            ``(mean, covariance)`` where ``mean`` has shape ``(8,)`` and
            ``covariance`` has shape ``(8, 8)``. Velocity components start
            at zero with broad covariance.
        """
        mean_pos = np.asarray(measurement, dtype=np.float64)
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]

        h = mean_pos[3]
        std = np.array(
            [
                2 * self._STD_WEIGHT_POSITION * h,
                2 * self._STD_WEIGHT_POSITION * h,
                1e-2,
                2 * self._STD_WEIGHT_POSITION * h,
                10 * self._STD_WEIGHT_VELOCITY * h,
                10 * self._STD_WEIGHT_VELOCITY * h,
                1e-5,
                10 * self._STD_WEIGHT_VELOCITY * h,
            ],
        )
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Propagate one step forward under the constant-velocity model.

        Args:
            mean: ``(8,)`` prior mean.
            covariance: ``(8, 8)`` prior covariance.

        Returns:
            ``(mean, covariance)`` of the propagated state.
        """
        motion_cov = self._predict_noise_cov(mean[3])
        new_mean = self._motion_mat @ mean
        new_covariance = self._motion_mat @ covariance @ self._motion_mat.T + motion_cov
        return new_mean, new_covariance

    def multi_predict(
        self,
        means: np.ndarray,
        covariances: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Propagate ``N`` tracks in a single batched call.

        Args:
            means: ``(N, 8)`` stacked priors.
            covariances: ``(N, 8, 8)`` stacked prior covariances.

        Returns:
            ``(means, covariances)`` of the propagated states.
        """
        if means.shape[0] == 0:
            return means, covariances
        motion_covs = np.stack([self._predict_noise_cov(h) for h in means[:, 3]], axis=0)
        # einsum avoids a macOS Accelerate batched-matmul path that raises
        # spurious floating-point warnings.
        new_means = np.einsum("nj,ij->ni", means, self._motion_mat)
        left = np.einsum("ij,njk->nik", self._motion_mat, covariances)
        new_covariances = np.einsum("nij,kj->nik", left, self._motion_mat) + motion_covs
        return new_means, new_covariances

    def project(self, mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Project the state distribution into measurement space.

        Args:
            mean: ``(8,)`` state mean.
            covariance: ``(8, 8)`` state covariance.

        Returns:
            ``(measurement_mean, measurement_covariance)`` of shapes
            ``(4,)`` and ``(4, 4)``.
        """
        innovation_cov = self._measurement_noise_cov(mean[3])
        m = self._update_mat @ mean
        c = self._update_mat @ covariance @ self._update_mat.T
        return m, c + innovation_cov

    def update(
        self,
        mean: np.ndarray,
        covariance: np.ndarray,
        measurement: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply the Kalman correction step with a new ``xyah`` measurement.

        Args:
            mean: ``(8,)`` predicted state mean.
            covariance: ``(8, 8)`` predicted state covariance.
            measurement: ``(4,)`` observed ``[x, y, a, h]``.

        Returns:
            ``(mean, covariance)`` of the corrected posterior.
        """
        projected_mean, projected_cov = self.project(mean, covariance)
        chol_factor, lower = scipy.linalg.cho_factor(projected_cov, lower=True, check_finite=False)
        kalman_gain_t = np.asarray(
            scipy.linalg.cho_solve(
                (chol_factor, lower),
                (covariance @ self._update_mat.T).T,
                check_finite=False,
            ),
        )
        kalman_gain = kalman_gain_t.T
        innovation = measurement - projected_mean
        new_mean = mean + kalman_gain @ innovation
        new_covariance = covariance - kalman_gain @ projected_cov @ kalman_gain.T
        return new_mean, new_covariance

    def multi_update(
        self,
        means: np.ndarray,
        covariances: np.ndarray,
        measurements: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Apply the Kalman correction step to ``N`` tracks in one batched call.

        Args:
            means: ``(N, 8)`` predicted state means.
            covariances: ``(N, 8, 8)`` predicted state covariances.
            measurements: ``(N, 4)`` observed ``[x, y, a, h]`` rows.

        Returns:
            ``(means, covariances)`` of the corrected posteriors.
        """
        if means.shape[0] == 0:
            return means, covariances
        innovation_covs = np.stack([self._measurement_noise_cov(h) for h in means[:, 3]], axis=0)
        projected_means = np.einsum("ij,nj->ni", self._update_mat, means)
        ph_t = np.einsum("nij,kj->nik", covariances, self._update_mat)
        projected_covs = np.einsum("ij,njk->nik", self._update_mat, ph_t) + innovation_covs
        # K = P H^T S^-1, obtained as solve(S, (P H^T)^T)^T per track.
        gains = np.linalg.solve(projected_covs, ph_t.transpose(0, 2, 1)).transpose(0, 2, 1)
        innovations = measurements - projected_means
        new_means = means + np.einsum("nij,nj->ni", gains, innovations)
        new_covariances = covariances - np.einsum("nij,njk,nlk->nil", gains, projected_covs, gains)
        return new_means, new_covariances

    def _predict_noise_cov(self, h: float) -> np.ndarray:
        std = np.array(
            [
                self._STD_WEIGHT_POSITION * h,
                self._STD_WEIGHT_POSITION * h,
                1e-2,
                self._STD_WEIGHT_POSITION * h,
                self._STD_WEIGHT_VELOCITY * h,
                self._STD_WEIGHT_VELOCITY * h,
                1e-5,
                self._STD_WEIGHT_VELOCITY * h,
            ],
        )
        return np.diag(np.square(std)) * self.process_noise

    def _measurement_noise_cov(self, h: float) -> np.ndarray:
        std = np.array(
            [
                self._STD_WEIGHT_POSITION * h,
                self._STD_WEIGHT_POSITION * h,
                1e-1,
                self._STD_WEIGHT_POSITION * h,
            ],
        )
        return np.diag(np.square(std)) * self.measurement_noise
