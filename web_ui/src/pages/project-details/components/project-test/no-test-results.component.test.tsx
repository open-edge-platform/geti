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

import { render, screen } from '@testing-library/react';

import { getMockedTest } from '../../../../core/tests/services/tests-utils';
import { Test } from '../../../../core/tests/tests.interface';
import { NoTestResults } from './no-test-results.component';

describe('NoTestResults', () => {
    it('given a test with at least one dataset deleted, it should inform that the test results were deleted', () => {
        const mockTestWithOneDatasetDeleted: Test = getMockedTest({
            datasetsInfo: [
                {
                    id: 'dataset-1',
                    isDeleted: false,
                    datasetName: 'dataset-1',
                    numberOfImages: 3,
                    numberOfFrames: 0,
                    numberOfSamples: 0,
                },
                {
                    id: 'dataset-2',
                    isDeleted: true,
                    datasetName: 'dataset-2',
                    numberOfImages: 3,
                    numberOfFrames: 1,
                    numberOfSamples: 1,
                },
            ],
        });
        render(<NoTestResults test={mockTestWithOneDatasetDeleted} />);

        expect(screen.getByText('The test results were deleted.')).toBeInTheDocument();
    });

    it('given a test with no datasets deleted, it should inform that to wait for the job to finish', () => {
        const mockTestWithNoDeletedDatasets: Test = getMockedTest({
            datasetsInfo: [
                {
                    id: 'dataset-1',
                    isDeleted: false,
                    datasetName: 'dataset-1',
                    numberOfImages: 3,
                    numberOfFrames: 0,
                    numberOfSamples: 0,
                },
                {
                    id: 'dataset-2',
                    isDeleted: false,
                    datasetName: 'dataset-2',
                    numberOfImages: 3,
                    numberOfFrames: 1,
                    numberOfSamples: 1,
                },
            ],
        });
        render(<NoTestResults test={mockTestWithNoDeletedDatasets} />);

        expect(screen.getByText('Please wait for the test job to finish.')).toBeInTheDocument();
    });
});
