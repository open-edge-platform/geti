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

import { Test } from '../../../../core/tests/tests.interface';
import { CardContent } from '../../../../shared/components/card-content/card-content.component';
import { NotFound } from '../../../../shared/components/not-found/not-found.component';

interface TestDetailsProps {
    test: Test;
}

export const NoTestResults = ({ test }: TestDetailsProps): JSX.Element => {
    const testingDatasetWasDeleted = test.datasetsInfo.some(({ isDeleted }) => isDeleted);

    return (
        <CardContent title={'Annotations vs Predictions'} gridArea={'media'}>
            <NotFound
                content={
                    testingDatasetWasDeleted
                        ? 'The test results were deleted.'
                        : 'Please wait for the test job to finish.'
                }
            />
        </CardContent>
    );
};
