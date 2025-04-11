// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { TASK_TYPE } from '../../../../core/projects/dtos/task.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { getMockedTest } from '../../../../core/tests/services/tests-utils';
import { getMockedProjectIdentifier } from '../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { ProjectProvider } from '../../providers/project-provider/project-provider.component';
import { MediaItemsBucketTitle } from './media-items-bucket.interface';
import { TestMediaContainer } from './test-media-container.component';

const inMemoryProjectService = createInMemoryProjectService();

const getScoreThresholdSlider = () => screen.queryByRole('group', { name: 'Model score threshold' });

const renderTestMediaContainer = async (taskType?: TASK_TYPE, onLabelChange = jest.fn(), selectedLabelId = 'null') => {
    const container = await render(
        <ProjectProvider projectIdentifier={getMockedProjectIdentifier()}>
            <TestMediaContainer
                modelInfo={'some model info'}
                test={getMockedTest()}
                taskType={taskType ?? TASK_TYPE.DETECTION}
                onLabelChange={onLabelChange}
                selectedLabelId={selectedLabelId}
            />
        </ProjectProvider>,
        {
            services: {
                projectService: inMemoryProjectService,
            },
        }
    );

    await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    return container;
};

describe('TestMediaContainer', () => {
    afterEach(() => {
        jest.clearAllMocks();
    });

    it('renders all UIs correctly', async () => {
        await renderTestMediaContainer();

        expect(screen.getByText(/Annotations vs Predictions/)).toBeInTheDocument();
        expect(screen.getByLabelText(/Select label/)).toBeInTheDocument();
        expect(screen.getByText(/Model score threshold/)).toBeInTheDocument();
        expect(screen.getByText(/Below threshold/)).toBeInTheDocument();
        expect(screen.getByText(/Above threshold/)).toBeInTheDocument();
    });

    it('only displays labels from the tested task', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.DETECTION,
                        labels: [
                            getMockedLabel({ id: 'detection-label-1', name: 'detection-label-1' }),
                            getMockedLabel({ id: 'detection-label-2', name: 'detection-label-2' }),
                        ],
                    }),
                    getMockedTask({
                        domain: DOMAIN.SEGMENTATION,
                        labels: [
                            getMockedLabel({ id: 'segmentation-label-1', name: 'segmentation-label-1' }),
                            getMockedLabel({ id: 'segmentation-label-2', name: 'segmentation-label-2' }),
                        ],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer();

        // Click on label picker
        userEvent.click(screen.getByLabelText(/Select label/));

        expect(screen.getByLabelText(/All labels/)).toBeInTheDocument();
        expect(screen.getByText('detection-label-1')).toBeInTheDocument();
        expect(screen.getByText('detection-label-2')).toBeInTheDocument();

        expect(screen.queryByText('segmentation-label-2')).not.toBeInTheDocument();
        expect(screen.queryByText('segmentation-label-2')).not.toBeInTheDocument();
    });

    it('does not display "all labels" if there is only 1 label to be displayed', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.DETECTION,
                        labels: [getMockedLabel({ id: 'detection-label-1', name: 'detection-label-1' })],
                    }),
                    getMockedTask({
                        domain: DOMAIN.SEGMENTATION,
                        labels: [
                            getMockedLabel({ id: 'segmentation-label-1', name: 'segmentation-label-1' }),
                            getMockedLabel({ id: 'segmentation-label-2', name: 'segmentation-label-2' }),
                        ],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer();

        // Click on label picker
        userEvent.click(screen.getByLabelText(/Select label/));

        expect(screen.queryByLabelText(/All labels/)).not.toBeInTheDocument();
        expect(screen.getAllByText('detection-label-1')[0]).toBeInTheDocument();

        expect(screen.queryByText('segmentation-label-2')).not.toBeInTheDocument();
        expect(screen.queryByText('segmentation-label-2')).not.toBeInTheDocument();
    });

    it('calls onLabelChange', async () => {
        const selectedLabel = { id: 'segmentation-label-3', name: 'segmentation-label-3' };
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.SEGMENTATION,
                        labels: [
                            getMockedLabel({ id: 'segmentation-label-1', name: 'segmentation-label-1' }),
                            getMockedLabel({ id: 'segmentation-label-2', name: 'segmentation-label-2' }),
                            getMockedLabel(selectedLabel),
                        ],
                    }),
                ],
            }),
        });

        const mockedOnLabelChange = jest.fn();
        await renderTestMediaContainer(undefined, mockedOnLabelChange);

        fireEvent.click(screen.getByLabelText(/Select label/i));

        await userEvent.selectOptions(
            screen.getByRole('listbox'),
            screen.getByRole('option', { name: selectedLabel.id })
        );

        expect(mockedOnLabelChange).toHaveBeenCalledWith(selectedLabel);
    });

    it('Should display slider score for detection -> classification type, ABOVE and BELOW threshold', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.DETECTION,
                        labels: [getMockedLabel({ id: 'detection-label-1', name: 'detection-label-1' })],
                    }),
                    getMockedTask({
                        domain: DOMAIN.CLASSIFICATION,
                        labels: [
                            getMockedLabel({
                                id: 'classification-label-1',
                                name: 'classification-label-1',
                                group: 'a',
                            }),
                            getMockedLabel({
                                id: 'classification-label-2',
                                name: 'classification-label-2',
                                group: 'a',
                            }),
                        ],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer();

        expect(getScoreThresholdSlider()).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.ABOVE_THRESHOLD)).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.BELOW_THRESHOLD)).toBeInTheDocument();
    });

    it('Should not display slider score for single label classification type, display CORRECT and INCORRECT title', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.CLASSIFICATION,
                        labels: [
                            getMockedLabel({
                                id: 'classification-label-1',
                                name: 'classification-label-1',
                                group: 'a',
                            }),
                            getMockedLabel({
                                id: 'classification-label-2',
                                name: 'classification-label-2',
                                group: 'a',
                            }),
                        ],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer(TASK_TYPE.CLASSIFICATION);

        expect(getScoreThresholdSlider()).not.toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.INCORRECT)).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.CORRECT)).toBeInTheDocument();
    });

    it('Should not display slider score for anomaly classification type, display CORRECT and INCORRECT title', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.ANOMALY_CLASSIFICATION,
                        labels: [getMockedLabel({ id: 'classification-label-1', name: 'classification-label-1' })],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer(TASK_TYPE.ANOMALY_CLASSIFICATION);

        expect(getScoreThresholdSlider()).not.toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.INCORRECT)).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.CORRECT)).toBeInTheDocument();
    });

    it('Display slider score for multi label classification type, display CORRECT and INCORRECT title', async () => {
        inMemoryProjectService.getProject = async () => ({
            ...getMockedProject({
                tasks: [
                    getMockedTask({
                        domain: DOMAIN.CLASSIFICATION,
                        labels: [
                            getMockedLabel({
                                id: 'classification-label-1',
                                name: 'classification-label-1',
                                group: 'a',
                            }),
                            getMockedLabel({
                                id: 'classification-label-2',
                                name: 'classification-label-2',
                                group: 'a',
                            }),
                            getMockedLabel({
                                id: 'classification-label-1',
                                name: 'classification-label-1',
                                group: 'b',
                            }),
                        ],
                    }),
                ],
            }),
        });

        await renderTestMediaContainer(TASK_TYPE.ANOMALY_CLASSIFICATION);

        expect(getScoreThresholdSlider()).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.INCORRECT)).toBeInTheDocument();
        expect(screen.getByText(MediaItemsBucketTitle.CORRECT)).toBeInTheDocument();
    });
});
