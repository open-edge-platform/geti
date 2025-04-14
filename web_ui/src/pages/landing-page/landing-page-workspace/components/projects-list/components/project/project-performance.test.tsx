// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../../../../../core/projects/core.interface';
import { PerformanceType } from '../../../../../../../core/projects/task.interface';
import { providersRender as render } from '../../../../../../../test-utils/required-providers-render';
import { ProjectPerformance } from './project-performance.component';

describe('ProjectPerformance', () => {
    it('should display performance for single (not anomaly detection, anomaly segmentation) task', () => {
        render(
            <ProjectPerformance
                performance={{
                    type: PerformanceType.DEFAULT,
                    score: 0.2,
                    taskPerformances: [
                        {
                            domain: DOMAIN.DETECTION,
                            taskNodeId: 'detection-id',
                            score: {
                                value: 0.2,
                                metricType: 'f-measure',
                            },
                        },
                    ],
                }}
            />
        );

        const performance = screen.getByLabelText('Metric type: f-measure');

        expect(performance).toBeVisible();
        expect(performance).toHaveAttribute('aria-valuenow', '20');
    });

    it('should display performance for task chain', () => {
        render(
            <ProjectPerformance
                performance={{
                    type: PerformanceType.DEFAULT,
                    score: 0.2,
                    taskPerformances: [
                        {
                            domain: DOMAIN.DETECTION,
                            taskNodeId: 'detection-id',
                            score: {
                                value: 0.2,
                                metricType: 'f-measure',
                            },
                        },
                        {
                            domain: DOMAIN.SEGMENTATION,
                            taskNodeId: 'segmentation-id',
                            score: {
                                value: 0.8,
                                metricType: 'accuracy',
                            },
                        },
                    ],
                }}
            />
        );

        const detectionPerformance = screen.getByLabelText('Detection - metric type: f-measure');
        const segmentationPerformance = screen.getByLabelText('Segmentation - metric type: accuracy');

        expect(detectionPerformance).toBeVisible();
        expect(detectionPerformance).toHaveAttribute('aria-valuenow', '20');

        expect(segmentationPerformance).toBeVisible();
        expect(segmentationPerformance).toHaveAttribute('aria-valuenow', '80');
    });

    it('should display performance for single anomaly detection task', () => {
        render(
            <ProjectPerformance
                performance={{
                    type: PerformanceType.ANOMALY,
                    globalScore: 0.8,
                    localScore: 0.5,
                    score: 0.8,
                    taskPerformances: [
                        {
                            domain: DOMAIN.ANOMALY_DETECTION,
                            taskNodeId: 'detection-id',
                            score: {
                                value: 0.8,
                                metricType: 'f-measure',
                            },
                            globalScore: {
                                value: 0.8,
                                metricType: 'f-measure',
                            },
                            localScore: {
                                value: 0.5,
                                metricType: 'accuracy',
                            },
                        },
                    ],
                }}
            />
        );

        const localPerformance = screen.getByLabelText('Object score metric type: accuracy');
        const globalPerformance = screen.getByLabelText('Image score metric type: f-measure');

        expect(localPerformance).toBeVisible();
        expect(localPerformance).toHaveAttribute('aria-valuenow', '50');

        expect(globalPerformance).toBeVisible();
        expect(globalPerformance).toHaveAttribute('aria-valuenow', '80');
    });
});
