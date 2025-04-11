// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect, useMemo, useState } from 'react';

import isEmpty from 'lodash/isEmpty';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { hasEqualId } from '../../../../shared/utils';
import { useAnnotationFilters } from './use-annotation-filters.hook';

const getAnnotationsFilter = (filters: string[]) => {
    return (annotation: Annotation) => {
        return !annotation.labels.some(({ id }) => filters.includes(id));
    };
};

export const useOutputAnnotationsFilter = (annotations: Annotation[]): Annotation[] => {
    const [filters] = useAnnotationFilters();
    const filterAnnotations = getAnnotationsFilter(filters);
    const [rejectedAnnotations, setRejectedAnnotations] = useState(annotations.filter(filterAnnotations));

    useEffect(() => {
        setRejectedAnnotations(annotations.filter(filterAnnotations));
        // We only want to apply the filter when a user changes the annotation filters
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filters]);

    const areFiltersDisabled = isEmpty(filters);

    return useMemo(() => {
        if (areFiltersDisabled) {
            return annotations;
        }

        return annotations.filter(({ id }) => !rejectedAnnotations.some(hasEqualId(id)));
    }, [rejectedAnnotations, annotations, areFiltersDisabled]);
};
