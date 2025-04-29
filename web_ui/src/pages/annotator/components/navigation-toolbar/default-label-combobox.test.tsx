// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { Label, LABEL_BEHAVIOUR } from '../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { getMockedLabel, labels } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedTask, mockedTaskContextProps } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { getById } from '../../../../test-utils/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { DefaultLabelCombobox } from './default-label-combobox.component';

jest.mock('../../providers/task-provider/task-provider.component', () => ({
    ...jest.requireActual('../../providers/task-provider/task-provider.component'),
    useTask: jest.fn(),
}));

const noObjectLabel = getMockedLabel({
    id: 'No object',
    name: 'No object',
    group: 'no Object',
    behaviour: LABEL_BEHAVIOUR.GLOBAL,
    isEmpty: true,
});

const getMockedLabels = (length: number, label?: Partial<Label>) =>
    Array.from({ length }, (_, index) =>
        getMockedLabel({ ...label, name: `${label?.name}-${index}`, id: `${label?.name}-${index}` })
    );

describe('Default label combobox', () => {
    const mockedLabels = getMockedLabels(4, { name: 'label', group: 'default', isEmpty: false });
    const classificationTask = getMockedTask({
        id: 'classification-id',
        title: 'Classification',
        domain: DOMAIN.CLASSIFICATION,
        labels: [...mockedLabels, noObjectLabel],
    });

    const detectionTask = {
        domain: DOMAIN.DETECTION,
        id: 'detection-id',
        labels,
        title: 'Detection',
        isEmpty: false,
    };

    beforeEach(() => {
        jest.resetAllMocks();
    });

    it('renders <TaskLabelTreeContainer /> if the selectedTask doesnt contain a default label', async () => {
        const mockSetDefaultLabel = jest.fn();

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [classificationTask], selectedTask: classificationTask })
        );

        render(<DefaultLabelCombobox defaultLabel={null} setDefaultLabel={mockSetDefaultLabel} />);

        const input = screen.getByRole('textbox', { name: 'Select default label' });
        await userEvent.click(input);

        mockedLabels.forEach((label) => {
            expect(screen.queryByText(label.name)).toBeInTheDocument();
        });

        expect(screen.queryByText(noObjectLabel.name)).not.toBeInTheDocument();

        const label = classificationTask.labels[0];
        fireEvent.input(input, { target: { value: label.name } });

        await userEvent.click(screen.getByText(label.name));
        expect(mockSetDefaultLabel).toHaveBeenCalled();
    });

    it('renders <HierarchicalLabelView /> if the selectedTask contains a default label', () => {
        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [detectionTask], selectedTask: detectionTask })
        );

        render(<DefaultLabelCombobox setDefaultLabel={jest.fn()} defaultLabel={detectionTask.labels[0]} />);

        expect(screen.getByLabelText('Close hierarchical label view')).toBeInTheDocument();
    });

    it('can remove the default label', () => {
        const mockSetDefaultLabel = jest.fn();

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [detectionTask], selectedTask: detectionTask })
        );

        render(<DefaultLabelCombobox setDefaultLabel={mockSetDefaultLabel} defaultLabel={detectionTask.labels[0]} />);

        expect(screen.queryByText(detectionTask.labels[0].name)).toBeInTheDocument();

        fireEvent.click(screen.getByLabelText('Close hierarchical label view'));

        expect(mockSetDefaultLabel).toHaveBeenCalledWith(null);
    });

    it('renders <TaskLabelTreeContainer /> and keeps the default value', async () => {
        const mockSetDefaultLabel = jest.fn();

        jest.mocked(useTask).mockReturnValue(
            mockedTaskContextProps({ tasks: [classificationTask], selectedTask: classificationTask })
        );

        const [firstLabel] = classificationTask.labels;
        const { container } = render(
            <DefaultLabelCombobox defaultLabel={firstLabel} setDefaultLabel={mockSetDefaultLabel} />
        );

        const span = getById(container, `label-default-${firstLabel.name}-${firstLabel.name}`) as HTMLElement;
        await userEvent.click(span);
        const input = screen.getByRole('textbox', { name: 'Select default label' }) as HTMLInputElement;

        expect(input.value).toBe(firstLabel.name);
        //one Label + labels group
        expect(screen.getAllByRole('listitem')).toHaveLength(2);

        fireEvent.input(input, { target: { value: '' } });
        //Labels + labels group
        expect(screen.getAllByRole('listitem')).toHaveLength(classificationTask.labels.length);
    });
});
