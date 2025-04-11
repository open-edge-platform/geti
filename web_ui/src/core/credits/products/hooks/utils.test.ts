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
