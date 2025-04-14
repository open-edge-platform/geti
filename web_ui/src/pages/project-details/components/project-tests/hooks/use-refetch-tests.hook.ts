// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
