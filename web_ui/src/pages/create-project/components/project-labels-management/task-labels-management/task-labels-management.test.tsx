// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import {
    LabelTreeItem,
    LabelTreeLabelProps,
    ValidationErrorType,
} from '../../../../../core/labels/label-tree-view.interface';
import { LabelsRelationType } from '../../../../../core/labels/label.interface';
import { GROUP_SEPARATOR } from '../../../../../core/labels/utils';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { getDefaultGroupName } from '../../../../../shared/components/label-tree-view/utils';
import { getMockedTreeGroup, getMockedTreeLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { getById, MORE_THAN_100_CHARS_NAME } from '../../../../../test-utils/utils';
import { DISTINCT_COLORS } from '../../distinct-colors';
import { LABEL_TREE_TYPE } from '../label-tree-type.enum';
import { TaskLabelsManagement } from './task-labels-management.component';

describe('Task label management', () => {
    const setTaskLabelsMock = jest.fn();
    const nextMock = jest.fn();
    const setValidityMock = jest.fn();

    const mockTaskMetadata = {
        labels: [],
        domain: DOMAIN.SEGMENTATION,
        relation: LabelsRelationType.SINGLE_SELECTION,
    };

    const domains = [DOMAIN.SEGMENTATION];

    it("Task of type single label - type name 'single label', it should be visible in textfield", async () => {
        render(
            <TaskLabelsManagement
                taskMetadata={mockTaskMetadata}
                type={LABEL_TREE_TYPE.SINGLE}
                next={jest.fn()}
                setLabels={jest.fn()}
                setValidationError={jest.fn()}
                projectLabels={[]}
                domains={domains}
            />
        );

        const textField = screen.getByLabelText('Label');
        await userEvent.type(textField, 'single label');
        expect(textField).toHaveValue('single label');
    });

    it('should assign a color to the single label', async () => {
        const { container } = render(
            <TaskLabelsManagement
                taskMetadata={mockTaskMetadata}
                type={LABEL_TREE_TYPE.SINGLE}
                setValidationError={jest.fn()}
                next={jest.fn()}
                setLabels={jest.fn()}
                projectLabels={[]}
                domains={domains}
            />
        );

        const colorButton = getById(container, 'change-color-button');
        expect(colorButton?.firstElementChild).not.toHaveStyle('background-color: rgb(255,255,255)');
    });

    it('should invoke "next" callback correctly', async () => {
        render(
            <TaskLabelsManagement
                taskMetadata={mockTaskMetadata}
                type={LABEL_TREE_TYPE.SINGLE}
                setValidationError={jest.fn()}
                next={nextMock}
                setLabels={jest.fn()}
                projectLabels={[]}
                domains={domains}
            />
        );

        const input = screen.getByLabelText('Label');
        await userEvent.type(input, 'Test label');

        await userEvent.keyboard('{Enter}');
        expect(nextMock).toHaveBeenCalled();
    });

    it('should disabled the "add" button after adding a label', async () => {
        render(
            <TaskLabelsManagement
                taskMetadata={mockTaskMetadata}
                type={LABEL_TREE_TYPE.HIERARCHY}
                setValidationError={jest.fn()}
                next={nextMock}
                setLabels={jest.fn()}
                projectLabels={[]}
                domains={domains}
            />
        );
        const addLabel = screen.getByTestId('add-label-button');
        expect(addLabel).toBeDisabled();

        const input = screen.getByLabelText('Label');
        await userEvent.type(input, 'Test label');

        expect(addLabel).toBeEnabled();

        fireEvent.click(addLabel);
        expect(addLabel).toBeDisabled();
    });

    it('should limit the name to 100 characters', async () => {
        render(
            <TaskLabelsManagement
                taskMetadata={mockTaskMetadata}
                type={LABEL_TREE_TYPE.FLAT}
                setValidationError={jest.fn()}
                next={nextMock}
                setLabels={jest.fn()}
                projectLabels={[]}
                domains={domains}
            />
        );

        const input = screen.getByRole('textbox', { name: 'Project label name input' });
        await userEvent.type(input, MORE_THAN_100_CHARS_NAME);

        expect(input.getAttribute('value')).not.toBe(MORE_THAN_100_CHARS_NAME);
        expect(input).toHaveValue(MORE_THAN_100_CHARS_NAME.substring(0, 100));
    });

    it('Allow to create classification project with two root labels in different groups', async () => {
        const mockedMetadata = {
            labels: [
                getMockedTreeGroup({
                    name: 'animal',
                    children: [
                        getMockedTreeLabel({
                            name: 'Cat',
                        }),
                    ],
                }),
                getMockedTreeGroup({
                    name: 'color',
                    children: [
                        getMockedTreeLabel({
                            name: 'pink',
                        }),
                    ],
                }),
            ],
            domain: DOMAIN.CLASSIFICATION,
            relation: LabelsRelationType.MIXED,
        };

        render(
            <TaskLabelsManagement
                taskMetadata={mockedMetadata}
                type={LABEL_TREE_TYPE.HIERARCHY}
                setValidationError={setValidityMock}
                next={nextMock}
                projectLabels={mockedMetadata.labels}
                setLabels={setTaskLabelsMock}
                domains={domains}
            />
        );

        expect(setValidityMock).toHaveBeenLastCalledWith({
            type: ValidationErrorType.TREE,
            validationError: undefined,
        });
    });

    it('Allow to create classification project with two labels in one group', async () => {
        const mockedMetadata = {
            labels: [
                getMockedTreeGroup({
                    name: 'state',
                    children: [getMockedTreeLabel({ name: 'sitting' }), getMockedTreeLabel({ name: 'barking' })],
                }),
            ],
            domain: DOMAIN.CLASSIFICATION,
            relation: LabelsRelationType.MIXED,
        };

        render(
            <TaskLabelsManagement
                taskMetadata={mockedMetadata}
                type={LABEL_TREE_TYPE.HIERARCHY}
                setValidationError={setValidityMock}
                next={nextMock}
                projectLabels={mockedMetadata.labels}
                setLabels={setTaskLabelsMock}
                domains={domains}
            />
        );

        expect(setValidityMock).toHaveBeenLastCalledWith({ type: 'tree', validationError: undefined });
    });

    describe('Check if domain names are proper', () => {
        let allLabels: LabelTreeItem[] = [];
        const setTaskLabelsHandler = (labels: LabelTreeItem[]) => {
            allLabels = labels;
        };

        const addLabel = (name: string) => {
            const addLabelButton = screen.getByTestId('add-label-button');
            const input = screen.getByLabelText('Label');

            fireEvent.change(input, { target: { value: name } });
            fireEvent.click(addLabelButton);
        };

        const labelName = 'test 123';

        beforeEach(() => {
            allLabels = [];
        });

        it('add new label in MULTI LABEL project - group equal to name', async () => {
            const classificationDomain = [DOMAIN.CLASSIFICATION];

            render(
                <TaskLabelsManagement
                    taskMetadata={{
                        ...mockTaskMetadata,
                        domain: DOMAIN.CLASSIFICATION,
                        relation: LabelsRelationType.MULTI_SELECTION,
                    }}
                    type={LABEL_TREE_TYPE.FLAT}
                    next={jest.fn()}
                    projectLabels={allLabels}
                    setValidationError={jest.fn()}
                    setLabels={setTaskLabelsHandler}
                    domains={classificationDomain}
                />
            );

            addLabel(labelName);

            expect(allLabels).toHaveLength(1);
            expect((allLabels[0] as LabelTreeLabelProps).group).toBe(
                `${getDefaultGroupName(classificationDomain[0])}${GROUP_SEPARATOR}${labelName}`
            );
        });

        it('Add two labels to multi selection DETECTION project - check names and groups of the labels', async () => {
            const Labels = () => (
                <TaskLabelsManagement
                    taskMetadata={{
                        domain: DOMAIN.DETECTION,
                        labels: allLabels,
                        relation: LabelsRelationType.MULTI_SELECTION,
                    }}
                    type={LABEL_TREE_TYPE.FLAT}
                    setValidationError={jest.fn()}
                    next={jest.fn()}
                    projectLabels={allLabels}
                    setLabels={setTaskLabelsHandler}
                    domains={domains}
                />
            );

            const { rerender } = render(<Labels />);

            addLabel(labelName);
            rerender(<Labels />);
            addLabel('test 2');

            expect(allLabels[0].name).toBe('test 2');
            expect(allLabels[1].name).toBe(labelName);
            expect((allLabels[0] as LabelTreeLabelProps).group).toBe(
                `${DOMAIN.DETECTION} labels${GROUP_SEPARATOR}${allLabels[0].name}`
            );
            expect((allLabels[1] as LabelTreeLabelProps).group).toBe(
                `${DOMAIN.DETECTION} labels${GROUP_SEPARATOR}${allLabels[1].name}`
            );
        });

        it('If there is already label Detection from task chain, fill the values', async () => {
            const name = 'detection label';
            const labels = [getMockedTreeLabel({ name, color: '#aabb44ff' })];

            const { container } = render(
                <TaskLabelsManagement
                    taskMetadata={{ ...mockTaskMetadata, labels }}
                    type={LABEL_TREE_TYPE.SINGLE}
                    next={jest.fn()}
                    projectLabels={allLabels}
                    setValidationError={jest.fn()}
                    setLabels={setTaskLabelsHandler}
                    domains={domains}
                />
            );

            expect(screen.getByRole('textbox', { name: 'Project label name input' })).toHaveValue(name);

            const selectedColor = getById(container, 'change-color-button-selected-color');
            expect(selectedColor).toHaveStyle('background-color: rgb(170, 187, 68)');
        });

        it('Does not pick colors from previous tasks when getting the next label color', async () => {
            // Create labels such that the next color will be the last from DISTINCT_COLORS
            const labels = DISTINCT_COLORS.slice(0, DISTINCT_COLORS.length - 1).map((color, index) => {
                return getMockedTreeLabel({ name: `detection label ${index}`, color });
            });

            const { container } = render(
                <TaskLabelsManagement
                    taskMetadata={{ ...mockTaskMetadata, labels: [] }}
                    type={LABEL_TREE_TYPE.SINGLE}
                    next={jest.fn()}
                    projectLabels={labels}
                    setValidationError={jest.fn()}
                    setLabels={setTaskLabelsHandler}
                    domains={domains}
                />
            );

            const selectedColor = getById(container, 'change-color-button-selected-color');
            expect(selectedColor).toHaveStyle('background-color: rgb(215, 188, 94)');
        });

        it('Do not crop last letter from first task in chain', async () => {
            render(
                <TaskLabelsManagement
                    taskMetadata={mockTaskMetadata}
                    type={LABEL_TREE_TYPE.SINGLE}
                    next={nextMock}
                    projectLabels={allLabels}
                    setValidationError={jest.fn()}
                    setLabels={setTaskLabelsMock}
                    domains={domains}
                />
            );

            const input = screen.getByRole('textbox', { name: 'Project label name input' });

            await userEvent.type(input, 'abc');
            await userEvent.keyboard('[Enter]');

            expect(setTaskLabelsMock).toHaveBeenLastCalledWith([expect.objectContaining({ name: 'abc' })]);
            expect(nextMock).toHaveBeenCalled();
        });

        it('Allow to create group with the same name as label', async () => {
            const mockClassificationTaskMetadata = {
                labels: [getMockedTreeGroup({ name: 'test', children: [getMockedTreeLabel({ name: 'test1' })] })],
                domain: DOMAIN.CLASSIFICATION,
                relation: LabelsRelationType.MIXED,
            };

            render(
                <TaskLabelsManagement
                    taskMetadata={mockClassificationTaskMetadata}
                    type={LABEL_TREE_TYPE.HIERARCHY}
                    setValidationError={setValidityMock}
                    next={nextMock}
                    projectLabels={mockClassificationTaskMetadata.labels}
                    setLabels={setTaskLabelsMock}
                    domains={domains}
                />
            );

            const input = screen.getAllByRole('textbox', { name: 'Label group name' })[0];

            await userEvent.type(input, 'test1');
            expect(screen.getByRole('button', { name: 'Create group' })).toBeEnabled();

            await userEvent.clear(input);
            await userEvent.type(input, 'test');
            expect(screen.getByRole('button', { name: 'Create group' })).toBeDisabled();
        });

        it('Check group of labels added in multi label classification project', async () => {
            const classificationDomain = [DOMAIN.CLASSIFICATION];

            const mockClassificationTaskMetadata = {
                labels: [],
                domain: DOMAIN.CLASSIFICATION,
                relation: LabelsRelationType.MULTI_SELECTION,
            };

            render(
                <TaskLabelsManagement
                    taskMetadata={mockClassificationTaskMetadata}
                    type={LABEL_TREE_TYPE.FLAT}
                    next={nextMock}
                    projectLabels={allLabels}
                    setValidationError={jest.fn()}
                    setLabels={setTaskLabelsMock}
                    domains={classificationDomain}
                />
            );

            await userEvent.type(screen.getByPlaceholderText('Label name'), 'label 1');
            await userEvent.click(screen.getByRole('button', { name: 'Create label' }));

            expect(setTaskLabelsMock).toHaveBeenCalledWith([
                expect.objectContaining({ group: `Classification labels${GROUP_SEPARATOR}label 1` }),
            ]);
        });
    });
});
