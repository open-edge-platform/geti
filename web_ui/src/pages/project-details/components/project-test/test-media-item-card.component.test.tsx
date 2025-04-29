// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen, waitForElementToBeRemoved } from '@testing-library/react';

import { MEDIA_TYPE } from '../../../../core/media/base-media.interface';
import { TestMediaItem } from '../../../../core/tests/test-media.interface';
import { TestScore } from '../../../../core/tests/tests.interface';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedImageMediaItem } from '../../../../test-utils/mocked-items-factory/mocked-media';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { TestMediaItemCard } from './test-media-item-card.component';

const mockedScores = [
    { name: 'test all', labelId: null, value: 0.8 },
    { name: 'test 1', labelId: 'label-id-1', value: 0.1 },
    { name: 'test 2', labelId: 'label-id-2', value: 0.2 },
];
const mediaItem: TestMediaItem = {
    type: MEDIA_TYPE.IMAGE,
    media: getMockedImageMediaItem({ name: 'test image' }),
    testResult: {
        scores: mockedScores,
        annotationId: 'annotation id',
        predictionId: 'prediction id',
    },
};

const renderApp = async (labelScore: TestScore) => {
    await render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TestMediaItemCard
                mediaItem={mediaItem}
                labelScore={labelScore}
                selectMediaItem={jest.fn()}
                shouldShowAnnotationIndicator={false}
            />
        </ProjectProvider>
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
};

describe('TestMediaItemCard', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('"null" labelId render average score', async () => {
        const [averageScore] = mockedScores;
        await renderApp(averageScore);

        expect(screen.getByText(`${averageScore.value * 100}%`)).toBeVisible();
    });

    it('render label score', async () => {
        const labelScore = mockedScores.at(-1) as TestScore;
        await renderApp(labelScore);

        expect(screen.getByText(`${Number(labelScore?.value) * 100}%`)).toBeVisible();
    });
});
