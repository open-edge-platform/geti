// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen, waitForElementToBeRemoved, within } from '@testing-library/react';
import { act } from 'react-dom/test-utils';

import { DOMAIN } from '../../../../core/projects/core.interface';
import { ProjectProps } from '../../../../core/projects/project.interface';
import { createInMemoryProjectService } from '../../../../core/projects/services/in-memory-project-service';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { mockFile } from '../../../../test-utils/mockFile';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { TaskProvider } from '../../../annotator/providers/task-provider/task-provider.component';
import { ProjectProvider } from '../../../project-details/providers/project-provider/project-provider.component';
import { MediaItem } from './media-item.component';

const mockedClassificationLabels = [
    getMockedLabel({ id: 'dog', name: 'dog' }),
    getMockedLabel({ id: 'cat', name: 'cat' }),
];

const classificationProject = getMockedProject({
    id: 'animal-project',
    domains: [DOMAIN.CLASSIFICATION],
    tasks: [getMockedTask({ id: 'classification', domain: DOMAIN.CLASSIFICATION, labels: mockedClassificationLabels })],
});

describe('MediaItem', () => {
    const renderApp = async ({
        id = 'test-id',
        labelIds = [],
        fileName = 'video.mp4',
        project = getMockedProject({ id: '1' }),
        onDeleteItem = jest.fn(),
        onSelectLabel = jest.fn(),
    }: {
        id?: string;
        fileName?: string;
        labelIds?: string[];
        onDeleteItem?: () => void;
        onSelectLabel?: () => void;
        project?: ProjectProps;
    }) => {
        const projectService = createInMemoryProjectService();
        projectService.getProject = async () => Promise.resolve(project);

        render(
            <ProjectProvider
                projectIdentifier={{
                    workspaceId: 'workspace-id',
                    projectId: 'project-id',
                    organizationId: 'organization-id',
                }}
            >
                <TaskProvider>
                    <MediaItem
                        id={id}
                        url=''
                        onPress={jest.fn()}
                        labelIds={labelIds}
                        mediaFile={mockFile({ name: fileName })}
                        onDeleteItem={onDeleteItem}
                        onSelectLabel={onSelectLabel}
                    />
                </TaskProvider>
            </ProjectProvider>,
            { services: { projectService } }
        );
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    describe('label selection is disabled with task-chain projects', () => {
        it.each([DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.CLASSIFICATION])(
            'task-chain detection-%o',
            async (domain) => {
                const mockedLabel = getMockedLabel({ name: 'camera-label-2' });
                await renderApp({
                    project: getMockedProject({
                        id: 'animal-project',
                        domains: [domain],
                        tasks: [
                            getMockedTask({ domain: DOMAIN.DETECTION, labels: [mockedLabel] }),
                            getMockedTask({ domain, labels: [mockedLabel] }),
                        ],
                    }),
                });

                expect(screen.getByRole('button', { name: 'Unlabeled' })).toBeDisabled();
            }
        );
    });

    it('labeled item show label name', async () => {
        const [, secondLabel] = mockedClassificationLabels;
        await renderApp({ project: classificationProject, labelIds: [secondLabel.id], fileName: 'test.png' });

        const labelButton = screen.getByRole('button', { name: secondLabel.name });
        expect(labelButton).toBeVisible();
        expect(labelButton).toBeEnabled();
    });

    it('open and select classification labels', async () => {
        const [firstLabel] = mockedClassificationLabels;
        const onSelectLabel = jest.fn();

        await renderApp({ project: classificationProject, onSelectLabel });

        act(() => {
            fireEvent.click(screen.getByRole('button', { name: 'Unlabeled' }));
        });
        const selectedLabelsContainer = screen.getByLabelText('label search results');
        expect(selectedLabelsContainer).toBeVisible();

        act(() => {
            fireEvent.click(within(selectedLabelsContainer).getByText(firstLabel.name));
        });

        expect(selectedLabelsContainer).not.toBeVisible();
        expect(onSelectLabel).toHaveBeenCalledWith([expect.objectContaining(firstLabel)]);
    });

    describe('delete confirmation dialog', () => {
        it('context menu calls onDeleteItem', async () => {
            const mockedDelete = jest.fn();
            const mockedId = 'item-id';

            await renderApp({ id: mockedId, onDeleteItem: mockedDelete });

            const deleteButton = screen.getByRole('button', { name: /delete/i });
            const container = deleteButton.parentElement as HTMLElement;

            fireEvent.contextMenu(container);
            fireEvent.click(screen.getByRole('menuitem', { name: /delete/i }));

            fireEvent.click(screen.getByRole('button', { name: /delete/i }));

            expect(mockedDelete).toHaveBeenCalledTimes(1);
        });
    });
});
