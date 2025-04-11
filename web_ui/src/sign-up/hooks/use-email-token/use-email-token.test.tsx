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

import { ReactNode } from 'react';

import { renderHook } from '@testing-library/react';
import dayjs from 'dayjs';
import { jwtDecode } from 'jwt-decode';
import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';

import { useEmailToken } from './use-email-token.hook';

const token = 'cool-token';

jest.mock('jwt-decode', () => ({
    jwtDecode: jest.fn(),
}));

const wrapper = ({
    children,
    initialEntries,
}: {
    children?: ReactNode;
    initialEntries: MemoryRouterProps['initialEntries'];
}) => {
    return <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>;
};

describe('useEmailToken', () => {
    const today = dayjs();
    const mail = 'test@gmail.com';

    afterEach(() => {
        jest.clearAllMocks();
    });

    it('Should return en email with token', async () => {
        const expiredAt = today.add(1, 'day');
        jest.mocked(jwtDecode).mockReturnValue({ exp: expiredAt.unix(), mail });

        const { result } = renderHook(() => useEmailToken(), {
            wrapper: ({ children }) => wrapper({ children, initialEntries: [`?token=${token}`] }),
        });

        expect(result.current).toEqual({
            email: mail,
            token,
        });
    });

    it('Should return error that token has expired', async () => {
        const expiredAt = today.subtract(1, 'day');

        jest.mocked(jwtDecode).mockReturnValue({ exp: expiredAt.unix(), mail });

        const { result } = renderHook(() => useEmailToken(), {
            wrapper: ({ children }) => wrapper({ children, initialEntries: [`?token=${token}`] }),
        });

        expect(result.current).toEqual({
            token: null,
            error: 'Your invitation link has expired',
        });
    });

    it('Should return an error when token is no present in the url', () => {
        const { result } = renderHook(() => useEmailToken(), {
            wrapper: ({ children }) => wrapper({ children, initialEntries: [`/`] }),
        });

        expect(result.current).toEqual({
            token: null,
            error: 'Invitation token is required for further actions',
        });
    });
});
