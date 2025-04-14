// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, screen } from '@testing-library/react';

import { providersRender as render } from '../../../../test-utils/required-providers-render';
import { UseSubmitAnnotationsMutationResult } from '../../providers/submit-annotations-provider/submit-annotations.interface';
import { SavingFailedDialog } from './saving-failed-dialog.component';

describe('Saving annotations failed dialog', () => {
    const mutation = {
        status: 'error',
        error: {
            message: 'error message',
        },
    } as UseSubmitAnnotationsMutationResult;

    it('Allows the user to retry', () => {
        const cancel = jest.fn();
        const retry = jest.fn();

        render(<SavingFailedDialog cancel={cancel} retry={retry} submitAnnotationsMutation={mutation} />);
        expect(screen.getByRole('alertdialog')).toBeInTheDocument();

        fireEvent.click(screen.getByRole('button', { name: /try again/i }));
        expect(retry).toHaveBeenCalled();
    });

    it('Dismisses the alertdialog', () => {
        const cancel = jest.fn();
        const retry = jest.fn();

        render(<SavingFailedDialog cancel={cancel} retry={retry} submitAnnotationsMutation={mutation} />);

        fireEvent.click(screen.getByRole('button', { name: /cancel/i }));
        expect(cancel).toHaveBeenCalled();
    });

    it('Shows a saving message', () => {
        const cancel = jest.fn();
        const retry = jest.fn();

        render(
            <SavingFailedDialog
                cancel={cancel}
                retry={retry}
                submitAnnotationsMutation={{ ...mutation, isPending: true } as UseSubmitAnnotationsMutationResult}
            />
        );

        expect(screen.getByRole('button', { name: /saving annotations/i })).toBeDisabled();
    });
});
