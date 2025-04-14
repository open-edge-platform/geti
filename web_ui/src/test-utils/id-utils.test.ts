// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
