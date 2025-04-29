// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import '@wessberg/pointer-events';

import { fireEvent, screen } from '@testing-library/react';

import { annotatorRender as render } from '../test-utils/annotator-render';
import { TransformZoomAnnotation } from './transform-zoom-annotation.component';
import { useZoom, ZoomProvider } from './zoom-provider.component';

describe('TransformZoomAnnotation', () => {
    const App = () => {
        const { setIsPanningDisabled } = useZoom();

        return (
            <TransformZoomAnnotation>
                <svg data-testid='fake-canvas'>Fake canvas</svg>
                <button onClick={() => setIsPanningDisabled(false)}>Enable panning</button>
            </TransformZoomAnnotation>
        );
    };

    it('sets the cursor to "grab" if the user is pressing the "ctrl" key', async () => {
        await render(
            <ZoomProvider>
                <App />
            </ZoomProvider>
        );

        const canvas = screen.getByTestId('transform-zoom-canvas');
        const editor = screen.getByTestId('fake-canvas');

        expect(canvas).not.toHaveClass('isPanning');

        // Press CTRL key
        fireEvent.mouseDown(editor, { button: 0, buttons: 1 });

        /* Enable panning
            This "hack" to update the `isPanningDisabled` was needed because:
        
            (1) `mouseDown` or `drag` or `dragStart` do not propagate the option `ctrlKey`,
            which is needed to set `isPanningDisabled` to false

            (2)`pointerDown` does propagate the option `ctrlKey` but does not trigger the 
            "panning" event on "react-zoom-pan-pinch" which means we will never reach the 
            expected tautology, where `isPanning` && `!isPanningDisabled` === true

            Therefore, I triggered the `isPanning` with the mouseDown event, and 
            updated the `isPanningDisabled` value by mocking a "hacky" button (line 25)
        */
        fireEvent.click(screen.getByText('Enable panning'));

        expect(canvas).toHaveClass('isPanning');
    });

    it('sets the cursor to "grab" if the user is pressing the mousewheel', async () => {
        await render(
            <ZoomProvider>
                <App />
            </ZoomProvider>
        );

        const editor = screen.getByTestId('fake-canvas');
        const canvas = screen.getByTestId('transform-zoom-canvas');

        expect(canvas).not.toHaveClass('isPanning');

        fireEvent.mouseDown(editor, { button: 1, buttons: 4 });

        expect(canvas).toHaveClass('isPanning');
    });
});
