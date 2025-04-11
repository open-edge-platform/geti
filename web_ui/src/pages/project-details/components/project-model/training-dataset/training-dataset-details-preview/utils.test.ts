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

import { checkIfCanSelectNext, checkIfCanSelectPrevious, goNext, goPrevious } from './utils';

describe('training-dataset-details-preview utils', () => {
    it('checkIfCanSelectPrevious', () => {
        expect(checkIfCanSelectPrevious(1, [1, 2])).toBe(false);
        expect(checkIfCanSelectPrevious(2, [1, 2])).toBe(true);
    });

    it('checkIfCanSelectNext', () => {
        expect(checkIfCanSelectNext(1, [1, 2])).toBe(true);
        expect(checkIfCanSelectNext(2, [1, 2])).toBe(false);
    });

    describe('goPrevious', () => {
        it('can go to previous', () => {
            const mockedGoto = jest.fn();
            goPrevious(2, [1, 2], mockedGoto);
            expect(mockedGoto).toHaveBeenCalledWith(1);
        });

        it('can not go to previous', () => {
            const mockedGoto = jest.fn();
            goPrevious(1, [1, 2], mockedGoto);
            expect(mockedGoto).not.toHaveBeenCalled();
        });
    });

    describe('goNext', () => {
        it('can go to next', () => {
            const mockedGoto = jest.fn();
            goNext(1, [1, 2], mockedGoto);
            expect(mockedGoto).toHaveBeenCalledWith(2);
        });

        it('can not go to next', () => {
            const mockedGoto = jest.fn();
            goNext(2, [1, 2], mockedGoto);
            expect(mockedGoto).not.toHaveBeenCalled();
        });
    });
});
