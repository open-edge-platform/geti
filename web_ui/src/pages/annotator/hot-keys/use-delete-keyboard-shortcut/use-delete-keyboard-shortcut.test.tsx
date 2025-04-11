// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
