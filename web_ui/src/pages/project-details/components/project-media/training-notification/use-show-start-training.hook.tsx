// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useMemo, useRef } from 'react';

import { OverlayTriggerState } from '@react-stately/overlays';

import { CREDIT_COST_PER_IMAGE_OR_VIDEO } from '../../../../../core/credits/credits.interface';
import { useCreditsQueries } from '../../../../../core/credits/hooks/use-credits-api.hook';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Label } from '../../../../../core/labels/label.interface';
import { isAnomalous, isExclusive } from '../../../../../core/labels/utils';
import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { useApplicationServices } from '../../../../../core/services/application-services-provider.component';
import { useOrganizationIdentifier } from '../../../../../hooks/use-organization-identifier/use-organization-identifier.hook';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { MEDIA_CONTENT_BUCKET } from '../../../../../providers/media-upload-provider/media-upload.interface';
import { QuietToggleButton } from '../../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { useDatasetIdentifier } from '../../../../annotator/hooks/use-dataset-identifier.hook';
import { useAdvancedMediaFilter } from '../../../../media/hooks/media-items/advanced-media-filter.hook';
import { getRequiredAnomalyFilters } from '../../../../media/providers/utils';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { MIN_NUMBER_OF_ANOMALOUS_REQUIRED_MEDIA_ITEMS, MIN_NUMBER_OF_NORMAL_REQUIRED_MEDIA_ITEMS } from '../utils';

const getMinNumberOfRequiredMediaItems = (bucket: MEDIA_CONTENT_BUCKET) => {
    return bucket === MEDIA_CONTENT_BUCKET.NORMAL
        ? MIN_NUMBER_OF_NORMAL_REQUIRED_MEDIA_ITEMS
        : MIN_NUMBER_OF_ANOMALOUS_REQUIRED_MEDIA_ITEMS;
};

const useMediaQueryForLabel = (enabled: boolean, label: Label | undefined) => {
    const {
        project: { datasets },
    } = useProject();
    const datasetIdentifier = useDatasetIdentifier();
    const selectedDataset = datasets.find(({ id }) => id === datasetIdentifier.datasetId);

    const { mediaService } = useApplicationServices();
    const mediaFilterOptions = useMemo(() => (label === undefined ? {} : getRequiredAnomalyFilters(label.id)), [label]);

    return useAdvancedMediaFilter({
        datasetIdentifier,
        mediaFilterOptions,
        mediaService,
        // We only care about knowing how much images / frames are in a bucket, so returning
        // a single media item is fine
        mediaItemsLoadSize: 1,
        sortingOptions: {},
        queryOptions: { enabled: enabled && selectedDataset?.useForTraining },
    });
};

export const START_TRAINING_MESSAGE = 'You can start training the model now';
export const MORE_MEDIAS_MESSAGE =
    'You have to upload at least twelve normal and three anomalous images/frames to start training.';

export const useShowStartTraining = (trainModelDialogState: OverlayTriggerState) => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const {
        isSingleDomainProject,
        project: { performance, labels },
    } = useProject();
    const moreMediasRef = useRef('');
    const startTrainingRef = useRef('');
    const { useGetOrganizationBalanceQuery } = useCreditsQueries();
    const { organizationId } = useOrganizationIdentifier();
    const { addNotification, removeNotification } = useNotification();

    const enabled = isSingleDomainProject(isAnomalyDomain);
    const anomalousLabelQuery = useMediaQueryForLabel(enabled, labels.find(isAnomalous));
    const normalLabelQuery = useMediaQueryForLabel(enabled, labels.find(isExclusive));
    const { data: balance } = useGetOrganizationBalanceQuery(
        { organizationId },
        { enabled: FEATURE_FLAG_CREDIT_SYSTEM }
    );

    const finishedLoading = !(normalLabelQuery.isLoading || anomalousLabelQuery.isLoading);

    const totalAnomalous = anomalousLabelQuery.totalMatchedImages + anomalousLabelQuery.totalMatchedVideoFrames;
    const hasEnoughAnomalousMedia = getMinNumberOfRequiredMediaItems(MEDIA_CONTENT_BUCKET.ANOMALOUS) <= totalAnomalous;

    const totalNormal = normalLabelQuery.totalMatchedImages + normalLabelQuery.totalMatchedVideoFrames;
    const hasEnoughNormalMedia = getMinNumberOfRequiredMediaItems(MEDIA_CONTENT_BUCKET.NORMAL) <= totalNormal;

    const hasEnoughCredits =
        (totalNormal + totalAnomalous) * CREDIT_COST_PER_IMAGE_OR_VIDEO <= (balance?.available ?? 0);

    const projectHasTrainedModels =
        // NOTE:
        // For non-anomaly projects, we always get `score` with `null` or `someValue`
        // For anomaly projects we either get `score: null` if there's no trained models,
        // or { globalScore, localScore } otherwise
        performance.type === 'default_performance' ? performance.score !== null : performance.globalScore !== null;

    const showStartTraining = hasEnoughCredits || !FEATURE_FLAG_CREDIT_SYSTEM;
    const moreImagesNeeded = !hasEnoughNormalMedia || !hasEnoughAnomalousMedia;
    // Only show the notification if we have loaded media, the project hasn't been trained before
    const showNotification = finishedLoading && !projectHasTrainedModels;

    useEffect(() => {
        if (!showNotification) {
            return;
        }

        if (moreImagesNeeded) {
            removeNotification(startTrainingRef.current);
            moreMediasRef.current = addNotification({
                message: MORE_MEDIAS_MESSAGE,
                type: NOTIFICATION_TYPE.DEFAULT,
                dismiss: { duration: 0 }, //0 will act as infinite duration
            });
        }

        if (!moreImagesNeeded && showStartTraining) {
            removeNotification(moreMediasRef.current);
            startTrainingRef.current = addNotification({
                message: START_TRAINING_MESSAGE,
                type: NOTIFICATION_TYPE.INFO,
                dismiss: { duration: 0, click: false, touch: false },
                actionButtons: [
                    <QuietToggleButton key={'open-train-model'} onPress={trainModelDialogState.open}>
                        Train
                    </QuietToggleButton>,
                ],
            });
        }
    }, [
        addNotification,
        moreImagesNeeded,
        removeNotification,
        showNotification,
        showStartTraining,
        trainModelDialogState.open,
    ]);
};
