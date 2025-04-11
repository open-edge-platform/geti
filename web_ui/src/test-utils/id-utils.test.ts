// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { idMatchingFormat } from './id-utils';

describe('test function which translates names to proper format', () => {
    it("'Test project id' should be changes to 'test-project-id'", () => {
        expect(idMatchingFormat('Test project id')).toBe('test-project-id');
    });

    it("'TeSt StRange NAME' should be changes to 'test-strange-name'", () => {
        expect(idMatchingFormat('TeSt StRange NAME')).toBe('test-strange-name');
    });

    it("'testId' should be changes to 'testid'", () => {
        expect(idMatchingFormat('testId')).toBe('testid');
    });

    it('empty id should give empty string', () => {
        expect(idMatchingFormat('')).toBe('');
    });
});
