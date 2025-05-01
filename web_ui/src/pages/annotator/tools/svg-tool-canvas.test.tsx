// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { getImageData } from '@shared/canvas-utils';
import { fireEvent, render, screen } from '@testing-library/react';

import { SvgToolCanvas } from './svg-tool-canvas.component';

describe('SvgToolCanvas', () => {
    const image = new Image();

    image.width = 100;
    image.height = 200;

    const imageData = getImageData(image);

    it('has the size of the image', () => {
        const { container } = render(<SvgToolCanvas image={imageData} />);

        const rect = container.querySelector('rect');

        expect(rect).toHaveAttribute('width', '100');
        expect(rect).toHaveAttribute('height', '200');
    });

    it('ignores down pointer events if the user ctrl left clicked', () => {
        const onPointerDown = jest.fn();

        render(<SvgToolCanvas image={imageData} onPointerDown={onPointerDown} />);

        const editor = screen.getByRole('editor');

        fireEvent.pointerDown(editor, {
            button: 0,
            buttons: 1,
            ctrlKey: true,
        });
        expect(onPointerDown).not.toHaveBeenCalled();
    });

    it('ignores down pointer events if the user used the middle mouse wheel to click', () => {
        const onPointerDown = jest.fn();

        render(<SvgToolCanvas image={imageData} onPointerDown={onPointerDown} />);

        const editor = screen.getByRole('editor');

        fireEvent.pointerDown(editor, {
            button: 1,
            buttons: 4,
        });
        expect(onPointerDown).not.toHaveBeenCalled();
    });
});
