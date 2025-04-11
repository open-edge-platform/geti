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

import isEmpty from 'lodash/isEmpty';

import { TrainingBodyDTO } from '../../../../../core/models/dtos/train-model.interface';
import { LifecycleStage } from '../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import {
    ModelTemplatesNames,
    SupportedAlgorithm,
} from '../../../../../core/supported-algorithms/supported-algorithms.interface';
import { ConfigurableParametersTaskChain } from '../../../../../shared/components/configurable-parameters/configurable-parameters.interface';
import { sortAscending } from '../../../../../shared/utils';
import { getTrainingConfigParametersDTO } from '../utils';
import { Template, TEMPLATES } from './model-templates-selection/model-templates-list/model-templates-list.interface';

interface SpeedAccuracyBalanceAlgorithms {
    speedAlgorithm?: SupportedAlgorithm;
    balanceAlgorithm?: SupportedAlgorithm;
    accuracyAlgorithm: SupportedAlgorithm;
}

interface ModelTemplatesDetails {
    templateName: string;
    summary: string;
}

const getDefaultAlgorithm = (supportedAlgorithms: SupportedAlgorithm[]): SupportedAlgorithm => {
    // it's algorithm that is selected by default
    // we assert here because we are sure that one algorithm has to be default one
    return supportedAlgorithms.find(({ isDefaultAlgorithm }) => isDefaultAlgorithm) as SupportedAlgorithm;
};

export const getModelTemplatesAlgorithms = (
    supportedAlgorithms: SupportedAlgorithm[]
): SpeedAccuracyBalanceAlgorithms | undefined => {
    if (isEmpty(supportedAlgorithms)) {
        return undefined;
    }

    const sortedAlgorithms = sortAscending([...supportedAlgorithms], 'gigaflops');

    // we have three model templates
    if (sortedAlgorithms.length > 2) {
        const [speedAlgorithm] = sortedAlgorithms;
        const accuracyAlgorithm = sortedAlgorithms[sortedAlgorithms.length - 1];
        const middleIndex =
            sortedAlgorithms.length % 2 === 0 ? sortedAlgorithms.length / 2 : Math.floor(sortedAlgorithms.length / 2);

        let balanceAlgorithm: SupportedAlgorithm = sortedAlgorithms[middleIndex];

        // this is additional check to make sure, that we always have default algorithm in the model templates
        const noneOfAlgorithmIsDefault = [speedAlgorithm, accuracyAlgorithm, sortedAlgorithms[middleIndex]].every(
            ({ isDefaultAlgorithm }) => !isDefaultAlgorithm
        );

        if (noneOfAlgorithmIsDefault) {
            balanceAlgorithm = getDefaultAlgorithm(supportedAlgorithms);
        }

        return {
            speedAlgorithm: { ...speedAlgorithm, templateName: ModelTemplatesNames.SPEED },
            accuracyAlgorithm: { ...accuracyAlgorithm, templateName: ModelTemplatesNames.ACCURACY },
            balanceAlgorithm: { ...balanceAlgorithm, templateName: ModelTemplatesNames.BALANCE },
        };
    }

    // we have two model templates: Accuracy and Speed
    if (sortedAlgorithms.length > 1) {
        const [speedAlgorithm, accuracyAlgorithm] = sortedAlgorithms;

        return {
            speedAlgorithm: { ...speedAlgorithm, templateName: ModelTemplatesNames.SPEED },
            accuracyAlgorithm: { ...accuracyAlgorithm, templateName: ModelTemplatesNames.ACCURACY },
        };
    }

    // I'm not sure if this case is valid, but it's worth to check
    // we have one model template: Accuracy

    return {
        accuracyAlgorithm: { ...sortedAlgorithms[0], templateName: ModelTemplatesNames.ACCURACY },
    };
};

export const getModelTemplateDetails = (
    modelTemplateId: string,
    supportedAlgorithms: SupportedAlgorithm[]
): ModelTemplatesDetails => {
    const groupedSupportedAlgorithms = getModelTemplatesAlgorithms(supportedAlgorithms);

    if (groupedSupportedAlgorithms !== undefined) {
        const { accuracyAlgorithm, speedAlgorithm, balanceAlgorithm } = groupedSupportedAlgorithms;
        const selectedAlgorithm = [speedAlgorithm, accuracyAlgorithm, balanceAlgorithm].find(
            (algorithm) => algorithm?.modelTemplateId === modelTemplateId
        );

        // Active model is not in recommended group
        if (selectedAlgorithm === undefined) {
            return {
                templateName: '',
                summary: supportedAlgorithms.find((algo) => algo.modelTemplateId === modelTemplateId)?.summary ?? '',
            };
        }

        return {
            templateName: selectedAlgorithm?.templateName ?? '',
            summary: selectedAlgorithm?.summary ?? '',
        };
    }

    return {
        templateName: '',
        summary: '',
    };
};

const mapAlgorithmsToTemplates = (
    templates: Template[],
    modelTemplatesAlgorithms: SpeedAccuracyBalanceAlgorithms | undefined
): Template[] => {
    // DO NOT MAP TEMPLATES IF THEY DO NOT HAVE MODEL TEMPLATE ID
    if (modelTemplatesAlgorithms === undefined) {
        return [];
    }

    const { speedAlgorithm, accuracyAlgorithm, balanceAlgorithm } = modelTemplatesAlgorithms;

    const isActive = ({ lifecycleStage }: SupportedAlgorithm) => lifecycleStage === LifecycleStage.ACTIVE;
    const getProperties = (data: SupportedAlgorithm) => {
        return {
            name: data.name,
            modelTemplateId: data.modelTemplateId,
            summary: data.summary,
            isDefaultAlgorithm: data.isDefaultAlgorithm,
            performanceCategory: data.performanceCategory,
            lifecycleStage: data.lifecycleStage,
            gigaflops: data.gigaflops,
            modelSize: data.modelSize,
        };
    };

    return templates.reduce<Template[]>((prevTemplates, currTemplate) => {
        if (isActive(accuracyAlgorithm) && currTemplate.text === ModelTemplatesNames.ACCURACY) {
            return [
                ...prevTemplates,
                {
                    ...currTemplate,
                    ...getProperties(accuracyAlgorithm),
                },
            ];
        }

        if (isActive(accuracyAlgorithm) && currTemplate.text === ModelTemplatesNames.SPEED && speedAlgorithm) {
            return [
                ...prevTemplates,
                {
                    ...currTemplate,
                    ...getProperties(speedAlgorithm),
                },
            ];
        }

        if (isActive(accuracyAlgorithm) && currTemplate.text === ModelTemplatesNames.BALANCE && balanceAlgorithm) {
            return [
                ...prevTemplates,
                {
                    ...currTemplate,
                    ...getProperties(balanceAlgorithm),
                },
            ];
        }

        return prevTemplates;
    }, []);
};

export const getModelTemplates = (supportedAlgorithms: SupportedAlgorithm[]): Template[] => {
    if (supportedAlgorithms === undefined) {
        return [];
    }

    const modelTemplatesAlgorithms = getModelTemplatesAlgorithms(supportedAlgorithms);

    return mapAlgorithmsToTemplates(TEMPLATES, modelTemplatesAlgorithms);
};

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
