// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect } from 'react';

import { useSearchParams } from 'react-router-dom';

import { isAnomalyDomain } from '../../../../core/projects/domains';
import { useTask } from '../task-provider/task-provider.component';

export const useIsInActiveMode = (): boolean => {
    const [searchParams, setSearchParams] = useSearchParams();
    const { selectedTask } = useTask();

    const isInActiveMode =
        searchParams.has('active') && (selectedTask === null || !isAnomalyDomain(selectedTask.domain));

    useEffect(() => {
        if (searchParams.has('active') && !isInActiveMode) {
            searchParams.delete('active');
            setSearchParams(searchParams);
        }
    }, [isInActiveMode, searchParams, setSearchParams]);

    return isInActiveMode;
};
