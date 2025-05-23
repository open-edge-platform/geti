// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { Flex, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { AdvancedFilterOptions, SearchRuleField } from '../../../../core/media/media-filter.interface';
import { isAnomalyDomain } from '../../../../core/projects/domains';
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
