// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { getMockedPolicy, getMockedProduct } from '../../../../test-utils/mocked-items-factory/mocked-product';
import { findPolicy, hasRenewableAmount, hasWelcomingCredits } from './utils';

describe('products hooks utils', () => {
    it('findPolicy', () => {
        const product = getMockedProduct({ name: 'test' });

        expect(findPolicy([product], hasWelcomingCredits)).toEqual(
            expect.objectContaining({ accountName: 'welcoming credits' })
        );
        expect(findPolicy([product], hasRenewableAmount)).toEqual(
            expect.objectContaining({ accountName: 'recurring credits' })
        );
    });

    it('hasWelcomingCredits', () => {
        expect(hasWelcomingCredits(getMockedPolicy({ initAmount: 10 }))).toBe(true);
        expect(hasWelcomingCredits(getMockedPolicy({ initAmount: undefined }))).toBe(false);
    });

    it('hasRenewableAmount', () => {
        expect(hasRenewableAmount(getMockedPolicy({ renewableAmount: 100 }))).toBe(true);
        expect(hasRenewableAmount(getMockedPolicy({ renewableAmount: null }))).toBe(false);
    });
});
