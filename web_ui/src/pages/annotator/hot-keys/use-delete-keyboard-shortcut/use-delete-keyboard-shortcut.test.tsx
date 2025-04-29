// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { fireEvent, screen, waitForElementToBeRemoved } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import { annotatorRender as render } from '../../test-utils/annotator-render';
import { useDeleteKeyboardShortcut } from './use-delete-keyboard-shortcut';

describe('useDeleteKeyboardShortcut', () => {
    const App = ({ removeAnnotations }: { removeAnnotations: AnnotationScene['removeAnnotations'] }) => {
        const hasShapePointSelected = useRef<boolean>(false);
        const annotations = [getMockedAnnotation({})] as ReadonlyArray<Annotation>;
        useDeleteKeyboardShortcut(removeAnnotations, hasShapePointSelected, annotations);
        return <></>;
    };

    const renderApp = async (removeAnnotations: AnnotationScene['removeAnnotations']): Promise<void> => {
        render(<App removeAnnotations={removeAnnotations} />);
        await waitForElementToBeRemoved(screen.getByRole('progressbar'));
    };

    it('RemoveAnnotations callback should be called on delete hotkey', async () => {
        const removeAnnotationsMock = jest.fn();
        await renderApp(removeAnnotationsMock);

        fireEvent.keyDown(document.body, { key: 'Delete', code: 'Delete', keyCode: 46 });
        expect(removeAnnotationsMock).toHaveBeenCalled();
    });

    it('RemoveAnnotations callback should be called on backspace hotkey', async () => {
        const removeAnnotationsMock = jest.fn();
        await renderApp(removeAnnotationsMock);

        fireEvent.keyDown(document.body, { key: 'Backspace', code: 'Backspace', keyCode: 8 });
        expect(removeAnnotationsMock).toHaveBeenCalled();
    });
});
