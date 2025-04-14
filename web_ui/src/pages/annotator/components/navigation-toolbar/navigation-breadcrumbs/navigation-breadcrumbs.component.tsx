// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Task } from '../../../../../core/projects/task.interface';
import { useAnnotationToolContext } from '../../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { useSubmitAnnotations } from '../../../providers/submit-annotations-provider/submit-annotations-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { TasksBreadcrumbs } from './tasks-breadcrumbs.component';

export const NavigationBreadcrumbs = (): JSX.Element => {
    const { setSelectedTask, selectedTask, tasks } = useTask();
    const { confirmSaveAnnotations } = useSubmitAnnotations();
    const { toggleToolOnTaskChange } = useAnnotationToolContext();

    const selectTask = (task: Task | null) => {
        if (selectedTask?.id === task?.id) {
            return;
        }

        confirmSaveAnnotations(async () => {
            const newSelectedTask = task ?? null;

            toggleToolOnTaskChange(newSelectedTask);
            setSelectedTask(newSelectedTask);
        });
    };

    return <TasksBreadcrumbs tasks={tasks} selectTask={selectTask} selectedTask={selectedTask} />;
};
