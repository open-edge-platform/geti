// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
