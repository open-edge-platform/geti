// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { fireEvent, screen } from '@testing-library/react';
import { render } from 'test-utils/render';

import { AnnotatorCanvasSettings } from './annotator-canvas-settings.component';
import { CanvasSettingsProvider } from './canvas-settings-provider.component';
import { CanvasSettings } from './canvas-settings.component';

describe('AnnotatorCanvasSettings', () => {
    it('toggles --annotation-labels-display via CSS instead of mounting/unmounting children', () => {
        render(
            <CanvasSettingsProvider>
                <AnnotatorCanvasSettings>
                    <div data-testid='canvas-content'>content</div>
                </AnnotatorCanvasSettings>
                <CanvasSettings />
            </CanvasSettingsProvider>
        );

        const wrapper = screen.getByTestId('canvas-content').parentElement as HTMLElement;
        const content = screen.getByTestId('canvas-content');

        expect(wrapper.style.getPropertyValue('--annotation-labels-display')).toBe('flex');

        fireEvent.click(screen.getByRole('switch', { name: 'Hide labels' }));

        // Same DOM node (not remounted), only the CSS variable changed.
        expect(screen.getByTestId('canvas-content')).toBe(content);
        expect(screen.getByTestId('canvas-content')).toBeInTheDocument();
        expect(wrapper.style.getPropertyValue('--annotation-labels-display')).toBe('none');
    });
});
