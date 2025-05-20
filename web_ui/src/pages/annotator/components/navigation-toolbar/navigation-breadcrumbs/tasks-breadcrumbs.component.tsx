// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Item, Picker, useMediaQuery } from '@geti/ui';

import { isLargeSizeQuery } from '../../../../../../packages/ui/theme/queries';
import { Task } from '../../../../../core/projects/task.interface';
import { hasEqualId } from '../../../../../shared/utils';
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
