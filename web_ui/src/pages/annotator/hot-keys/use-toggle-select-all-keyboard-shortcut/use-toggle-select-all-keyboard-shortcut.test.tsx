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
