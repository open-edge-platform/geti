// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';
import { jwtDecode } from 'jwt-decode';
import { useSearchParams } from 'react-router-dom';

import { isJwtPayloadWithMail } from './utils';

interface InvalidToken {
    token: null;
    error: string;
}

interface UseEmailToken {
    email: string;
    token: string;
}

export const useEmailToken = (): UseEmailToken | InvalidToken => {
    const [searchParams] = useSearchParams();

    const searchParamsToken = searchParams.get('token');

    if (searchParamsToken === null) {
        // Theoretically we should never be here, but just in case

        return {
            token: null,
            error: 'Invitation token is required for further actions',
        };
    }

    try {
        // set email and token that comes from the invitation link
        const decodedToken = jwtDecode(searchParamsToken);
        if (isJwtPayloadWithMail(decodedToken)) {
            const currentTime = dayjs().unix();
            const isTokenExpired = currentTime > decodedToken.exp;

            if (isTokenExpired) {
                return {
                    token: null,
                    error: 'Your invitation link has expired',
                };
            }

            return {
                token: searchParamsToken,
                email: decodedToken.mail,
            };
        }

        return {
            token: null,
            error: 'Invitation token is invalid',
        };
    } catch {
        return {
            token: null,
            error: 'Invitation token is invalid',
        };
    }
};
