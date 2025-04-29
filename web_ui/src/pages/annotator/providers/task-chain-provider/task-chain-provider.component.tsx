// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { createContext, ReactNode, useContext, useMemo } from 'react';

import { Label } from '../../../../core/labels/label.interface';
import { Task } from '../../../../core/projects/task.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import {
    AnnotationSceneContext,
    useAnnotationScene,
} from '../annotation-scene-provider/annotation-scene-provider.component';
import { TaskChainContextProps } from './task-chain.interface';
import { useEnhanceScene } from './use-enhance-scene.hook';
import { getInputsOutputs } from './utils';

const TaskChainContext = createContext<TaskChainContextProps | undefined>(undefined);

interface TaskChainProviderProps {
    children: ReactNode;
    tasks: Task[];
    selectedTask: Task | null;
    defaultLabel: Label | null;
}

export const TaskChainProvider = ({
    children,
    tasks,
    selectedTask,
    defaultLabel,
}: TaskChainProviderProps): JSX.Element => {
    const parentScene = useAnnotationScene();
    const scene = useEnhanceScene(parentScene, tasks, selectedTask, defaultLabel);
    const { inputs, outputs } = useMemo(
        () => getInputsOutputs(scene.annotations, tasks, selectedTask),
        [scene.annotations, tasks, selectedTask]
    );

    return (
        <TaskChainContext.Provider value={{ inputs, outputs }}>
            <AnnotationSceneContext.Provider value={scene}>{children}</AnnotationSceneContext.Provider>
        </TaskChainContext.Provider>
    );
};

export const useTaskChain = (): TaskChainContextProps => {
    const context = useContext(TaskChainContext);

    if (context === undefined) {
        throw new MissingProviderError('useTaskChain', 'TaskChainProvider');
    }

    return context;
};
