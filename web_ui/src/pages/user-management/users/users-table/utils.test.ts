// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedUser } from '../../../../test-utils/mocked-items-factory/mocked-users';
import { getFullNameFromUser } from './utils';

describe('Users table utils', () => {
    it("Check user's fullname", () => {
        const mockedUser = getMockedUser({ lastName: 'Sparrow', firstName: 'Jack' });
        const fullName = getFullNameFromUser(mockedUser);

        expect(fullName).toBe('Jack Sparrow');
    });
});
