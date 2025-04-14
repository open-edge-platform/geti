// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { renderHook, waitFor } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

import { RequiredProviders } from '../../../../test-utils/required-providers-render';
import { AnnotatorProviders } from '../../test-utils/annotator-render';
import { useToggleSelectAllKeyboardShortcut } from './use-toggle-select-all-keyboard-shortcut';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useLocation: () => jest.fn(),
}));

const wrapper = ({ children }: { children: ReactNode }): JSX.Element => {
    const datasetIdentifier = {
        workspaceId: 'workspace-id',
        projectId: 'project-id',
        datasetId: 'dataset-id',
        organizationId: 'organization-id',
    };

    return (
        <RequiredProviders>
            <AnnotatorProviders datasetIdentifier={datasetIdentifier}>{children}</AnnotatorProviders>
        </RequiredProviders>
    );
};

describe('useToggleSelectAllKeyboardShortcut', () => {
    it('should toggleSelectAll with "true" after "selectAll" hotkey is pressed', async () => {
        const toggleSelectAll = jest.fn();

        renderHook(() => useToggleSelectAllKeyboardShortcut(toggleSelectAll), {
            wrapper,
        });

        await userEvent.keyboard('{Control>}A');

        await waitFor(() => {
            expect(toggleSelectAll).toHaveBeenNthCalledWith(1, true);
        });
    });

    it('should toggleSelectAll with "false" after "deselectAll" hotkey is pressed', async () => {
        const toggleSelectAll = jest.fn();

        renderHook(() => useToggleSelectAllKeyboardShortcut(toggleSelectAll), {
            wrapper,
        });

        await userEvent.keyboard('{Control>}D');

        await waitFor(() => {
            expect(toggleSelectAll).toHaveBeenNthCalledWith(1, false);
        });
    });
});
