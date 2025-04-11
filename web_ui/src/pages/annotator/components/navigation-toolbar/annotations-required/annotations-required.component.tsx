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

import { useCallback, useRef } from 'react';

import { DialogTrigger, Flex, Text, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import isNil from 'lodash/isNil';

import { ProjectIdentifier } from '../../../../../core/projects/core.interface';
import { useProjectStatus } from '../../../../../core/projects/hooks/use-project-status.hook';
import { Task } from '../../../../../core/projects/task.interface';
import { ActionButton } from '../../../../../shared/components/button/button.component';
import { useAutoTrainingTasksConfig } from '../../../../../shared/components/header/active-learning-configuration/use-tasks-auto-training-config.hook';
import { getAllAutoTrainingValue } from '../../../../../shared/components/header/active-learning-configuration/util';
import { hasEqualId } from '../../../../../shared/utils';
import { useProject } from '../../../../project-details/providers/project-provider/project-provider.component';
import { TaskRequiredAnnotations, useRequiredAnnotations } from '../../../hooks/use-required-annotations.hook';
import { DetailsDialog } from './details-dialog.component';
import { NoAnnotationsRequired } from './no-annotations-required.component';

import classes from './annotations-required.module.scss';

interface AnnotationsRequiredProps {
    id?: string;
    selectedTask: Task | null;
}

export const getAnnotationsDetails = (isAutoTrainingOn: boolean, requiredAnnotations: TaskRequiredAnnotations[]) => {
    if (isAutoTrainingOn) {
        return {
            text: 'Annotations required',
            styles: {
                backgroundColor: 'var(--brand-coral-coral-shade1)',
            },
            total: requiredAnnotations.reduce((acc, currentTask) => acc + currentTask.value, 0),
        };
    }

    return {
        text: 'New annotations',
        styles: {
            color: 'var(--spectrum-global-color-gray-50)',
            backgroundColor: 'var(--brand-moss)',
        },
        total: requiredAnnotations.reduce((acc, currentTask) => acc + currentTask.newAnnotations, 0),
    };
};

const useIsTaskTraining = (projectIdentifier: ProjectIdentifier) => {
    const { data: projectStatus } = useProjectStatus(projectIdentifier);

    return useCallback(
        (task: Task | null) => {
            if (!task) {
                return !!projectStatus?.isTraining;
            }

            const projectTasks = projectStatus?.tasks || [];

            return !!projectTasks.find(hasEqualId(task.id))?.is_training;
        },
        [projectStatus?.isTraining, projectStatus?.tasks]
    );
};

export const AnnotationsRequired = ({ id, selectedTask }: AnnotationsRequiredProps): JSX.Element => {
    const { projectIdentifier, project } = useProject();
    const containerRef = useRef<HTMLDivElement>({} as HTMLDivElement);
    const isTaskTraining = useIsTaskTraining(projectIdentifier);
    const requiredAnnotations = useRequiredAnnotations(selectedTask);
    const { autoTrainingTasks, isLoading: isTasksConfigLoading } = useAutoTrainingTasksConfig(
        projectIdentifier,
        project.tasks
    );

    const { clientWidth } = containerRef?.current ?? {};
    const isAllTasks = isNil(selectedTask);
    const autoTrainingSelectedTask = autoTrainingTasks.find(({ task }) => isEqual(task.id, selectedTask?.id));
    const allAutoTrainingValue = getAllAutoTrainingValue(autoTrainingTasks);
    const isAutoTrainingOn = isAllTasks
        ? Boolean(allAutoTrainingValue)
        : Boolean(autoTrainingSelectedTask?.trainingConfig?.value);
    const annotationsDetails = getAnnotationsDetails(isAutoTrainingOn, requiredAnnotations);

    // We need to show the training information per task
    const isTraining = isTaskTraining(selectedTask);

    // We will only enable the dialog if we're on 'All tasks' or if we're on a specific task that has 'details'
    const isDialogDisabled = !requiredAnnotations.some(({ details }) => !isEmpty(details)) && !isNil(selectedTask);

    if (isTasksConfigLoading || isTraining) {
        return <NoAnnotationsRequired id={id} ref={containerRef} />;
    }

    return (
        <DialogTrigger type='popover' hideArrow isDismissable>
            <div ref={containerRef} style={{ flexGrow: 1 }} id={`is-training-${isTraining}-id`}>
                <ActionButton isQuiet isDisabled={isDialogDisabled} UNSAFE_className={classes.button}>
                    <Flex
                        id={id}
                        direction='row-reverse'
                        alignItems='center'
                        data-testid='required-annotations-value'
                        marginX={{ base: '0px', L: 'size-100' }}
                    >
                        <Text id='annotations-required-id'>{annotationsDetails.text}:</Text>
                        <View
                            id={'annotations-required-number-id'}
                            paddingY='size-10'
                            paddingX='size-65'
                            borderRadius='small'
                            UNSAFE_style={annotationsDetails.styles}
                        >
                            {annotationsDetails.total}
                        </View>
                    </Flex>
                </ActionButton>
            </div>

            <DetailsDialog
                clientWidth={clientWidth}
                isAutoTrainingOn={isAutoTrainingOn}
                requiredAnnotations={requiredAnnotations}
            />
        </DialogTrigger>
    );
};
