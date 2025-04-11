// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { LabelItemEditionState, LabelTreeItem } from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { getMockedTreeLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { projectRender as render } from '../../../../../test-utils/project-provider-render';
import { ProjectLabelsManagement } from './project-labels-management.component';

const labels: LabelTreeItem[] = [
    getMockedTreeLabel({ name: 'test1', id: '1', group: 'default group', hotkey: '' }),
    getMockedTreeLabel({ name: 'test2', id: '2', group: 'default group', hotkey: '' }),
    getMockedTreeLabel({ name: 'test3', id: '3', group: 'default group', hotkey: '' }),
];
const setLabels = jest.fn();

const mockMutate = jest.fn((_config, helpers) => {
    const { onSuccess, onSettled } = helpers;
    onSuccess();
    onSettled();
});

jest.mock('../../../../../core/projects/hooks/use-project-actions.hook', () => ({
    useProjectActions: () => ({
        ...jest.requireActual('../../../../../core/projects/hooks/use-project-actions.hook').useProjectActions(),
        editProjectLabelsMutation: {
            mutate: mockMutate,
        },
    }),
}));

describe('project labels management', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    const mockedSetLabelsTree = jest.fn();
    const domains = [DOMAIN.DETECTION];

    it('Check if labels are properly shown', async () => {
        await render(
            <ProjectLabelsManagement
                isInEdition={false}
                setIsDirty={jest.fn()}
                labelsTree={labels}
                setLabelsTree={setLabels}
                relation={LabelsRelationType.SINGLE_SELECTION}
                isTaskChainProject={false}
                domains={domains}
                setLabelsValidity={jest.fn()}
            />
        );

        const allListItems = screen.getAllByRole('listitem');
        expect(allListItems).toHaveLength(3);
    });

    it('Delete buttons are shown', async () => {
        await render(
            <ProjectLabelsManagement
                isInEdition={true}
                setIsDirty={jest.fn()}
                labelsTree={labels}
                setLabelsTree={setLabels}
                relation={LabelsRelationType.SINGLE_SELECTION}
                isTaskChainProject={false}
                domains={domains}
                setLabelsValidity={jest.fn()}
            />
        );

        expect(screen.queryByTestId('test1-label-delete-label-button')).toBeInTheDocument();
        expect(screen.queryByTestId('test2-label-delete-label-button')).toBeInTheDocument();
        expect(screen.queryByTestId('test3-label-delete-label-button')).toBeInTheDocument();
    });

    it('Check if edited value is shown', async () => {
        const setIsDirtyMock = jest.fn();

        await render(
            <ProjectLabelsManagement
                isInEdition={true}
                setIsDirty={setIsDirtyMock}
                labelsTree={labels}
                setLabelsTree={setLabels}
                relation={LabelsRelationType.SINGLE_SELECTION}
                isTaskChainProject={false}
                domains={domains}
                setLabelsValidity={jest.fn()}
            />
        );

        const nameInput = screen.getByTestId('label-tree-test3-name-input');
        expect(nameInput).toBeInTheDocument();

        await userEvent.type(nameInput, '1');

        expect(setIsDirtyMock).toHaveBeenCalledWith(true);
        expect(setLabels).toHaveBeenCalledWith([
            labels[0],
            labels[1],
            { ...labels[2], name: 'test31', state: LabelItemEditionState.CHANGED },
        ]);
    });

    it('Check if added label has state "NEW" and if input is cleared', async () => {
        await render(
            <ProjectLabelsManagement
                isInEdition={true}
                setIsDirty={jest.fn()}
                labelsTree={[]}
                setLabelsTree={mockedSetLabelsTree}
                relation={LabelsRelationType.SINGLE_SELECTION}
                isTaskChainProject={false}
                domains={domains}
                setLabelsValidity={jest.fn()}
            />
        );

        const createLabelButton = screen.getByRole('button', { name: 'Create label' });

        await userEvent.type(screen.getByRole('textbox'), 'new label');

        fireEvent.click(createLabelButton);

        expect(mockedSetLabelsTree).toHaveBeenCalledWith([
            expect.objectContaining({ state: LabelItemEditionState.NEW }),
        ]);

        expect(screen.getByRole('textbox')).toHaveValue('');
        expect(createLabelButton).toBeDisabled();
    });

    it('Check if user in anomaly project is not able to add new labels', async () => {
        await render(
            <ProjectLabelsManagement
                isInEdition={true}
                setIsDirty={jest.fn()}
                labelsTree={[]}
                setLabelsTree={mockedSetLabelsTree}
                relation={LabelsRelationType.SINGLE_SELECTION}
                isTaskChainProject={false}
                domains={domains}
                setLabelsValidity={jest.fn()}
            />
        );

        expect(screen.queryByRole('button', { name: 'Add label' })).not.toBeInTheDocument();
    });

    describe('MixedLabelsManagement', () => {
        it('Check if added group has state "NEW" and input is cleared', async () => {
            await render(
                <ProjectLabelsManagement
                    isInEdition={true}
                    setIsDirty={jest.fn()}
                    labelsTree={[]}
                    setLabelsTree={mockedSetLabelsTree}
                    relation={LabelsRelationType.MIXED}
                    isTaskChainProject={false}
                    domains={domains}
                    setLabelsValidity={jest.fn()}
                />
            );

            const createGroupButton = screen.getByRole('button', { name: 'Create group' });

            await userEvent.type(screen.getByRole('textbox'), 'new group');
            fireEvent.click(createGroupButton);

            expect(mockedSetLabelsTree).toHaveBeenCalledWith([
                expect.objectContaining({ state: LabelItemEditionState.NEW }),
            ]);

            expect(screen.getByRole('textbox')).toHaveValue('');
            expect(createGroupButton).toBeDisabled();
        });

        it('Not chain hierarchical classification project should have possibility to add new root group', async () => {
            await render(
                <ProjectLabelsManagement
                    isInEdition={true}
                    setIsDirty={jest.fn()}
                    labelsTree={[]}
                    setLabelsTree={mockedSetLabelsTree}
                    relation={LabelsRelationType.MIXED}
                    isTaskChainProject={false}
                    domains={domains}
                    setLabelsValidity={jest.fn()}
                />
            );

            expect(screen.getByRole('button', { name: 'Create group' })).toBeInTheDocument();
        });

        it('Task chain project should not have possibility to add new root group', async () => {
            await render(
                <ProjectLabelsManagement
                    isInEdition={true}
                    setIsDirty={jest.fn()}
                    labelsTree={[]}
                    setLabelsTree={mockedSetLabelsTree}
                    relation={LabelsRelationType.MIXED}
                    isTaskChainProject={true}
                    domains={domains}
                    setLabelsValidity={jest.fn()}
                />
            );

            expect(screen.queryByRole('button', { name: 'Add group' })).not.toBeInTheDocument();
        });
    });
});
