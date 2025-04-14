// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
