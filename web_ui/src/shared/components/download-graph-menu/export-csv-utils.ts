// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import isString from 'lodash/isString';

import { downloadFile } from '../../utils';
import { LineChartData } from '../charts/line-chart/line-chart.interface';

interface DownloadableTextChart {
    type: 'text';
    data: number | string;
    header: string;
}

interface DownloadableLineChart {
    type: 'lineChart';
    yLabel: string;
    xLabel: string;
    data: LineChartData[];
}

interface DownloadableMatrix {
    type: 'matrix';
    data: {
        rowHeader: string;
        columnHeader: string;
        columnNames: string[];
        rowNames: string[];
        matrixValues: number[][];
        header: string;
        key: string;
    };
}

interface DownloadableBarChart {
    type: 'barChart';
    data: {
        name: string;
        value: number;
    }[];
}

export interface DownloadableArray {
    type: 'default';
    header: [string, string];
    data: [number, number][];
}

export type DownloadableData =
    | DownloadableLineChart
    | DownloadableMatrix
    | DownloadableBarChart
    | DownloadableArray
    | DownloadableTextChart;

const CSV_DELIMITER = ',';

export const sanitiseSpecialCharacters = (str: string) => {
    const startsWithSpecialCharactersRegex = new RegExp(/^[=+\-@|].*/);

    if (startsWithSpecialCharactersRegex.test(str)) {
        return `'${str}`;
    }

    return str;
};

export const sanitiseDoublequotes = (str: string) => str.replace(/"/g, '""');

export const sanitiseString = (str: string) => {
    // Rules taken from issue with CSV injection:
    // - Wrap all strings in double quotes
    // - Prepend with single-quote if needed
    // - Escape every double quote with another double quote (aside from the doublequotes from the first rule)

    return `"${sanitiseDoublequotes(sanitiseSpecialCharacters(str))}"`;
};

export const downloadCSV = (fileName: string, csvData: (string | number)[][]) => {
    downloadFile(
        `data:text/csv;charset=utf-8,${encodeURI(getFormattedCvsToString(csvData))}`,
        normalizeFilenameForDownload(fileName)
    );
};

export const getFormattedCvsToString = (csvData: (string | number)[][]) => {
    return csvData
        .map((row) => {
            return row.map((value) => (isString(value) ? sanitiseString(value) : value));
        })
        .reduce((accum, row) => {
            return `${accum}${row.join(CSV_DELIMITER)}\n`;
        }, '');
};

export const getFormattedText = (textChartData: DownloadableTextChart): (string | number)[][] => {
    const { header, data } = textChartData;

    return [[header], [data]];
};

export const getFormattedMatrix = ({ data }: DownloadableMatrix): (string | number)[][] => {
    if (isEmpty(data.matrixValues)) {
        return [];
    }

    const formattedRows = data.matrixValues.map((row, index) => [data.rowNames[index], ...row]);

    return [['', ...data.columnNames], ...formattedRows];
};

export const getFormattedLineChart = ({
    data: lineChartsData,
    xLabel,
    yLabel,
}: DownloadableLineChart): (string | number)[][] => {
    const [data] = lineChartsData;

    if (isEmpty(lineChartsData) || isEmpty(data.points)) {
        return [];
    }

    const initVal: (string | number)[][] = [[xLabel, yLabel]];

    return data.points.reduce((accum, { x, y }) => {
        return [...accum, [x, y]];
    }, initVal);
};

export const getFormattedBarChart = ({ data }: DownloadableBarChart): (string | number)[][] => {
    if (isEmpty(data)) {
        return [];
    }

    const initVal: [string[], number[]] = [[], []];

    return data.reduce((accum, { name, value }) => {
        accum[0] = [...accum[0], name];
        accum[1] = [...accum[1], value];

        return accum;
    }, initVal);
};

export const getFormattedArray = ({ header, data }: DownloadableArray): (string | number)[][] => {
    if (isEmpty(data)) {
        return [header];
    }

    return [header, ...data];
};

// If the graph title has any '.' in the string, then the browser will assume the string
// that comes after the dot will be the extension. So we shouldnt allow that
export const normalizeFilenameForDownload = (fileName: string) => {
    return fileName.replaceAll('.', '_');
};
