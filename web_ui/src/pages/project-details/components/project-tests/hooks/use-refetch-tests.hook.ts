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

import { useEffect } from 'react';

import isEmpty from 'lodash/isEmpty';

import { JobInfoStatus } from '../../../../../core/tests/dtos/tests.interface';
import { Test } from '../../../../../core/tests/tests.interface';

const TIME_TO_REFETCH_TESTS = 2000;

export const useRefetchTests = (tests: Test[], refetch: () => Promise<void>) => {
    useEffect(() => {
        let refetchId: ReturnType<typeof setInterval> | null = null;

        const shouldRefetchTests =
            !isEmpty(tests) &&
            !tests.every(
                ({ jobInfo }) => jobInfo.status === JobInfoStatus.DONE || jobInfo.status === JobInfoStatus.ERROR
            );

        if (shouldRefetchTests) {
            refetchId = setInterval(async () => {
                await refetch();
            }, TIME_TO_REFETCH_TESTS);
        } else {
            refetchId && clearInterval(refetchId);
            refetchId = null;
        }

        return () => {
            refetchId && clearInterval(refetchId);
        };
    }, [tests, refetch]);
};
