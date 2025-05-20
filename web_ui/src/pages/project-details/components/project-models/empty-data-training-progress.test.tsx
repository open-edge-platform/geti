// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { screen } from '@testing-library/react';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { mockedRunningTrainingJobs } from '../../../../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { EmptyDataTrainingProgress } from './empty-data-training-progress.componen';
import { useTrainingProgress } from './training-progress/use-training-progress/use-training-progress.hook';

jest.mock('./training-progress/use-training-progress/use-training-progress.hook', () => ({
    useTrainingProgress: jest.fn(() => ({})),
}));

describe('EmptyDataTrainingProgress', () => {
    it('Single task project', async () => {
        const trainingDetails = mockedRunningTrainingJobs;

        jest.mocked(useTrainingProgress).mockImplementation(() => ({
            showTrainingProgress: true,
            trainingDetails,
        }));

        render(<EmptyDataTrainingProgress isTaskChain={false} tasks={[getMockedTask({ domain: DOMAIN.DETECTION })]} />);

        expect(screen.getByTestId('current-training-task-id')).toBeInTheDocument();
        expect(screen.getByTestId('task-value-id')).toHaveTextContent('Detection');
    });

    it('Task chain project', async () => {
        const trainingDetails = mockedRunningTrainingJobs;
        let taskIndex = 0;

        jest.mocked(useTrainingProgress).mockImplementation(() => {
            const currentTrainingDetails = !taskIndex
                ? trainingDetails
                : {
                      ...trainingDetails,
                      metadata: {
                          ...trainingDetails[0].metadata,
                          task: getMockedTask({ domain: DOMAIN.SEGMENTATION }),
                      },
                  };
            taskIndex = taskIndex + 1;

            return {
                showTrainingProgress: true,
                trainingDetails: currentTrainingDetails,
            } as ReturnType<typeof useTrainingProgress>;
        });

        render(
            <EmptyDataTrainingProgress
                isTaskChain={true}
                tasks={[getMockedTask({ domain: DOMAIN.DETECTION }), getMockedTask({ domain: DOMAIN.SEGMENTATION })]}
            />
        );
        expect(screen.getByTestId('detection-id')).toBeInTheDocument();
        expect(screen.getByTestId('segmentation-id')).toBeInTheDocument();
        expect(screen.getAllByTestId('current-training-task-id')).toHaveLength(2);

        const allTaskValueElements = screen.getAllByTestId('task-value-id');
        expect(allTaskValueElements).toHaveLength(2);
    });
});
