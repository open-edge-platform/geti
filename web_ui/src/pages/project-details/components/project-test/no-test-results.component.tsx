// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CardContent } from '@shared/components/card-content/card-content.component';
import { NotFound } from '@shared/components/not-found/not-found.component';

import { Test } from '../../../../core/tests/tests.interface';

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
