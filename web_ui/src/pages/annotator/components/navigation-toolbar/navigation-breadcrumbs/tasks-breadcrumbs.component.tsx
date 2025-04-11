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

import { Item, Picker } from '@adobe/react-spectrum';
import { useMediaQuery } from '@react-spectrum/utils';

import { Task } from '../../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../../shared/utils';
import { isLargeSizeQuery } from '../../../../../theme/queries';
import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { usePrediction } from '../../../providers/prediction-provider/prediction-provider.component';
import { BreadcrumbSegment } from './breadcrumb-segment.component';

import classes from './tasks-breadcrumbs.module.scss';

interface TasksBreadcrumbsProps {
    tasks: Task[];
    selectedTask: null | Task;
    selectTask: (task: Task | null) => void;
    allTasks?: boolean;
    position?: 'center' | 'start';
}

export const TasksBreadcrumbs = ({
    tasks,
    selectTask,
    selectedTask,
    allTasks = true,
    position = 'center',
}: TasksBreadcrumbsProps): JSX.Element => {
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const isSceneBusy = useIsSceneBusy();
    const { setExplanationVisible } = usePrediction();

    const handleSelectBreadcrumb = (id: string) => {
        const task = tasks.find(hasEqualId(id));
        selectTask(task ?? null);
    };

    if (!isLargeSize) {
        return (
            <Picker
                maxWidth='size-2000'
                selectedKey={selectedTask?.id ?? ''}
                items={[{ id: '', title: 'All tasks' }, ...tasks]}
                onSelectionChange={(key) => handleSelectBreadcrumb(String(key))}
                isDisabled={isSceneBusy}
            >
                {(item) => <Item key={item.id}>{item.title}</Item>}
            </Picker>
        );
    }

    return (
        <nav role='navigation' aria-label='navigation-breadcrumbs' className={classes.breadcrumbsNav}>
            <ul className={classes.breadcrumbsList} style={{ justifyContent: position }}>
                {allTasks && (
                    <BreadcrumbSegment
                        withoutArrow
                        key='all-tasks'
                        text='All Tasks'
                        idSuffix='all-tasks'
                        isSelected={!selectedTask}
                        isDisabled={isSceneBusy}
                        onClick={() => {
                            handleSelectBreadcrumb('');
                            setExplanationVisible(false);
                        }}
                    />
                )}

                {tasks.map((task) => (
                    <BreadcrumbSegment
                        key={task.id}
                        text={task.domain}
                        idSuffix={task.title}
                        isSelected={selectedTask?.id === task.id}
                        onClick={() => handleSelectBreadcrumb(task.id)}
                        isDisabled={isSceneBusy}
                    />
                ))}
            </ul>
        </nav>
    );
};
