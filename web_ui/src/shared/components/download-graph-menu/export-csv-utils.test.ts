// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { downloadFile } from '../../utils';
import {
    DownloadableArray,
    downloadCSV,
    getFormattedArray,
    getFormattedBarChart,
    getFormattedCvsToString,
    getFormattedLineChart,
    getFormattedMatrix,
    getFormattedText,
    normalizeFilenameForDownload,
    sanitiseDoublequotes,
    sanitiseSpecialCharacters,
} from './export-csv-utils';

jest.mock('../../utils', () => ({
    ...jest.requireActual('../../utils'),
    downloadFile: jest.fn(),
}));

describe('Download svg button utils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('downloadCSV', () => {
        downloadCSV('file-test', []);

        expect(downloadFile).toHaveBeenCalledWith('data:text/csv;charset=utf-8,', 'file-test');
    });

    it('normalizeFilenameForDownload', () => {
        expect(normalizeFilenameForDownload('Some-file=name-with.dots')).toEqual('Some-file=name-with_dots');

        downloadCSV('file-test.with.dots', []);

        expect(downloadFile).toHaveBeenCalledWith('data:text/csv;charset=utf-8,', 'file-test_with_dots');
    });

    it('getFormattedText', () => {
        const data = 'data-test';
        const header = 'header-test';

        expect(getFormattedText({ type: 'text', data, header })).toEqual([[header], [data]]);
    });

    it('getFormattedArray', () => {
        const config: DownloadableArray = { type: 'default', data: [[1, 1]], header: ['header-one', 'header-two'] };

        expect(getFormattedArray(config)).toEqual([config.header, config.data[0]]);
        expect(getFormattedArray({ ...config, data: [] })).toEqual([config.header]);
    });

    it('getFormattedCvsToString', () => {
        expect(getFormattedCvsToString([])).toEqual('');

        expect(
            getFormattedCvsToString([
                ['title', 'title'],
                [1, 1],
                [2, 2],
            ])
        ).toEqual(`"title","title"\n1,1\n2,2\n`);

        expect(
            getFormattedCvsToString([
                ['@title', '=title'],
                [1, 1],
                [2, 2],
            ])
        ).toEqual(`"'@title","'=title"\n1,1\n2,2\n`);

        expect(
            getFormattedCvsToString([
                ['this"is a test"', 'title,test'],
                [1, 1],
                [2, 2],
            ])
        ).toEqual(`"this""is a test""","title,test"\n1,1\n2,2\n`);

        expect(
            getFormattedCvsToString([
                ['', 'title', 'title2'],
                ['row', 1, 2],
                ['row', 3, 4],
            ])
        ).toEqual(`"","title","title2"\n"row",1,2\n"row",3,4\n`);
    });

    it('getFormattedMatrix', () => {
        expect(
            getFormattedMatrix({
                type: 'matrix',
                data: {
                    key: 'key',
                    rowHeader: 'rowHeader',
                    header: 'matrix header',
                    columnHeader: 'columnHeader',
                    columnNames: ['title', 'title2'],
                    rowNames: ['row', 'row2'],
                    matrixValues: [],
                },
            })
        ).toEqual([]);

        expect(
            getFormattedMatrix({
                type: 'matrix',
                data: {
                    key: 'key',
                    rowHeader: 'rowHeader',
                    header: 'matrix header',
                    columnHeader: 'columnHeader',
                    columnNames: ['title', 'title2'],
                    rowNames: ['row', 'row2'],
                    matrixValues: [
                        [1, 2],
                        [3, 4],
                    ],
                },
            })
        ).toEqual([
            ['', 'title', 'title2'],
            ['row', 1, 2],
            ['row2', 3, 4],
        ]);
    });

    it('getFormattedLineChart', () => {
        expect(
            getFormattedLineChart({
                type: 'lineChart',
                xLabel: 'xLabel',
                yLabel: 'yLabel',
                data: [],
            })
        ).toEqual([]);

        expect(
            getFormattedLineChart({
                type: 'lineChart',
                xLabel: 'xLabel',
                yLabel: 'yLabel',
                data: [
                    {
                        name: 'test',
                        color: '#0000',
                        points: [],
                    },
                ],
            })
        ).toEqual([]);

        expect(
            getFormattedLineChart({
                type: 'lineChart',
                xLabel: 'xLabel',
                yLabel: 'yLabel',
                data: [
                    {
                        name: 'test',
                        color: '#0000',
                        points: [
                            { x: 1, y: 1 },
                            { x: 2, y: 2 },
                            { x: 3, y: 3 },
                        ],
                    },
                    {
                        name: 'test2',
                        color: '#0000',
                        points: [
                            { x: 11, y: 11 },
                            { x: 22, y: 22 },
                            { x: 33, y: 33 },
                        ],
                    },
                ],
            })
        ).toEqual([
            ['xLabel', 'yLabel'],
            [1, 1],
            [2, 2],
            [3, 3],
        ]);
    });

    it('getFormattedBarChart', () => {
        expect(
            getFormattedBarChart({
                type: 'barChart',
                data: [],
            })
        ).toEqual([]);

        expect(
            getFormattedBarChart({
                type: 'barChart',
                data: [
                    { name: 'test', value: 1 },
                    { name: 'test2', value: 2 },
                    { name: 'test3', value: 3 },
                ],
            })
        ).toEqual([
            ['test', 'test2', 'test3'],
            [1, 2, 3],
        ]);
    });

    it('sanitiseSpecialCharacters', () => {
        const stringWithoutSpecialCharacters = 'Frodo';

        expect(sanitiseSpecialCharacters(stringWithoutSpecialCharacters)).toEqual(stringWithoutSpecialCharacters);

        const someString1 = '@someString';
        const someString2 = '-someString';
        const someString3 = '+someString';
        const someString4 = '|someString';
        const someString5 = '=label';

        const invalidStrings = [someString1, someString2, someString3, someString4, someString5];

        invalidStrings.forEach((str) => {
            expect(sanitiseSpecialCharacters(str)).toEqual(`'${str}`);
        });
    });

    it('sanitiseDoublequotes', () => {
        expect(sanitiseDoublequotes('some"str')).toEqual('some""str');
    });
});
