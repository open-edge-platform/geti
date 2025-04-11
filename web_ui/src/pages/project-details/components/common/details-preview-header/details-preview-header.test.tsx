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

import { fireEvent, screen } from '@testing-library/react';

import { DOMAIN } from '../../../../../core/projects/core.interface';
import { getMockedTestImageMediaItem } from '../../../../../core/tests/services/tests-utils';
import { getMockedLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { ANNOTATOR_MODE } from '../../../../annotator/core/annotation-tool-context.interface';
import {
    PredictionContextProps,
    usePrediction,
} from '../../../../annotator/providers/prediction-provider/prediction-provider.component';
import { useTask } from '../../../../annotator/providers/task-provider/task-provider.component';
import { DetailsPreviewHeader } from './details-preview-header.component';

jest.mock('../../../../annotator/providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../../../annotator/providers/task-provider/task-provider.component'),
    useTask: jest.fn(() => ({
        selectedTask: undefined,
        tasks: [],
    })),
}));

jest.mock('../../../../annotator/providers/prediction-provider/prediction-provider.component', () => ({
    ...jest.requireActual('../../../../annotator/providers/prediction-provider/prediction-provider.component'),
    usePrediction: jest.fn(),
}));

describe('Header component', () => {
    jest.mocked(usePrediction).mockReturnValue({
        isExplanationVisible: false,
        setExplanationVisible: jest.fn(),
    } as unknown as PredictionContextProps);

    const fakeTask = { id: '1234', title: 'Segmentation', labels: [], domain: DOMAIN.SEGMENTATION };

    it('Check if there is a buttons to switch modes by default', async () => {
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({
                selectedTask: fakeTask,
                tasks: [fakeTask],
            })
        );

        render(
            <DetailsPreviewHeader
                tasks={[]}
                selectedTask={null}
                mode={ANNOTATOR_MODE.ACTIVE_LEARNING}
                setMode={jest.fn()}
            />
        );

        expect(screen.getByText('Annotations')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Select prediction mode' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Select annotation mode' })).toBeInTheDocument();
        expect(
            screen.queryByText('Predictions are only available in the active model. Displaying annotations.')
        ).not.toBeInTheDocument();
    });

    it('Check if there is no buttons to switch modes is it was disabled', async () => {
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({
                selectedTask: fakeTask,
                tasks: [fakeTask],
            })
        );

        render(
            <DetailsPreviewHeader
                tasks={[]}
                selectedTask={null}
                disableActionModes
                mode={ANNOTATOR_MODE.ACTIVE_LEARNING}
                setMode={jest.fn()}
            />
        );

        expect(screen.queryByRole('button', { name: 'Select prediction mode' })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: 'Select annotation mode' })).not.toBeInTheDocument();
        expect(
            screen.getByText('Predictions are only available in the active model. Displaying annotations.')
        ).toBeInTheDocument();
    });

    it('Check if clicking of mode buttons calls proper function', async () => {
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({
                selectedTask: fakeTask,
                tasks: [fakeTask],
            })
        );

        const setModeMock = jest.fn();

        render(
            <DetailsPreviewHeader
                tasks={[]}
                selectedTask={null}
                mode={ANNOTATOR_MODE.ACTIVE_LEARNING}
                setMode={setModeMock}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'Select prediction mode' }));
        expect(setModeMock).toHaveBeenCalled();
    });

    it('prediction mode, render labels scores', async () => {
        jest.useFakeTimers();

        const mockedLabels = [
            getMockedLabel({ id: 'labelOne', name: 'labelOne', group: 'default' }),
            getMockedLabel({ id: 'labelTwo', name: 'labelTwo', group: 'default' }),
        ];

        const mockedScores = [
            { name: '', labelId: null, value: 0.5 },
            { name: 'labelOne', labelId: 'labelOne', value: 0.2 },
            { name: 'labelTwo', labelId: 'labelTwo', value: 0.4 },
        ];
        const mockedTestImage = getMockedTestImageMediaItem(undefined, mockedScores);
        const mockedTasks = [getMockedTask({ labels: mockedLabels, domain: DOMAIN.CLASSIFICATION })];

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({
                selectedTask: fakeTask,
                tasks: [fakeTask],
            })
        );

        render(
            <DetailsPreviewHeader
                tasks={mockedTasks}
                testResult={mockedTestImage.testResult}
                selectedTask={mockedTasks[0]}
                mode={ANNOTATOR_MODE.PREDICTION}
                setMode={jest.fn()}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: 'labels scores' }));
        jest.advanceTimersByTime(1000);

        expect(screen.getByText('Predictions')).toBeVisible();
        expect(screen.getByText('Model score: 50%')).toBeVisible();

        expect(screen.getByRole('listitem', { name: `label item labelOne` })).toHaveTextContent(`labelOne20%`);
        expect(screen.getByRole('listitem', { name: `label item labelTwo` })).toHaveTextContent(`labelTwo40%`);

        jest.useRealTimers();
    });
});
