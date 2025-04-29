# Copyright (C) 2022-2025 Intel Corporation
# LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

"""Backend-team implementation of 'Feature Reconstruction Error' algorithm"""

from collections import Counter
from collections.abc import Sequence

import numpy as np
from sklearn.decomposition import PCA

from active_learning.algorithms.interface import IScoringFunction, ScoringFunctionRequirements
from active_learning.utils import NullableDataset

from geti_telemetry_tools import unified_tracing
from sc_sdk.entities.dataset_item import DatasetItem
from sc_sdk.utils.classes import classproperty


class FeatureReconstructionError(IScoringFunction):
    """
    FRE (Feature Reconstruction Error) algorithm with pseudo stratified sampling.

    Paper:
        Robust Contrastive Active Learning with Feature-guided Query Strategies
        https://arxiv.org/pdf/2109.06873.pdf

    This class implements:
     - the FRE scoring function
     - a score post-processing procedure to emulate stratified sampling

    Assumptions:
     - multi-class (single label) global annotations and predictions
    """

    @classproperty
    def requirements(cls) -> ScoringFunctionRequirements:
        return ScoringFunctionRequirements(
            unseen_dataset_with_predictions=True,
            seen_dataset_with_annotations=True,
            seen_dataset_features=True,
            unseen_dataset_features=True,
        )

    @staticmethod
    @unified_tracing
    def compute_scores(
        unseen_dataset_with_predictions: NullableDataset,
        seen_dataset_items_with_predictions: Sequence[DatasetItem],  # noqa: ARG004
        seen_dataset_items_with_annotations: Sequence[DatasetItem],
        unseen_dataset_features: np.ndarray,
        seen_dataset_features: np.ndarray,
    ) -> np.ndarray:
        # note: instead of Labels, we use their IDs to identify them uniquely
        unseen_dataset_pred_labels = np.fromiter(
            (next(iter(item.get_roi_label_ids())) for item in unseen_dataset_with_predictions),
            dtype="S24",
            count=len(unseen_dataset_with_predictions),
        )
        seen_dataset_ann_labels = np.fromiter(
            (next(iter(item.get_roi_label_ids())) for item in seen_dataset_items_with_annotations),
            dtype="S24",
            count=len(seen_dataset_items_with_annotations),
        )
        unseen_dataset_pred_labels_unique = set(unseen_dataset_pred_labels)
        _, most_predicted_label_freq = Counter(unseen_dataset_pred_labels).most_common(1)[0]
        final_scores = np.ones(len(unseen_dataset_pred_labels))

        # For each label that was predicted at least once in the unannotated set
        for pred_label in unseen_dataset_pred_labels_unique:
            # Get the features of unseen items whose prediction has this label
            unseen_indices = np.where(unseen_dataset_pred_labels == pred_label)[0]
            unseen_features = unseen_dataset_features[unseen_indices]

            # Get the features of seen items whose annotation has this label
            seen_features = seen_dataset_features[seen_dataset_ann_labels == pred_label]

            if len(seen_features) == 0:
                # No seen items with this label to apply PCA
                unseen_features_reconstructed = unseen_features
            else:
                # Apply label-conditional PCA to reduce the feature space dimensionality
                pca_for_label = PCA(0.995)
                pca_for_label.fit(seen_features)
                unseen_features_reduced = pca_for_label.transform(unseen_features)
                unseen_features_reconstructed = pca_for_label.inverse_transform(unseen_features_reduced)

            # Compute the FRE scores as the distance of the original features from the
            # reconstructed ones; this promotes diversity along the low-variance axes.
            # The minus sign makes so that better items map to lower scores (Geti)
            fre_scores = -np.sum(np.square(unseen_features - unseen_features_reconstructed), axis=1)

            # Normalize the scores to be in [0,1) in such a way that non-stratified
            # sampling (class-agnostic) would generate the same output active set
            # as stratified-sampling. To do so, the active scores are obtained as
            # the sorting indices of the FRE scores.
            # Note: score value 1.0 is already a placeholder for N/A, so the computed
            # scores should always be better (< 1.0).
            scaling_factor = max(most_predicted_label_freq, 1)
            al_scores = np.argsort(np.argsort(fre_scores)) / scaling_factor

            # Update the final scores
            final_scores[unseen_indices] = al_scores

        return final_scores


class FeatureReconstructionErrorClassAgnostic(IScoringFunction):
    """
    Variation of FRE (Feature Reconstruction Error) that does not require information
    about labels (predicted and user made).
    """

    @classproperty
    def requirements(cls) -> ScoringFunctionRequirements:
        return ScoringFunctionRequirements(
            seen_dataset_features=True,
            unseen_dataset_features=True,
        )

    @staticmethod
    @unified_tracing
    def compute_scores(
        unseen_dataset_with_predictions: NullableDataset,  # noqa: ARG004
        seen_dataset_items_with_predictions: Sequence[DatasetItem],  # noqa: ARG004
        seen_dataset_items_with_annotations: Sequence[DatasetItem],  # noqa: ARG004
        unseen_dataset_features: np.ndarray,
        seen_dataset_features: np.ndarray,
    ) -> np.ndarray:
        if len(unseen_dataset_features) == 0:  # Empty unseen dataset
            return np.array([])

        if len(seen_dataset_features) == 0:  # Empty seen dataset, cannot apply PCA
            return np.ones(len(unseen_dataset_features))

        # Apply PCA to reduce the feature space dimensionality
        pca_for_label = PCA(0.995)
        pca_for_label.fit(seen_dataset_features)
        unseen_features_reduced = pca_for_label.transform(unseen_dataset_features)
        unseen_features_reconstructed = pca_for_label.inverse_transform(unseen_features_reduced)

        # Compute the FRE scores as the distance of the original features from the
        # reconstructed ones; this promotes diversity along the low-variance axes.
        # The minus sign makes so that better items map to lower scores (Geti)
        fre_scores = -np.sum(np.square(unseen_dataset_features - unseen_features_reconstructed), axis=1)

        # Normalize the scores to be in [0,1), while keeping the same order of FRE
        # scores. To do so, the active scores are from the sorting indices of the
        # FRE scores, then scaled as appropriate.
        # Note: score value 1.0 is already a placeholder for N/A, so the computed
        # scores should always be better (< 1.0).
        scaling_factor = max(len(unseen_dataset_features), 1)
        return np.argsort(np.argsort(fre_scores)) / scaling_factor
