// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
