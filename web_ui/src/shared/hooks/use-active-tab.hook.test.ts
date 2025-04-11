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

import { renderHook } from '@testing-library/react';
import { useLocation } from 'react-router-dom';

import { useActiveTab } from './use-active-tab.hook';

jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useLocation: jest.fn(),
}));

describe('useActiveTab', () => {
    it('sets the active tab to defaultKey if the current route is the root', () => {
        // @ts-expect-error We don't care about mocking other values
        jest.mocked(useLocation).mockImplementationOnce(() => ({ pathname: '' }));

        const { result } = renderHook(() => useActiveTab('some-key'));

        expect(result.current).toEqual('some-key');
    });

    it('sets the active tab based on the last parameter of the url', () => {
        // @ts-expect-error We don't care about mocking other values
        jest.mocked(useLocation).mockImplementationOnce(() => ({ pathname: 'new-feature' }));

        const { result } = renderHook(() => useActiveTab('default-key'));

        expect(result.current).toEqual('new-feature');
    });
});
