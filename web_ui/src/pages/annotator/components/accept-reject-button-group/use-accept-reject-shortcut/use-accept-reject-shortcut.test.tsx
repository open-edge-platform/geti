// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { getMockedDatasetIdentifier } from '../../../../../test-utils/mocked-items-factory/mocked-identifiers';
import { RequiredProviders } from '../../../../../test-utils/required-providers-render';
import { AnnotatorProviders } from '../../../test-utils/annotator-render';
import { useAcceptRejectShortcut } from './use-accept-reject-shortcut.hook';

const wrapper = ({ children }: { children: ReactNode }) => {
    const datasetIdentifier = getMockedDatasetIdentifier();

    return (
        <RequiredProviders>
            <AnnotatorProviders datasetIdentifier={datasetIdentifier}>{children}</AnnotatorProviders>
        </RequiredProviders>
    );
};

describe('useAcceptRejectShortcut', () => {
    it('Should call both callbacks when hotkeys are enabled', async () => {
        const accept = jest.fn();
        const reject = jest.fn();

        renderHook(
            () => useAcceptRejectShortcut({ callback: accept, isEnabled: true }, { callback: reject, isEnabled: true }),
            {
                wrapper,
            }
        );

        expect(accept).not.toHaveBeenCalled();

        await waitFor(async () => {
            await userEvent.keyboard('{enter}');
            expect(accept).toHaveBeenCalled();
        });

        expect(reject).not.toHaveBeenCalled();
        await userEvent.keyboard('{escape}');
        expect(reject).toHaveBeenCalled();
    });

    it('Should call reject callback when accept is disabled and reject is enabled', async () => {
        const accept = jest.fn();
        const reject = jest.fn();

        renderHook(
            () =>
                useAcceptRejectShortcut({ callback: accept, isEnabled: false }, { callback: reject, isEnabled: true }),
            {
                wrapper,
            }
        );

        expect(reject).not.toHaveBeenCalled();
        await waitFor(async () => {
            await userEvent.keyboard('{escape}');
            expect(reject).toHaveBeenCalled();
        });

        expect(accept).not.toHaveBeenCalled();
        await userEvent.keyboard('{enter}');
        expect(accept).not.toHaveBeenCalled();
    });

    it('Should call accept callback when accept is enabled and reject is disabled', async () => {
        const accept = jest.fn();
        const reject = jest.fn();

        renderHook(
            () =>
                useAcceptRejectShortcut({ callback: accept, isEnabled: true }, { callback: reject, isEnabled: false }),
            {
                wrapper,
            }
        );

        expect(accept).not.toHaveBeenCalled();
        await waitFor(async () => {
            await userEvent.keyboard('{enter}');
            expect(accept).toHaveBeenCalled();
        });

        expect(reject).not.toHaveBeenCalled();
        await userEvent.keyboard('{escape}');
        expect(reject).not.toHaveBeenCalled();
    });

    it('Should NOT call both callbacks when hotkeys are disabled', async () => {
        const accept = jest.fn();
        const reject = jest.fn();

        renderHook(
            () =>
                useAcceptRejectShortcut({ callback: accept, isEnabled: false }, { callback: reject, isEnabled: false }),
            {
                wrapper,
            }
        );

        expect(accept).not.toHaveBeenCalled();
        await waitFor(async () => {
            await userEvent.keyboard('{enter}');
            expect(accept).not.toHaveBeenCalled();
        });

        expect(reject).not.toHaveBeenCalled();
        await userEvent.keyboard('{escape}');
        expect(reject).not.toHaveBeenCalled();
    });
});
