// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useState } from 'react';

import { isEqual } from 'lodash-es';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Task } from '../../../../core/projects/task.interface';
import { FEATURES_KEYS } from '../../../../core/user-settings/dtos/user-settings.interface';
import { UserProjectSettings, UseSettings } from '../../../../core/user-settings/services/user-settings.interface';
import { getSettingsOfType } from '../../../../core/user-settings/utils';
import { usePrevious } from '../../../../hooks/use-previous/use-previous.hook';
import { SelectedMediaItem } from '../selected-media-item-provider/selected-media-item.interface';
import { getInitialAnnotations } from './utils';

export const useInitialAnnotation = (
    selectedMediaItem: SelectedMediaItem | undefined,
    selectedTask: Task | null,
    settings: UseSettings<UserProjectSettings>,
    isTaskChainSelectedClassification: boolean
) => {
    const [initialAnnotations, setInitialAnnotations] = useState<ReadonlyArray<Annotation>>(() => {
        const featuresConfig = getSettingsOfType(settings.config, FEATURES_KEYS);
        const isInitialPredictionsEnabled = Boolean(featuresConfig[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled);
        const initialPredictions = selectedMediaItem?.predictions?.annotations;
        return getInitialAnnotations(
            selectedMediaItem?.annotations,
            isInitialPredictionsEnabled ? initialPredictions : [],
            isTaskChainSelectedClassification
        );
    });
    const previousMediaItemIdentifier = usePrevious(selectedMediaItem?.identifier);
    const previousTaskId = usePrevious(selectedTask?.id);
    const previousPredictions = usePrevious(selectedMediaItem?.predictions?.annotations);

    useEffect(() => {
        const initialPredictions = selectedMediaItem?.predictions?.annotations;

        if (
            previousTaskId === selectedTask?.id &&
            initialPredictions?.length === previousPredictions?.length &&
            isEqual(previousMediaItemIdentifier, selectedMediaItem?.identifier)
        ) {
            return;
        }

        const featuresConfig = getSettingsOfType(settings.config, FEATURES_KEYS);
        const isInitialPredictionsEnabled = Boolean(featuresConfig[FEATURES_KEYS.INITIAL_PREDICTION].isEnabled);

        setInitialAnnotations(
            getInitialAnnotations(
                selectedMediaItem?.annotations,
                isInitialPredictionsEnabled ? initialPredictions : [],
                isTaskChainSelectedClassification
            )
        );
    }, [
        previousMediaItemIdentifier,
        selectedMediaItem?.identifier,
        selectedTask,
        previousTaskId,
        settings.config,
        selectedMediaItem?.annotations,
        selectedMediaItem?.predictions?.annotations,
        isTaskChainSelectedClassification,
        previousPredictions,
    ]);

    return initialAnnotations;
};
