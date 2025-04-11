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
