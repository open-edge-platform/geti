// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

/* eslint-disable */

import { act, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import {
    LabelItemEditionState,
    LabelItemType,
    LabelTreeLabelProps,
} from '../../../../../core/labels/label-tree-view.interface';
import { Label, LabelsRelationType } from '../../../../../core/labels/label.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { UNIQUE_LABEL_HOTKEY_VALIDATION_MESSAGE } from '../../../../../pages/create-project/components/utils';
import { getMockedLabel, getMockedTreeLabel } from '../../../../../test-utils/mocked-items-factory/mocked-labels';
import { providersRender as render } from '../../../../../test-utils/required-providers-render';
import { MORE_THAN_100_CHARS_NAME } from '../../../../../test-utils/utils';
import { LabelEditionMode } from './label-edition-mode.component';

describe.skip('label edition', () => {
    it('temporarily disabled tests', () => undefined);

    const domains = [DOMAIN.DETECTION];

    const label: LabelTreeLabelProps = {
        open: false,
        inEditMode: true,
        children: [],
        state: LabelItemEditionState.IDLE,
        relation: LabelsRelationType.MULTI_SELECTION,
        type: LabelItemType.LABEL,
        ...(getMockedLabel({ name: 'apple', group: 'default group', hotkey: 'control+a+f' }) as Label),
    };

    it('check if edited name has visible new value', () => {
        render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        const nameField = screen.getByRole('textbox', { name: 'edited name' });

        userEvent.type(nameField, 'test');

        expect(nameField).toHaveValue('test');
    });

    it('check if name is limited to 100 chars in label edition', () => {
        render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        const nameField = screen.getByRole('textbox', { name: 'edited name' });

        userEvent.clear(nameField);
        userEvent.type(nameField, MORE_THAN_100_CHARS_NAME);
        expect(nameField).toHaveValue(MORE_THAN_100_CHARS_NAME.substring(0, 100));
    });

    it('check if hotkey value stays after gaining and loosing focus without any changes', () => {
        render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        const EXPECTED_HOTKEY = 'e+r'.toUpperCase();
        const hotkeyField = screen.getByRole('textbox', { name: 'edited hotkey' });
        const nameField = screen.getByRole('textbox', { name: 'edited name' });

        userEvent.click(hotkeyField);
        userEvent.keyboard('{w>}{e>}r{/e}{/w}');
        expect(hotkeyField).toHaveValue(EXPECTED_HOTKEY);

        userEvent.click(nameField);
        expect(hotkeyField).toHaveValue(EXPECTED_HOTKEY);

        userEvent.click(hotkeyField);
        expect(hotkeyField).toHaveAttribute('placeholder', 'Press key(s)');

        userEvent.click(nameField);
        expect(hotkeyField).toHaveValue(EXPECTED_HOTKEY);
    });

    it('Check group name of new label from single label project', () => {
        render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        userEvent.type(screen.getByRole('textbox', { name: 'edited name' }), 'Test label');
        userEvent.keyboard('[Enter]');
    });

    it('Check group name of new label from multi label project', () => {
        const name = 'Test label';

        render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        userEvent.type(screen.getByRole('textbox', { name: 'edited name' }), name);
        userEvent.keyboard('[Enter]');
    });

    it('Empty label - cancel deletes it', async () => {
        const cancelMock = jest.fn();
        const saveMock = jest.fn();

        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        userEvent.click(screen.getByRole('button', { name: 'Cancel' }));
        expect(cancelMock).toHaveBeenCalled();
    });

    it('Label edit name to the one already existed - Show proper message', async () => {
        const projectLabels = [getMockedTreeLabel({ name: 'test' }), getMockedTreeLabel({ name: 'test2' })];
        const cancelMock = jest.fn();
        const saveMock = jest.fn();

        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        userEvent.type(screen.getByRole('textbox', { name: 'edited name' }), 'test');
        expect(screen.getByText("Label 'test' already exists")).toBeInTheDocument();
    });

    it('Non unique hotkey - error on the screen', async () => {
        const projectLabels = [getMockedTreeLabel({ name: 'test', hotkey: 'ctrl+1' })];

        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        userEvent.click(screen.getByRole('link', { name: '+ Add hotkey' }));
        act(() => {
            userEvent.keyboard('{CTRL>}1{/CTRL}');
        });
        expect(screen.getByRole('button', { name: 'Submit' })).toBeDisabled();
        expect(screen.getByText(UNIQUE_LABEL_HOTKEY_VALIDATION_MESSAGE)).toBeInTheDocument();
    });

    it("Typing 'A' and then 'CTRL+F'", async () => {
        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        await userEvent.click(screen.getByRole('link', { name: '+ Add hotkey' }));
        await userEvent.keyboard('a');

        expect(screen.getByRole('textbox', { name: 'edited hotkey' })).toHaveValue('A');

        await userEvent.keyboard('{CTRL>}f{/CTRL}');

        expect(screen.getByRole('textbox', { name: 'edited hotkey' })).toHaveValue('CTRL+F');
    });

    it('Label can have a hotkey previously used by a removed label', async () => {
        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        await userEvent.click(screen.getByRole('link', { name: '+ Add hotkey' }));
        await userEvent.keyboard('{CTRL>}1{/CTRL}');
    });

    it('Label cannot have a hotkey used by an action in the annotator (e.g. B - bounding box for detection)', async () => {
        await render(
            <LabelEditionMode
                item={label}
                setValidationError={jest.fn()}
                validationErrors={{}}
                savedItem={label}
                flatListProjectItems={[]}
                save={jest.fn()}
                domains={domains}
                newTree
            />
        );

        await userEvent.click(screen.getByRole('link', { name: '+ Add hotkey' }));

        await userEvent.keyboard('B');
    });
});
