// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { JobInfoStatus } from '../../../../core/tests/dtos/tests.interface';
import { getMockedTest } from '../../../../core/tests/services/tests-utils';
import { Test } from '../../../../core/tests/tests.interface';
import { projectRender as render } from '../../../../test-utils/project-provider-render';
import { TestDetails } from './test-details.component';

const inMemoryProjectService = createInMemoryProjectService();

const mockedScores = [
    {
        name: 'score-name-overall',
        labelId: 'null',
        value: 0.7,
    },
    {
        name: 'score-name',
        labelId: 'label-id',
        value: 0.2,
    },
];

const renderTestDetails = async (test?: Partial<Test> | undefined) => {
    await render(<TestDetails test={getMockedTest(test)} />, {
        services: {
            projectService: inMemoryProjectService,
        },
    });
};

describe('TestDetails', () => {
    const testName = 'mocked-test-name';

    it('renders initial score (labelId null)', async () => {
        const initialScore = mockedScores[0].value * 100;
        await renderTestDetails({ scores: mockedScores, testName });

        expect(screen.getByLabelText(`${testName} model score`)).toHaveAttribute('aria-valuenow', `${initialScore}`);
        expect(screen.getByLabelText('Model score value')).toHaveTextContent(`${initialScore}%`);
    });

    it('error test result', async () => {
        await renderTestDetails({ jobInfo: { id: 'job-info-id', status: JobInfoStatus.ERROR } });

        expect(screen.getByText('No results')).toBeVisible();
        expect(screen.getByText('Please wait for the test job to finish.')).toBeVisible();
    });

    it('deleted test result info', async () => {
        await renderTestDetails({
            datasetsInfo: [
                {
                    id: 'dataset-id',
                    datasetName: 'dataset-name',
                    isDeleted: true,
                    numberOfFrames: 2,
                    numberOfImages: 4,
                    numberOfSamples: 1,
                },
            ],
        });

        expect(screen.getByText('No results')).toBeVisible();
        expect(screen.getByText('The test results were deleted.')).toBeVisible();
    });

    it('does not render model accuracy if the score of the selected label is "undefined"', async () => {
        // "undefined" scores result from not finding a label id that matches the selected label.
        // that's why these 2 labelId's have '' as an id. By default the component's selected label has an
        // id of "null"
        const mockedScoresWithUndefined = [
            {
                name: 'score-name-overall',
                labelId: '',
                value: 0.7,
            },
            {
                name: 'score-name',
                labelId: '',
                value: 0.2,
            },
        ];
        await renderTestDetails({ scores: mockedScoresWithUndefined, testName });

        const scoreContainer = screen.getByTestId('test-model-accuracy');

        expect(scoreContainer.parentElement).toHaveTextContent('N/A');
    });
});
