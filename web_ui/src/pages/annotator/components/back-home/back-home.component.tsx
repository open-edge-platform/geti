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

import { Flex, View } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AdvancedFilterOptions, SearchRuleField } from '../../../../core/media/media-filter.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { paths } from '../../../../core/services/routes';
import {
    encodeFilterSearchParam,
    getFilterParam,
} from '../../../../hooks/use-filter-search-param/use-filter-search-param.hook';
import { BackButton as BackHomeButton } from '../../../../shared/components/back-button/back-button.component';
import { isMediaFilterOptions } from '../../../media/utils';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useDatasetIdentifier } from '../../hooks/use-dataset-identifier.hook';
import { useSubmitAnnotations } from '../../providers/submit-annotations-provider/submit-annotations-provider.component';

const getDatasetFilter = (searchParams: URLSearchParams, isAnomaly = false): string => {
    const filter = searchParams.get('filter');

    if (filter === null) {
        return '';
    }

    if (isAnomaly) {
        const decodedFilters = getFilterParam<AdvancedFilterOptions>(filter);
        if (
            isMediaFilterOptions(decodedFilters) &&
            decodedFilters.rules.some(({ field }) => field === SearchRuleField.LabelId)
        ) {
            const filtersWithoutLabelIdRule: AdvancedFilterOptions = {
                condition: decodedFilters.condition,
                rules: decodedFilters.rules.filter(({ field }) => field !== SearchRuleField.LabelId),
            };

            const encodedFilters = encodeFilterSearchParam(filtersWithoutLabelIdRule);
            const filterSearchParams = new URLSearchParams([
                ['filter-normal', encodedFilters],
                ['filter-anomalous', encodedFilters],
            ]);

            return `?${filterSearchParams.toString()}`;
        }

        const newSearchParams = new URLSearchParams([
            ['filter-normal', filter],
            ['filter-anomalous', filter],
        ]);

        return `?${newSearchParams.toString()}`;
    }

    const newSearchParams = new URLSearchParams([['filter', filter]]);

    return `?${newSearchParams.toString()}`;
};

const getSortingParams = (searchParams: URLSearchParams, hasFilter: boolean): string => {
    const sortBy = searchParams.get('sortBy');
    const sortDirection = searchParams.get('sortDirection');
    const separator = hasFilter ? '&' : '?';

    if (sortBy === null) {
        return '';
    }

    return `${separator}sortBy=${sortBy}&sortDirection=${sortDirection}`;
};

export const BackHome = (): JSX.Element => {
    const navigate = useNavigate();
    const datasetIdentifier = useDatasetIdentifier();
    const { confirmSaveAnnotations } = useSubmitAnnotations();
    const { isSingleDomainProject } = useProject();
    const [searchParams] = useSearchParams();

    const handleGoBack = () => {
        confirmSaveAnnotations(async () => {
            // Remember the filter that the user used in the annotator
            const search = getDatasetFilter(searchParams, isSingleDomainProject(isAnomalyDomain));
            const sorting = getSortingParams(searchParams, !isEmpty(search));

            navigate(`${paths.project.dataset.media(datasetIdentifier)}${search}${sorting}`);
        });
    };

    return (
        <View backgroundColor='gray-200'>
            <Flex gridArea='backHome' alignContent='center' justifyContent='center' alignItems='center' height='100%'>
                <BackHomeButton onPress={handleGoBack} />
            </Flex>
        </View>
    );
};
