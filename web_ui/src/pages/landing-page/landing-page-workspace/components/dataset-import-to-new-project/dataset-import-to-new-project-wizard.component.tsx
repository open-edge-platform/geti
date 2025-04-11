// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useCallback } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';
import Checkmark from '@spectrum-icons/workflow/Checkmark';
import capitalize from 'lodash/capitalize';
import isEmpty from 'lodash/isEmpty';

import { DATASET_IMPORT_TO_NEW_PROJECT_STEP } from '../../../../../core/datasets/dataset.enum';
import { DatasetImportToNewProjectItem } from '../../../../../core/datasets/dataset.interface';

import classes from './dataset-import-to-new-project.module.scss';

interface DatasetImportToNewProjectWizardProps {
    datasetImportItem?: DatasetImportToNewProjectItem;
    patchDatasetImport: (item: Partial<DatasetImportToNewProjectItem>) => void;
}

export const DatasetImportToNewProjectWizard = ({
    datasetImportItem: uploadItem,
    patchDatasetImport,
}: DatasetImportToNewProjectWizardProps): JSX.Element => {
    const isCompleted = useCallback(
        (step: string): boolean => {
            if (!uploadItem) return false;

            const { activeStep, completedSteps, uploadId, projectName, taskType, labels } = uploadItem;
            const baseComplete = step !== activeStep && ((completedSteps as string[]) || []).includes(step);

            switch (step) {
                case DATASET_IMPORT_TO_NEW_PROJECT_STEP.DATASET:
                    return baseComplete && !!(uploadId as string)?.length;
                case DATASET_IMPORT_TO_NEW_PROJECT_STEP.DOMAIN:
                    return (
                        baseComplete &&
                        !!(projectName as string)?.trim().length &&
                        !!(taskType as string)?.trim().length
                    );
                case DATASET_IMPORT_TO_NEW_PROJECT_STEP.LABELS:
                    return baseComplete && !isEmpty(labels);
                default:
                    return baseComplete;
            }
        },
        [uploadItem]
    );

    const isActionAllowed = useCallback(
        (step: string): boolean => {
            if (!uploadItem) return false;

            const { activeStep, openedSteps } = uploadItem;

            return activeStep !== step && (openedSteps as string[]).includes(step);
        },
        [uploadItem]
    );

    const getStepNumberClass = useCallback(
        (step: string, idx: number, weak?: boolean): string => {
            let className = weak ? '' : `${classes.stepNumber}`;

            if ((!uploadItem && idx === 0) || uploadItem?.activeStep === step) {
                className = `${className} ${classes.active}`;
            }

            return className;
        },
        [uploadItem]
    );

    const getStepNumber = useCallback(
        (step: string, idx: number): JSX.Element => {
            if (!uploadItem) return <Text UNSAFE_className={getStepNumberClass(step, idx)}>{idx + 1}</Text>;

            if (isCompleted(step)) {
                return (
                    <Text UNSAFE_className={getStepNumberClass(step, idx)}>
                        <Checkmark size='S' />
                    </Text>
                );
            }

            return <Text UNSAFE_className={getStepNumberClass(step, idx)}>{idx + 1}</Text>;
        },
        [getStepNumberClass, isCompleted, uploadItem]
    );

    return (
        <View UNSAFE_className={classes.wizard}>
            <Flex alignItems='center' justifyContent='center' gap='size-100'>
                {Object.values(DATASET_IMPORT_TO_NEW_PROJECT_STEP).map((step: string, idx: number) => (
                    <Flex
                        gap='size-100'
                        alignItems='center'
                        key={`step-${idx}-${step}`}
                        flex={idx < Object.values(DATASET_IMPORT_TO_NEW_PROJECT_STEP).length - 1 ? 1 : 0}
                    >
                        <div
                            onClick={() => {
                                if (!uploadItem || !isActionAllowed(step)) return;
                                patchDatasetImport({
                                    id: uploadItem.id as string,
                                    activeStep: step as DATASET_IMPORT_TO_NEW_PROJECT_STEP,
                                });
                            }}
                        >
                            <Flex
                                alignItems='center'
                                gap='size-100'
                                UNSAFE_style={{
                                    cursor: uploadItem && isActionAllowed(step) ? 'pointer' : 'default',
                                    width: 'max-content',
                                }}
                            >
                                {getStepNumber(step, idx)}
                                <Text UNSAFE_className={getStepNumberClass(step, idx, true)}>{capitalize(step)}</Text>
                            </Flex>
                        </div>
                        {idx < Object.values(DATASET_IMPORT_TO_NEW_PROJECT_STEP).length - 1 && (
                            <View key={`step-divider-${idx}-${step}`} UNSAFE_className={classes.stepDivider}></View>
                        )}
                    </Flex>
                ))}
            </Flex>
        </View>
    );
};
