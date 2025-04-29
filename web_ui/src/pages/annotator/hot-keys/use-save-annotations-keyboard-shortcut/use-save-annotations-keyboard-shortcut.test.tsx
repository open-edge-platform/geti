// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { annotatorRender as render } from '../../test-utils/annotator-render';
import { useSaveAnnotationsKeyboardShortcut } from './use-save-annotations-keyboard-shortcut';

describe('useSaveAnnotationShortcut', () => {
    const App = ({ submitAnnotations, canSave }: { submitAnnotations: () => void; canSave: boolean }) => {
        useSaveAnnotationsKeyboardShortcut(submitAnnotations, canSave);
        return <></>;
    };

    const renderApp = async (submitAnnotations: () => void, canSave: boolean): Promise<void> => {
        render(<App submitAnnotations={submitAnnotations} canSave={canSave} />);
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('submitAnnotations callback should be called on "ctrl+s" shortcut', async () => {
        const saveAnnotationsMock = jest.fn();
        await renderApp(saveAnnotationsMock, true);

        fireEvent.keyDown(document.body, { key: 's', code: 'KeyS', keyCode: 83, ctrlKey: true });
        expect(saveAnnotationsMock).toHaveBeenCalled();
    });

    it('submitAnnotations callback should not be called on "ctrl+s" shortcut if canSave is false', async () => {
        const saveAnnotationsMock = jest.fn();
        await renderApp(saveAnnotationsMock, false);

        fireEvent.keyDown(document.body, { key: 's', code: 'KeyS', keyCode: 83, ctrlKey: true });
        expect(saveAnnotationsMock).not.toHaveBeenCalled();
    });
});
