// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useTask } from '../providers/task-provider/task-provider.component';
import { useCollectPredictions } from './use-collect-predictions.hook';
import { useCollectToolsFrequencyMetrics } from './use-collect-tools-frequency-metrics.hook';

export const useCollectAnnotatorMetrics = () => {
    const { selectedTask, tasks } = useTask();

    const taskName = selectedTask === null ? tasks.map(({ domain }) => domain).join('-') : selectedTask.domain;

    const { collectToolsFrequencyMetric } = useCollectToolsFrequencyMetrics(taskName);
    const { collectPredictionsMetric } = useCollectPredictions(taskName);

    return { collectPredictionsMetric, collectToolsFrequencyMetric };
};
