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
            screen.getByText('Object score is not available'),
            ANOMALY_OBJECT_PERFORMANCE_N_A_TOOLTIP_MESSAGE
        );
    });
});
