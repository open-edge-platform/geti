// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedSupportedAlgorithm } from '../../../../../../../core/supported-algorithms/services/test-utils';
import { moveActiveArchitectureToBeRightAfterRecommended } from './utils';

describe('moveActiveArchitectureToBeRightAfterRecommended', () => {
    it('returns unsorted algorithms when active model is null', () => {
        const activeModelTemplateId = null;
        const recommendedAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '1' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '2' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '3' }),
        ];
        const otherAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '4' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '5' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '6' }),
        ];
        expect(
            moveActiveArchitectureToBeRightAfterRecommended(
                recommendedAlgorithms,
                otherAlgorithms,
                activeModelTemplateId
            )
        ).toEqual([otherAlgorithms, recommendedAlgorithms]);
    });

    it('returns unsorted algorithms when active model is in recommended algorithms', () => {
        const activeModelTemplateId = '1';
        const recommendedAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '1' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '2' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '3' }),
        ];
        const otherAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '4' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '5' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '6' }),
        ];
        expect(
            moveActiveArchitectureToBeRightAfterRecommended(
                recommendedAlgorithms,
                otherAlgorithms,
                activeModelTemplateId
            )
        ).toEqual([otherAlgorithms, recommendedAlgorithms]);
    });

    it('returns unsorted algorithms when active model is not part of the algorithms [it should never happen]', () => {
        const activeModelTemplateId = '11';
        const recommendedAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '1' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '2' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '3' }),
        ];
        const otherAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '4' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '5' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '6' }),
        ];
        expect(
            moveActiveArchitectureToBeRightAfterRecommended(
                recommendedAlgorithms,
                otherAlgorithms,
                activeModelTemplateId
            )
        ).toEqual([otherAlgorithms, recommendedAlgorithms]);
    });

    it('moves active algorithm to be the first in the other algorithms list', () => {
        const activeModelTemplateId = '6';

        const recommendedAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '1' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '2' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '3' }),
        ];
        const otherAlgorithms = [
            getMockedSupportedAlgorithm({ modelTemplateId: '4' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '5' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '6' }),
        ];

        const [newOtherAlgorithms, newRecommendedAlgorithms] = moveActiveArchitectureToBeRightAfterRecommended(
            recommendedAlgorithms,
            otherAlgorithms,
            activeModelTemplateId
        );

        expect(newOtherAlgorithms).toEqual([
            getMockedSupportedAlgorithm({ modelTemplateId: '6' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '4' }),
            getMockedSupportedAlgorithm({ modelTemplateId: '5' }),
        ]);
        expect(newRecommendedAlgorithms).toEqual(recommendedAlgorithms);
    });
});
