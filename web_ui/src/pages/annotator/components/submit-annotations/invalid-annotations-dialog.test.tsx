// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
