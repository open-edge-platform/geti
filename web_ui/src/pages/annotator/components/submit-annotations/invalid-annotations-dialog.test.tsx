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

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';
import { InvalidAnnotationsDialog } from './invalid-annotations-dialog.component';

describe('Invalid annotations dialog', () => {
    const mutation = {
        status: 'idle',
    } as UseSubmitAnnotationsMutationResult;

    it('Shows the user has one or more invalid annotations', () => {
        const cancel = jest.fn();
        const saveOnlyValidAnnotations = jest.fn();

        render(
            <InvalidAnnotationsDialog
                cancel={cancel}
                saveOnlyValidAnnotations={saveOnlyValidAnnotations}
                submitAnnotationsMutation={mutation}
            />
        );
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /continue/i }));
        expect(saveOnlyValidAnnotations).toHaveBeenCalled();
    });

    it('Dismisses the alertdialog', () => {
        const cancel = jest.fn();
        const saveOnlyValidAnnotations = jest.fn();

        render(
            <InvalidAnnotationsDialog
                cancel={cancel}
                saveOnlyValidAnnotations={saveOnlyValidAnnotations}
                submitAnnotationsMutation={mutation}
            />
        );

        fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
        expect(cancel).toHaveBeenCalled();
    });

    it('Shows a saving message', () => {
        const cancel = jest.fn();
        const saveOnlyValidAnnotations = jest.fn();

        render(
            <InvalidAnnotationsDialog
                cancel={cancel}
                saveOnlyValidAnnotations={saveOnlyValidAnnotations}
                submitAnnotationsMutation={
                    {
                        ...mutation,
                        status: 'pending',
                        isPending: true,
                    } as UseSubmitAnnotationsMutationResult
                }
            />
        );

        expect(screen.getByRole('button', { name: /saving annotations/i })).toBeDisabled();
    });
});
