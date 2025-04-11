// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { JWTPayload, SignJWT } from 'jose';

type TokenPayload =
    | {
          email: string;
      }
    | { mail: string }
    | JWTPayload;

export const generateToken = async (
    expirationTime: number | string | Date = '2h',
    payload: TokenPayload = { email: 'joe@geti.com' }
) => {
    const secret = new TextEncoder().encode('cc7e0d44fd473002f1c42167459001140ec6389b7353f8088f4d9a95f2f596f2');
    const alg = 'HS256';
    const jwt = await new SignJWT(payload)
        .setProtectedHeader({ alg })
        .setIssuedAt()
        .setIssuer('admin@geti.com')
        .setExpirationTime(expirationTime)
        .sign(secret);

    return jwt;
};
