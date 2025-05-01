// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ConfigurableParametersTaskChain } from '@shared/components/configurable-parameters/configurable-parameters.interface';

import { TrainingBodyDTO } from '../../../../../core/models/dtos/train-model.interface';
import { getTrainingConfigParametersDTO } from '../utils';

interface TrainingBody {
    taskId: string;
    trainFromScratch: boolean;
    isReshufflingSubsetsEnabled: boolean;
    modelTemplateId: string | undefined;
    configParameters: ConfigurableParametersTaskChain | undefined;
    maxTrainingDatasetSize?: number;
}

export const getTrainingBodyDTO = ({
    taskId,
    trainFromScratch,
    modelTemplateId,
    configParameters,
    maxTrainingDatasetSize,
    isReshufflingSubsetsEnabled,
}: TrainingBody): TrainingBodyDTO => {
    // send config parameters only when custom training was selected
    return {
        train_from_scratch: trainFromScratch,
        reshuffle_subsets: isReshufflingSubsetsEnabled,
        model_template_id: modelTemplateId,
        task_id: taskId,
        hyper_parameters: configParameters ? getTrainingConfigParametersDTO(configParameters) : undefined,
        max_training_dataset_size: maxTrainingDatasetSize,
    };
};

export const TRAIN_FROM_SCRATCH_TOOLTIP_MSG = 'Ignore the training history, and retrain using the pre-trained weights.';
export const RESHUFFLE_SUBSETS_TOOLTIP_MSG =
    'Reassign all dataset items to train, validation, and test subsets from scratch. Previous splits will not be ' +
    'retained. Only available when training from scratch is enabled.';
