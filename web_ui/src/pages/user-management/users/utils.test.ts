// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { validateEmail } from './utils';

/*
    Rules based on:
    https://en.wikipedia.org/wiki/Email_address#Reserved_domains:~:text=1234567890123456789012345678901234567890123456789012345678901234%2Bx%40example.com%20(local%2Dpart%20is%20longer%20than%2064%20characters)
*/
describe('User management utils', () => {
    it('validateEmail', async () => {
        expect(await validateEmail.isValid('nolan')).toBeFalsy();
        expect(await validateEmail.isValid('nolan@')).toBeFalsy();
        expect(await validateEmail.isValid('nolan@nolan')).toBeFalsy();
        expect(await validateEmail.isValid('nolan@nolan.')).toBeFalsy();
        expect(await validateEmail.isValid('nolan@nolan@nolan')).toBeFalsy();
        expect(await validateEmail.isValid('nolan@nolan@nolan.com')).toBeFalsy();
        expect(await validateEmail.isValid(`this\ still\"not\\allowed@example.com`)).toBeFalsy();
        expect(
            await validateEmail.isValid('i_like_underscore@but_its_not_allowed_in_this_part.example.com')
        ).toBeFalsy();
        expect(await validateEmail.isValid('"this is"notallowed@example.com"')).toBeFalsy();
        expect(await validateEmail.isValid(`"a"b(c)d,e:f;g<h>i[j\k]l@example.com"`)).toBeFalsy();

        expect(await validateEmail.isValid('nolan@nolan.com')).toBeTruthy();
        expect(await validateEmail.isValid('nolan@inception.pt')).toBeTruthy();
        expect(await validateEmail.isValid('nolan@nolan.intel.com')).toBeTruthy();
        expect(await validateEmail.isValid('nolan_christopher@darkknight.en')).toBeTruthy();
        expect(await validateEmail.isValid('nolaninterstellar_@masterpiece.pt')).toBeTruthy();
    });
});
