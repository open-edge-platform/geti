// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import isEmpty from 'lodash/isEmpty';

import { AdvancedFilterOptions } from '../../../core/media/media-filter.interface';

export const useMediaFilterEmpty = (mediaFilterOptions: AdvancedFilterOptions): boolean => {
    return useMemo(() => {
        return isEmpty(mediaFilterOptions) || isEmpty(mediaFilterOptions.rules);
    }, [mediaFilterOptions]);
};
