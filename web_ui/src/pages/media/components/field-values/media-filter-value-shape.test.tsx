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

import { SearchRuleShapeType } from '../../../../core/media/media-filter.interface';
import { KeyMap } from '../../../../shared/keyboard-events/keyboard.interface';
import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { SHAPE_OPTIONS } from '../../utils';
import { MediaFilterValueShape } from './media-filter-value-shape.component';

const getInput = (): HTMLTextAreaElement => screen.getByLabelText('media-filter-shape-type') as HTMLTextAreaElement;

const typeValue = (value: string) => {
    const input = getInput();

    fireEvent.input(input, { target: { value } });
    fireEvent.keyUp(input, { keyCode: 90 });
};

describe('MediaFilterValueLabel', () => {
    const onSelectionChange = jest.fn();
    const [shapeOne, shapeTwo] = SHAPE_OPTIONS;

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders empty input value', async () => {
        render(<MediaFilterValueShape value={1} onSelectionChange={onSelectionChange} />);

        expect(getInput()).toHaveAttribute('value', '');
    });

    it('opens dropdown menu', async () => {
        render(<MediaFilterValueShape value={1} onSelectionChange={onSelectionChange} />);

        fireEvent.change(getInput(), { target: { value: 'test' } });

        const menu = screen.getByRole('menu');

        expect(menu).toBeInTheDocument();
        expect(screen.getAllByRole('menuitem')).toHaveLength(SHAPE_OPTIONS.length);
    });

    it('unexistent shape types are invalid', async () => {
        render(<MediaFilterValueShape value={''} onSelectionChange={onSelectionChange} />);

        fireEvent.input(getInput(), { target: { value: 'test' } });

        expect(getInput().getAttribute('aria-invalid')).toBe('true');
        expect(onSelectionChange).not.toHaveBeenCalled();
    });

    describe('single value', () => {
        it('renders shape text', async () => {
            render(<MediaFilterValueShape value={SearchRuleShapeType.POLYGON} onSelectionChange={onSelectionChange} />);

            expect(getInput()).toHaveAttribute('value', 'Polygon');
        });

        it('type a valid shape name and calls onSelectionChange with its key', async () => {
            render(<MediaFilterValueShape value={''} onSelectionChange={onSelectionChange} />);

            typeValue(shapeOne.text.toLocaleLowerCase());
            const input = getInput();

            expect(input.getAttribute('aria-invalid')).toBe(null);
            expect(input.value).toBe(shapeOne.text);
            expect(onSelectionChange).toHaveBeenCalled();
        });

        it('remove invalid shape name when the user deleting characters', async () => {
            render(<MediaFilterValueShape value={shapeOne.key} onSelectionChange={onSelectionChange} />);

            const input = getInput();
            expect(input.getAttribute('aria-invalid')).toBe(null);
            expect(input.value).toBe(shapeOne.text);

            input.value = `${shapeOne.text.slice(0, -1)}`;
            fireEvent.keyUp(input, { code: KeyMap.Backspace });

            expect(input.value).toBe('');
            expect(onSelectionChange).toHaveBeenCalledWith('');
        });

        it('moving the caret back and forward do not trigger onSelectionChange', async () => {
            render(<MediaFilterValueShape value={shapeOne.key} onSelectionChange={onSelectionChange} />);

            const input = getInput();

            // leftArrow = 37
            fireEvent.keyUp(input, { keyCode: 37 });

            // rightArrow = 39
            fireEvent.keyUp(input, { keyCode: 39 });

            expect(onSelectionChange).not.toHaveBeenCalled();
        });

        it('selects an option from options list', async () => {
            render(<MediaFilterValueShape value={''} onSelectionChange={onSelectionChange} />);
            const input = getInput();
            expect(input.value).toBe('');

            fireEvent.keyDown(input, { key: 'ArrowDown' });
            expect(await screen.findByRole('menu')).toBeInTheDocument();

            fireEvent.click(screen.getByRole('menuitem', { name: shapeOne.text }));
            expect(input.value).toBe(shapeOne.text);
            expect(onSelectionChange).toHaveBeenCalledWith(shapeOne.key);
        });

        it('selecting an existing option does not add it twice', async () => {
            render(<MediaFilterValueShape value={shapeOne.key} onSelectionChange={onSelectionChange} />);

            const input = getInput();
            expect(input.value).toBe(shapeOne.text);

            fireEvent.keyDown(input, { key: 'ArrowDown' });

            fireEvent.click(screen.getByRole('menuitem', { name: shapeOne.text }));
            expect(input.value).toBe(shapeOne.text);
            expect(onSelectionChange).not.toHaveBeenCalled();
        });
    });

    describe('multiple values', () => {
        it('renders shapes texts', async () => {
            render(
                <MediaFilterValueShape
                    isMultiselection
                    value={[SearchRuleShapeType.POLYGON, SearchRuleShapeType.RECTANGLE]}
                    onSelectionChange={onSelectionChange}
                />
            );

            expect(getInput()).toHaveAttribute('value', 'Polygon, Rectangle, ');
        });

        it('type a valid shapes names and calls onSelectionChange with its keys', async () => {
            render(<MediaFilterValueShape value={''} onSelectionChange={onSelectionChange} isMultiselection />);

            const input = getInput();
            typeValue(shapeOne.text.toLocaleLowerCase());

            expect(input.getAttribute('aria-invalid')).toBe(null);
            expect(input.value).toBe(`${shapeOne.text}, `);
            expect(onSelectionChange).toHaveBeenCalled();
        });

        it('remove invalid shapes names when the user deleting characters', async () => {
            render(
                <MediaFilterValueShape
                    isMultiselection
                    value={[shapeOne.key, shapeTwo.key]}
                    onSelectionChange={onSelectionChange}
                />
            );

            const input = getInput();
            expect(input.getAttribute('aria-invalid')).toBe(null);
            const validText = `${shapeOne.text}, ${shapeTwo.text}, `;
            expect(input.value).toBe(validText);

            input.value = validText.slice(0, -3);
            fireEvent.keyUp(input, { code: KeyMap.Backspace });

            expect(input.value).toBe(`${shapeOne.text}, `);
        });

        it('moving the caret back and forward do not trigger onSelectionChange', async () => {
            render(
                <MediaFilterValueShape
                    isMultiselection
                    value={[shapeOne.key, shapeTwo.key]}
                    onSelectionChange={onSelectionChange}
                />
            );

            const input = getInput();
            //leftArrow = 37
            fireEvent.keyUp(input, { keyCode: 37 });
            //rightArrow = 39
            fireEvent.keyUp(input, { keyCode: 39 });

            expect(onSelectionChange).not.toHaveBeenCalled();
        });

        it('selects an option from options list', async () => {
            render(<MediaFilterValueShape isMultiselection value={''} onSelectionChange={onSelectionChange} />);

            const input = getInput();
            expect(input.value).toBe('');

            fireEvent.keyDown(input, { key: 'ArrowDown' });
            expect(screen.getByRole('menu')).toBeInTheDocument();

            fireEvent.click(screen.getByLabelText(`option-${shapeOne.key}`));
            expect(input.value).toBe(`${shapeOne.text}, `);

            fireEvent.keyDown(input, { key: 'ArrowDown' });
            fireEvent.click(screen.getByLabelText(`option-${shapeTwo.key}`));
            expect(input.value).toBe(`${shapeOne.text}, ${shapeTwo.text}, `);

            expect(onSelectionChange).toHaveBeenLastCalledWith([shapeOne.key, shapeTwo.key]);
        });
    });
});
