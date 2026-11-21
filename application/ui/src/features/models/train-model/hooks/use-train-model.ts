// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { isEqual } from 'lodash-es';

import { useTrainModelMutation } from '../api/use-train-model-mutation';
import { useUpdateTrainingConfigurationMutation } from '../api/use-update-training-configuration-mutation';
import { useTrainModelState } from '../train-model-provider.component';
import { getTrainingConfigurationUpdatePayload } from './utils';

export const useTrainModel = () => {
    const projectIdentifier = useProjectIdentifier();
    const trainModelMutation = useTrainModelMutation();
    const updateTrainingConfigurationMutation = useUpdateTrainingConfigurationMutation();

    const {
        selectedTrainingDevice,
        selectedDatasetSourceId,
        resolvedModelArchitectureId,
        isAdvancedSettingsMode,
        trainingConfiguration,
        selectedModelRevisionId,
        defaultTrainingConfiguration,
        projectTrainingConfiguration,
        datasetSources,
        modelRevisions,
    } = useTrainModelState();
    const parentModelRevisionId =
        modelRevisions.find((revision) => revision.id === selectedModelRevisionId)?.value ?? null;

    /**
     * Triggers model training with the following workflow:
     *
     * 1. Direct training — if advanced settings are off, or the displayed configuration
     *    and revision metric match the current project configuration, start immediately.
     *
     * 2. Configuration update + training — persist changed settings or the displayed
     *    revision metric before starting training:
     *      a. Persist the updated configuration first.
     *      b. On success, start the training job.
     *      c. If the training job itself fails, roll the configuration back to the previous
     *         values so the project is not left in an inconsistent state.
     */
    const trainModel = ({ onSuccess }: { onSuccess: () => void }) => {
        if (resolvedModelArchitectureId === null || selectedTrainingDevice === null) {
            return;
        }

        const datasetSource = datasetSources.find((source) => source.id === selectedDatasetSourceId);

        const trainModelMutationBody = {
            body: {
                project_id: projectIdentifier,
                job_type: 'train',
                parameters: {
                    device: selectedTrainingDevice,
                    model_architecture_id: resolvedModelArchitectureId,
                    parent_model_revision_id: parentModelRevisionId,
                    dataset_revision_id: datasetSource?.kind === 'revision' ? datasetSource.value : null,
                    dataset_view_id: datasetSource?.kind === 'view' ? datasetSource.value : null,
                },
            },
        } as const;

        const hasConfigurationChanged = !isEqual(defaultTrainingConfiguration, trainingConfiguration);
        const configurationPayload = getTrainingConfigurationUpdatePayload(trainingConfiguration);
        const projectPayload = getTrainingConfigurationUpdatePayload(projectTrainingConfiguration);
        const revisionMetricChanged =
            parentModelRevisionId !== null &&
            configurationPayload['evaluation.validation_metric'] !== undefined &&
            configurationPayload['evaluation.validation_metric'] !== projectPayload['evaluation.validation_metric'];

        if (isAdvancedSettingsMode && parentModelRevisionId !== null && projectTrainingConfiguration === undefined) {
            return;
        }

        if (!isAdvancedSettingsMode || (!hasConfigurationChanged && !revisionMetricChanged)) {
            trainModelMutation.mutate(trainModelMutationBody, { onSuccess });

            return;
        }

        const configurationParams = {
            params: {
                path: {
                    project_id: projectIdentifier,
                },
                query: {
                    model_architecture_id: resolvedModelArchitectureId,
                },
            },
        };

        updateTrainingConfigurationMutation.mutate(
            {
                ...configurationParams,
                body: hasConfigurationChanged
                    ? configurationPayload
                    : { 'evaluation.validation_metric': configurationPayload['evaluation.validation_metric'] },
            },
            {
                onSuccess: () => {
                    trainModelMutation.mutate(trainModelMutationBody, {
                        onSuccess,
                        onError: () => {
                            updateTrainingConfigurationMutation.mutate({
                                ...configurationParams,
                                body: hasConfigurationChanged
                                    ? getTrainingConfigurationUpdatePayload(
                                          projectTrainingConfiguration ?? defaultTrainingConfiguration
                                      )
                                    : {
                                          'evaluation.validation_metric':
                                              projectPayload['evaluation.validation_metric'],
                                      },
                            });
                        },
                    });
                },
            }
        );
    };

    return {
        trainModel,
        isPending:
            trainModelMutation.isPending ||
            updateTrainingConfigurationMutation.isPending ||
            (isAdvancedSettingsMode && parentModelRevisionId !== null && projectTrainingConfiguration === undefined),
    };
};
