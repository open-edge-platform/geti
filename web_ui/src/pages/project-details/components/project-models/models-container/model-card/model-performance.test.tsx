// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { PerformanceType } from '../../../../../../core/projects/task.interface';
import { providersRender as render } from '../../../../../../test-utils/required-providers-render';
import { checkTooltip } from '../../../../../../test-utils/utils';
import { ModelPerformance } from './model-performance.component';
import {
    ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE,
    ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE,
    ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE,
    DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE,
} from './utils';

describe('ModelPerformance', () => {
    const genericId = 'model-performance';

    beforeAll(() => {
        jest.useFakeTimers();
    });

    beforeEach(() => {
        jest.runAllTimers();
    });

    it("shows a model's performance", async () => {
        render(
            <ModelPerformance
                genericId={genericId}
                performance={{
                    type: PerformanceType.DEFAULT,
                    score: 0.1,
                }}
            />
        );

        expect(screen.getByLabelText('Score value')).toHaveTextContent('10%');

        await checkTooltip(screen.getByText('Score'), DEFAULT_PERFORMANCE_TOOLTIP_MESSAGE);
    });

    it("shows an anomaly model's local and global performance", async () => {
        render(
            <ModelPerformance
                genericId={genericId}
                performance={{
                    type: PerformanceType.ANOMALY,
                    globalScore: 0.9,
                    localScore: 0.4,
                }}
            />
        );

        expect(screen.getByLabelText('Image score value')).toHaveTextContent('90%');

        expect(screen.getByLabelText('Object score value')).toHaveTextContent('40%');

        await checkTooltip(screen.getByLabelText('Image score value'), ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE);

        await checkTooltip(screen.getByLabelText('Object score value'), ANOMALY_OBJECT_PERFORMANCE_TOOLTIP_MESSAGE);
    });

    it('tells the user to annotate more images to get a local performance score', async () => {
        render(
            <ModelPerformance
                genericId={genericId}
                performance={{
                    type: PerformanceType.ANOMALY,
                    globalScore: 0.9,
                    localScore: null,
                }}
            />
        );

        expect(screen.getByLabelText('Image score value')).toHaveTextContent('90%');

        expect(screen.queryByAltText('Object score value')).not.toBeInTheDocument();

        await checkTooltip(screen.getByLabelText('Image score value'), ANOMALY_IMAGE_PERFORMANCE_TOOLTIP_MESSAGE);

        await checkTooltip(
            screen.getByText('Object score not available'),
            ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE
        );
    });
});
