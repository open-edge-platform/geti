// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
