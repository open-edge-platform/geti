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
