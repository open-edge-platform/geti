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
