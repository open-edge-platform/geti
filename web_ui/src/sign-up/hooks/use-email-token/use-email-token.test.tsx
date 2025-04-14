// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
