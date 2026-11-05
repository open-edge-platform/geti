// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { getDuplicateKeyIndexes, getWebhookInitialConfig, headersToRows, rowsToHeaders, toWebhookBody } from './utils';

describe('webhook utils', () => {
    describe('headersToRows / rowsToHeaders', () => {
        it('round-trips headers and preserves order', () => {
            const headers = { 'X-Second': '2', 'X-First': '1', Authorization: 'Bearer token' };

            const rows = headersToRows(headers);

            expect(rows).toEqual([
                { key: 'X-Second', value: '2' },
                { key: 'X-First', value: '1' },
                { key: 'Authorization', value: 'Bearer token' },
            ]);
            expect(rowsToHeaders(rows)).toEqual(headers);
            expect(Object.keys(rowsToHeaders(rows))).toEqual(['X-Second', 'X-First', 'Authorization']);
        });

        it.each([undefined, null, {}])('returns no rows for %s headers', (headers) => {
            expect(headersToRows(headers)).toEqual([]);
        });

        it('trims keys and skips rows with an empty key', () => {
            expect(
                rowsToHeaders([
                    { key: '  X-Key ', value: 'v' },
                    { key: '   ', value: 'ignored' },
                ])
            ).toEqual({ 'X-Key': 'v' });
        });
    });

    describe('getDuplicateKeyIndexes', () => {
        it('flags later rows with the same trimmed key', () => {
            const rows = [
                { key: 'X-Key', value: '1' },
                { key: 'Other', value: '2' },
                { key: ' X-Key ', value: '3' },
                { key: 'X-Key', value: '4' },
            ];

            expect([...getDuplicateKeyIndexes(rows)]).toEqual([2, 3]);
        });

        it('ignores empty keys', () => {
            expect(
                getDuplicateKeyIndexes([
                    { key: '', value: '' },
                    { key: ' ', value: '' },
                ]).size
            ).toBe(0);
        });
    });

    describe('toWebhookBody', () => {
        it('drops the id and builds the headers object from rows', () => {
            const body = toWebhookBody({
                ...getWebhookInitialConfig(((key: string) => key) as never),
                id: 'some-id',
                headers: [{ key: 'X-Key', value: 'v' }],
            });

            expect(body).not.toHaveProperty('id');
            expect(body.headers).toEqual({ 'X-Key': 'v' });
        });
    });
});
