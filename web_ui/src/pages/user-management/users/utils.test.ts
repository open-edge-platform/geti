// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
