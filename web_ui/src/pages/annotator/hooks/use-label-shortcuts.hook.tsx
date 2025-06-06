// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useFeatureFlags } from '../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Label } from '../../../core/labels/label.interface';
import { isExclusive, isNonBackgroundLabel } from '../../../core/labels/utils';
import { hasEqualId } from '../../../shared/utils';
import { useTask } from '../providers/task-provider/task-provider.component';

// For now we'll remove any empty labels from a sub task if we're in the "All tasks" view
export const useLabelShortcuts = (): Label[] => {
    const { FEATURE_FLAG_ANNOTATION_HOLE } = useFeatureFlags();
    const { labels: taskLabels, tasks, selectedTask } = useTask();

    if (tasks.length < 2 || selectedTask !== null) {
        const filteredTaskLabels = taskLabels.filter((label) =>
            tasks.some((task) => task.labels.some(hasEqualId(label.id)))
        );

        return FEATURE_FLAG_ANNOTATION_HOLE ? filteredTaskLabels : filteredTaskLabels.filter(isNonBackgroundLabel);
    }

    const secondTask = tasks[1];

    const filteredTaskLabels = taskLabels.filter((label) => {
        if (!isExclusive(label)) {
            return true;
        }

        return (
            !secondTask.labels.some(hasEqualId(label.id)) &&
            tasks.some((task) => task.labels.some(hasEqualId(label.id)))
        );
    });

    return FEATURE_FLAG_ANNOTATION_HOLE ? filteredTaskLabels : filteredTaskLabels.filter(isNonBackgroundLabel);
};
