// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { parseDateTime } from '@internationalized/date';
import dayjs from 'dayjs';

import { JobState, JobStepState } from '../core/jobs/jobs.const';
import { JobDataset } from '../core/jobs/jobs.interface';
import { DOMAIN } from '../core/projects/core.interface';
import { getMockedTest } from '../core/tests/services/tests-utils';
import { Test } from '../core/tests/tests.interface';
import { getMockedJobStep } from '../test-utils/mocked-items-factory/mocked-jobs';
import { getMockedTask } from '../test-utils/mocked-items-factory/mocked-tasks';
import {
    DATE_TIME_IN_ISO_AND_UTC_OFFSETFORMAT,
    formatDownloadUrl,
    getDateTimeInISOAndUTCOffsetFormat,
    getDownloadNotificationMessage,
    getFileSize,
    getId,
    getIds,
    getIntervalJobHandlers,
    getProgressScoreColor,
    getUniqueNameFromArray,
    hasDifferentId,
    hasEqualId,
    hasEqualSize,
    isDateBetween,
    isDifferent,
    isNonEmptyArray,
    isNonEmptyString,
    isNotCropDomain,
    isNotCropTask,
    loadImage,
    onValidFileList,
    pluralize,
    sanitize,
    trimText,
} from './utils';

jest.mock('./utils', () => ({
    ...jest.requireActual('./utils'),
    redirectTo: jest.fn(),
}));

describe('getUniqueNameFromList', () => {
    const getFakeTestsNames = (tests: Test[]) => tests.map((test) => test.testName);

    it('Random scenario: assigns an unique test name', () => {
        const T1 = getMockedTest({ testName: 'T1' });
        const T2 = getMockedTest({ testName: 'T2' });
        const T3 = getMockedTest({ testName: 'T3' });
        const fakeTests = [T1, T2, T3];

        // Remove 1 from the beginning (T1)
        fakeTests.shift();

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T1');

        // Add the first test again (T1)
        fakeTests.unshift(T1);

        // Remove 1 from the end (T3)
        fakeTests.pop();

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T3');

        // Add a new test
        fakeTests.push(getMockedTest({ testName: 'T3' }));

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T4');

        // Add two more tests
        fakeTests.push(getMockedTest({ testName: 'T4' }));
        fakeTests.push(getMockedTest({ testName: 'T5' }));

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T6');
    });

    it('index increments correctly on the best case scenario', () => {
        const fakeTests: Test[] = [];

        // Empty tests list
        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T1');

        // With 2 sequential tests
        fakeTests.push(getMockedTest({ testName: 'T1' }));
        fakeTests.push(getMockedTest({ testName: 'T2' }));

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T3');
    });

    it('index increments correctly on the worst case scenario', () => {
        const fakeTests: Test[] = [];

        // Empty tests list
        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T1');

        // With 5 non-sequential tests
        fakeTests.push(getMockedTest({ testName: 'T4' }));
        fakeTests.push(getMockedTest({ testName: 'T11' }));
        fakeTests.push(getMockedTest({ testName: 'T1' }));
        fakeTests.push(getMockedTest({ testName: 'T5' }));
        fakeTests.push(getMockedTest({ testName: 'T2' }));

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T3');

        // Add T3 to the list
        fakeTests.push(getMockedTest({ testName: 'T3' }));

        expect(getUniqueNameFromArray(getFakeTestsNames(fakeTests), 'T')).toEqual('T6');
    });
});

describe('onValidFileList', () => {
    it('file array', () => {
        const mockedHandler = jest.fn();
        const validFile = [new File(['foo'], 'foo.txt')];

        onValidFileList(mockedHandler)(validFile);

        expect(mockedHandler).toBeCalledTimes(1);
    });

    it('file list', () => {
        const mockedHandler = jest.fn();

        const mockFileList = {
            0: new File(['foo'], 'foo.txt'),
            1: new File(['foo'], 'foo.txt'),
            length: 2,
        };

        onValidFileList(mockedHandler)(mockFileList as unknown as FileList);

        expect(mockedHandler).toBeCalledTimes(1);
    });

    it('null', () => {
        const mockedHandler = jest.fn();
        onValidFileList(mockedHandler)(null);

        expect(mockedHandler).toBeCalledTimes(0);
    });
});

describe('isNonEmptyString', () => {
    it('valid', () => {
        expect(isNonEmptyString(' ')).toBe(true);
        expect(isNonEmptyString('0')).toBe(true);
    });

    it('falsy', () => {
        expect(isNonEmptyString('')).toBe(false);
        expect(isNonEmptyString(0)).toBe(false);
        expect(isNonEmptyString([])).toBe(false);
        expect(isNonEmptyString(null)).toBe(false);
        expect(isNonEmptyString(undefined)).toBe(false);
    });
});

describe('isNonEmptyArray', () => {
    it('valid', () => {
        expect(isNonEmptyArray([''])).toBe(true);
        expect(isNonEmptyArray([1, 2, 3])).toBe(true);
        expect(isNonEmptyArray(['1', '2'])).toBe(true);
        expect(isNonEmptyArray([undefined])).toBe(true);
    });

    it('falsy', () => {
        expect(isNonEmptyArray('')).toBe(false);
        expect(isNonEmptyArray(0)).toBe(false);
        expect(isNonEmptyArray([])).toBe(false);
        expect(isNonEmptyArray(null)).toBe(false);
        expect(isNonEmptyArray(undefined)).toBe(false);
    });
});

describe('hasEqualSize', () => {
    it('valid', () => {
        expect(hasEqualSize([], [])).toBe(true);
    });

    it('falsy', () => {
        expect(hasEqualSize([], [1])).toBe(false);
    });
});

describe('isNotCropDomain', () => {
    it('valid', () => {
        expect(isNotCropDomain(DOMAIN.DETECTION)).toBe(true);
        expect(isNotCropDomain(DOMAIN.SEGMENTATION)).toBe(true);
        expect(isNotCropDomain(DOMAIN.CLASSIFICATION)).toBe(true);
        expect(isNotCropDomain(DOMAIN.ANOMALY_CLASSIFICATION)).toBe(true);
        expect(isNotCropDomain(DOMAIN.SEGMENTATION_INSTANCE)).toBe(true);
    });

    it('falsy', () => {
        expect(isNotCropDomain(DOMAIN.CROP)).toBe(false);
    });
});

describe('isNotCropTask', () => {
    it('valid', () => {
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.DETECTION }))).toBe(true);
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.SEGMENTATION }))).toBe(true);
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.CLASSIFICATION }))).toBe(true);
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.ANOMALY_CLASSIFICATION }))).toBe(true);
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.SEGMENTATION_INSTANCE }))).toBe(true);
    });

    it('falsy', () => {
        expect(isNotCropTask(getMockedTask({ domain: DOMAIN.CROP }))).toBe(false);
    });
});

describe('hasDifferentId', () => {
    const handler = hasDifferentId('123');

    it('valid', () => {
        expect(handler({ id: '12' })).toBe(true);
        expect(handler({ id: '1234' })).toBe(true);
    });

    it('falsy', () => {
        expect(handler({ id: '123' })).toBe(false);
    });
});

describe('hasEqualId', () => {
    const handler = hasEqualId('123');

    it('valid', () => {
        expect(handler({ id: '123' })).toBe(true);
    });

    it('falsy', () => {
        expect(handler({ id: '12' })).toBe(false);
        expect(handler({ id: '1234' })).toBe(false);
    });
});

describe('isDifferent', () => {
    it('valid', () => {
        expect(isDifferent(1, 2)).toBe(true);
        expect(isDifferent('1', 1)).toBe(true);
    });

    it('falsy', () => {
        expect(isDifferent(1, 1)).toBe(false);
        expect(isDifferent('1', '1')).toBe(false);
        expect(isDifferent([], [])).toBe(false);
        expect(isDifferent({}, {})).toBe(false);
    });
});

it('getIds', () => {
    expect(getIds([])).toEqual([]);
    expect(getIds([{ id: '123' }, { id: '456' }, { id: '789' }])).toEqual(['123', '456', '789']);
});

it('getId', () => {
    expect(getId({ id: '123' })).toEqual('123');
});

it('getDateTimeInISOAndUTCOffsetFormat', () => {
    const mockedFormat = jest.fn();
    getDateTimeInISOAndUTCOffsetFormat({ format: mockedFormat } as unknown as dayjs.Dayjs);
    expect(mockedFormat).toHaveBeenLastCalledWith(DATE_TIME_IN_ISO_AND_UTC_OFFSETFORMAT);
});

it('trimText', () => {
    expect(trimText('test', 3)).toBe('te...');
    expect(trimText('test', 10)).toBe('test');
});

it('getProgressScoreColor', () => {
    expect(getProgressScoreColor(10)).toBe('var(--brand-coral-cobalt)');
    expect(getProgressScoreColor(50)).toBe('var(--brand-daisy)');
    expect(getProgressScoreColor(90)).toBe('var(--brand-moss)');
});

it('loadImage', () => {
    return expect(loadImage('url-test')).resolves.not.toThrow();
});

it('isDateBetween', () => {
    const MIN_DATE = parseDateTime('2023-01-10');
    const MAX_DATE = parseDateTime('2023-01-20');

    expect(isDateBetween(parseDateTime('2023-01-12'), MIN_DATE, MAX_DATE)).toBe(true);
    expect(isDateBetween(parseDateTime('2023-01-02'), MIN_DATE, MAX_DATE)).toBe(false);
    expect(isDateBetween(parseDateTime('2023-01-22'), MIN_DATE, MAX_DATE)).toBe(false);
});

it('formatDownloadUrl', () => {
    expect(formatDownloadUrl('test-url')).toBe('/test-url');
    expect(formatDownloadUrl('/test-url')).toBe('/test-url');
});

it('getFileSize', () => {
    expect(getFileSize(undefined)).toBe('');
    expect(getFileSize(100)).toBe('100 B');
});

it('pluralize', () => {
    expect(pluralize(1, 'test')).toBe('1 test');
    expect(pluralize(0, 'test')).toBe('0 tests');
    expect(pluralize(2, 'test')).toBe('2 tests');
    expect(pluralize(200, 'test')).toBe('200 tests');
});

it('sanitize', () => {
    const projectNames = ['Some project name with lots of spaces', '123456', '=)?;;,km', '♠️Amazing🤩'];

    expect(sanitize(projectNames[0])).toEqual('Some_project_name_with_lots_of_spaces');
    expect(sanitize(projectNames[1])).toEqual('123456');
    expect(sanitize(projectNames[2])).toEqual('______km');
    expect(sanitize(projectNames[3])).toEqual('__Amazing__');
});

it('getDownloadNotificationMessage', () => {
    expect(getDownloadNotificationMessage('test-name')).toEqual(
        'Your test-name file is being prepared and will start downloading shortly.'
    );
});

describe('getIntervalJobHandlers', () => {
    const getMockedDatasetJob = (state: JobState) =>
        ({
            state,
            steps: [getMockedJobStep({ state: JobStepState.FAILED, message: null })],
        }) as JobDataset;

    const defaultErrorResponse = {
        message: 'Something went wrong. Please try again',
        response: { status: 501 },
    };
    const mockedHandlers = {
        onError: jest.fn(),
        onSuccess: jest.fn(),
        onSettled: jest.fn(),
        onCancelOrFailed: jest.fn(),
        onCancel: jest.fn(),
    };

    const intervalHandler = getIntervalJobHandlers(mockedHandlers);

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('finished', () => {
        const job = getMockedDatasetJob(JobState.FINISHED);
        intervalHandler(job);

        expect(mockedHandlers.onSuccess).toHaveBeenCalledWith(job);
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onCancelOrFailed).not.toHaveBeenCalled();
        expect(mockedHandlers.onError).not.toHaveBeenCalled();
    });

    it('cancelled', () => {
        const job = getMockedDatasetJob(JobState.CANCELLED);
        intervalHandler(job);

        expect(mockedHandlers.onCancelOrFailed).toHaveBeenCalled();
        expect(mockedHandlers.onCancel).toHaveBeenCalled();
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onSuccess).not.toHaveBeenCalled();
    });

    it('failed', () => {
        const job = getMockedDatasetJob(JobState.FAILED);
        intervalHandler(job);

        expect(mockedHandlers.onCancelOrFailed).toHaveBeenCalled();
        expect(mockedHandlers.onSettled).toHaveBeenCalled();
        expect(mockedHandlers.onError).toHaveBeenCalledWith(defaultErrorResponse);
        expect(mockedHandlers.onSuccess).not.toHaveBeenCalled();
    });
});
