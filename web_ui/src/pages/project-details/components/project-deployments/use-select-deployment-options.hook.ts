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

import { useMemo, useState } from 'react';

import { Task } from '../../../../core/projects/task.interface';
import { DeployModelByTask } from './interfaces';

interface UseStepperProps {
    modelSelection: DeployModelByTask;
    tasks: Task[];
}

interface StepperState {
    taskIndex: number;
    selectedTask: Task;
    showNextButton: boolean;
    prevButtonEnabled: boolean;
}

interface UseStepperResult extends StepperState {
    next: () => void;
    previous: () => void;
    downloadEnabled: boolean;
    nextButtonEnabled: boolean;
}

export const useSelectDeploymentOptions = ({ modelSelection, tasks }: UseStepperProps): UseStepperResult => {
    const [configuration, setConfiguration] = useState<StepperState>({
        taskIndex: 0,
        selectedTask: tasks[0],
        showNextButton: true,
        prevButtonEnabled: false,
    });

    const downloadEnabled = useMemo(() => {
        if (Object.keys(modelSelection).length !== tasks.length) {
            return false;
        }

        return Object.values(modelSelection).every((model) => model.optimisationId);
    }, [modelSelection, tasks.length]);

    const nextButtonEnabled = useMemo(() => {
        const currentSelection = modelSelection[configuration.selectedTask.id];

        return !!currentSelection?.optimisationId;
    }, [configuration.selectedTask.id, modelSelection]);

    const next = () => {
        setConfiguration((prevConfig) => {
            const nextIndex = prevConfig.taskIndex + 1;

            return {
                ...configuration,
                taskIndex: nextIndex,
                selectedTask: tasks[nextIndex],
                showNextButton: nextIndex < tasks.length - 1,
                prevButtonEnabled: true,
            };
        });
    };

    const previous = () => {
        setConfiguration((prevConfig) => {
            const previousIndex = Math.max(prevConfig.taskIndex - 1, 0);

            return {
                ...configuration,
                taskIndex: previousIndex,
                selectedTask: tasks[previousIndex],
                showNextButton: true,
                prevButtonEnabled: previousIndex > 0,
            };
        });
    };

    return { ...configuration, next, previous, downloadEnabled, nextButtonEnabled };
};
