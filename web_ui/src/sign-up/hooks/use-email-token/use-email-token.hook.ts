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
