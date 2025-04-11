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

import { defaultTheme, Provider } from '@adobe/react-spectrum';
import { fireEvent, render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { KeyMap } from '../../../../shared/keyboard-events/keyboard.interface';
import { getMockedLabel } from '../../../../test-utils/mocked-items-factory/mocked-labels';
import { getMockedProject } from '../../../../test-utils/mocked-items-factory/mocked-project';
import { getMockedTask } from '../../../../test-utils/mocked-items-factory/mocked-tasks';
import { MediaFilterValueLabel } from './media-filter-value-label.component';

const mockLabels = [
    { name: 'test 1', id: '2020' },
    { name: 'test2', id: '2021' },
    { name: 'test3', id: '2022' },
];
const tasks = [getMockedTask({ labels: mockLabels.map(({ id, name }) => getMockedLabel({ name, id })) })];

const mockProject = getMockedProject({
    tasks,
});

jest.mock('../../../project-details/providers/project-provider/project-provider.component', () => ({
    useProject: () => ({ project: mockProject }),
}));

describe('MediaFilterValueLabel', () => {
    const onSelectionChange = jest.fn();
    const getTextArea = () => screen.getByLabelText('media-filter-label');

    beforeEach(() => {
        jest.clearAllMocks();
    });

    afterEach(() => {
        jest.resetModules();
    });

    afterAll(() => {
        jest.clearAllMocks();
    });

    describe('inital value', () => {
        it('empty value is invalid', async () => {
            await render(<MediaFilterValueLabel value={''} onSelectionChange={onSelectionChange} />);

            expect(getTextArea().getAttribute('aria-invalid')).toBe('true');
            expect(onSelectionChange).not.toHaveBeenCalled();
        });

        it('unexisten label ids are invalid', async () => {
            await render(<MediaFilterValueLabel value={['9875', '6545']} onSelectionChange={onSelectionChange} />);

            expect(getTextArea().getAttribute('aria-invalid')).toBe('true');
            expect(onSelectionChange).not.toHaveBeenCalled();
        });

        it('add valid labes', async () => {
            const [testLabel, labelTwo] = mockLabels;

            await render(
                <MediaFilterValueLabel
                    value={[testLabel.id, '123', labelTwo.id]}
                    onSelectionChange={onSelectionChange}
                />
            );

            const textArea = getTextArea();

            expect(textArea.getAttribute('aria-invalid')).toBe(null);
            expect(textArea).toHaveValue(`${testLabel.name}, ${labelTwo.name}, `);
            expect(onSelectionChange).not.toHaveBeenCalled();
        });
    });

    describe('label panel three', () => {
        it('selecting a panel item calls onSelectionChange and adds it as text value', async () => {
            const [testLabel] = mockLabels;
            await render(
                <Provider theme={defaultTheme}>
                    <MediaFilterValueLabel value={''} onSelectionChange={onSelectionChange} />
                </Provider>
            );

            const textArea = getTextArea();

            await userEvent.click(textArea);

            const labelItem = await screen.findByLabelText(`label item ${testLabel.name}`);

            await userEvent.click(labelItem.firstChild as HTMLElement);

            expect(textArea).toHaveValue(`${testLabel.name}, `);
            expect(onSelectionChange).toHaveBeenCalledWith([testLabel.id]);
        });

        it('only add unique labels', async () => {
            const [testLabel, testLabelTwo] = mockLabels;

            await render(
                <Provider theme={defaultTheme}>
                    <MediaFilterValueLabel
                        value={[testLabel.id, testLabelTwo.id]}
                        onSelectionChange={onSelectionChange}
                    />
                </Provider>
            );

            const textArea = getTextArea();

            await userEvent.click(textArea);
            const labelItem = await screen.findByLabelText(`label item ${testLabel.name}`);

            await userEvent.click(labelItem.firstChild as HTMLElement);

            expect(textArea).toHaveValue(`${testLabel.name}, ${testLabelTwo.name}, `);
            expect(onSelectionChange).not.toHaveBeenCalled();
        });
    });

    describe('text typing', () => {
        it('remove invalid label names when the user deleting characters', async () => {
            const [testLabel, testLabelTwo] = mockLabels;
            await render(
                <Provider theme={defaultTheme}>
                    <MediaFilterValueLabel
                        value={[testLabel.id, testLabelTwo.id]}
                        onSelectionChange={onSelectionChange}
                    />
                </Provider>
            );

            const textArea = getTextArea();
            fireEvent.change(textArea, { target: { value: `${testLabel.name}, ${testLabelTwo.name.slice(0, -1)}` } });
            fireEvent.keyUp(textArea, { code: KeyMap.Backspace });
            expect(textArea).toHaveValue(`${testLabel.name}, `);
            expect(onSelectionChange).toHaveBeenLastCalledWith([testLabel.id]);

            fireEvent.change(textArea, { target: { value: `${testLabel.name.slice(0, -1)}` } });
            fireEvent.keyUp(textArea, { code: KeyMap.Delete });
            expect(textArea).toHaveValue('');
            expect(onSelectionChange).toHaveBeenLastCalledWith([]);
        });

        it('moving the caret back and forward do not trigger onSelectionChange', async () => {
            const [testLabel] = mockLabels;

            await render(<MediaFilterValueLabel value={[testLabel.id]} onSelectionChange={onSelectionChange} />);

            const textArea = getTextArea();

            // leftArrow = 37
            fireEvent.keyUp(textArea, { keyCode: 37 });

            // rightArrow = 39
            fireEvent.keyUp(textArea, { keyCode: 39 });

            expect(onSelectionChange).not.toHaveBeenCalled();
        });
    });
});
