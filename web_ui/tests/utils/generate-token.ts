// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
