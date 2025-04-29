// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';

import { useLocalAnnotations } from '../../hooks/use-local-annotations.hooks';
import { useAnnotationFilters } from './use-annotation-filters.hook';
import { useOutputAnnotationsFilter } from './use-output-annotations-filter.hook';

export const useHasStaleFilter = () => {
    const annotations = useLocalAnnotations();
    const currentFilteredAnnotations = useOutputAnnotationsFilter(annotations);

    const [filters] = useAnnotationFilters();

    if (isEmpty(filters)) {
        return false;
    }

    return !isEqual(
        annotations.filter((annotation) => annotation.labels.some(({ id }) => filters.includes(id))),
        currentFilteredAnnotations
    );
};
