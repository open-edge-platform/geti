// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { JwtPayload } from 'jwt-decode';
import get from 'lodash/get';
import isNumber from 'lodash/isNumber';
import isObject from 'lodash/isObject';
import isString from 'lodash/isString';

interface JwtPayloadWithMail extends Omit<JwtPayload, 'exp'> {
    mail: string;
    exp: number;
}

export const isJwtPayloadWithMail = (decoded: unknown): decoded is JwtPayloadWithMail => {
    return (
        isObject(decoded) &&
        'mail' in decoded &&
        'exp' in decoded &&
        isString(get(decoded, 'mail')) &&
        isNumber(get(decoded, 'exp'))
    );
};
