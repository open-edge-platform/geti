// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Grid, minmax } from '@geti/ui';

import {
    BoolParameter,
    NumberParameter,
    TrainingConfiguration,
} from '../../../../../../../../core/configurable-parameters/services/configuration.interface';
import { isBoolParameter, isNumberParameter } from '../../../../../../../../core/configurable-parameters/utils';
import { Accordion } from '../../ui/accordion/accordion.component';
import { FilterOption, FiltersOptions } from './filters-options.component';

type FiltersConfiguration = TrainingConfiguration['datasetPreparation']['filtering'];

interface FiltersProps {
    filtersConfiguration: FiltersConfiguration;
    onUpdateTrainingConfiguration: (
        updateFunction: (config: TrainingConfiguration | undefined) => TrainingConfiguration | undefined
    ) => void;
}

export const Filters: FC<FiltersProps> = ({ filtersConfiguration, onUpdateTrainingConfiguration }) => {
    const filterOptions: FilterOption[] = Object.values(filtersConfiguration)
        .map(([enableParameter, configParameter]) => {
            if (isBoolParameter(enableParameter) && isNumberParameter(configParameter)) {
                return [enableParameter, configParameter] as [BoolParameter, NumberParameter];
            }

            return undefined;
        })
        .filter((option) => option !== undefined);

    const handleFilterOptionChange = ([enableParameter, configParameter]: FilterOption) => {
        onUpdateTrainingConfiguration((prevConfig) => {
            if (prevConfig === undefined) {
                return;
            }

            const newConfig = structuredClone(prevConfig);

            newConfig.datasetPreparation.filtering = Object.entries(
                prevConfig.datasetPreparation.filtering
            ).reduce<FiltersConfiguration>((acc, [key, parameters]) => {
                const [enableParameterLocal, configParameterLocal] = parameters;

                if (
                    enableParameter.key === enableParameterLocal.key &&
                    configParameter.key === configParameterLocal.key
                ) {
                    return {
                        ...acc,
                        [key]: [enableParameter, configParameter],
                    };
                }

                return {
                    ...acc,
                    [key]: parameters,
                };
            }, {});

            return newConfig;
        });
    };

    const areFiltersEnabled = filterOptions.some(([enableParameter]) => enableParameter.value);

    return (
        <Accordion>
            <Accordion.Title>
                Filters <Accordion.Tag> {areFiltersEnabled ? 'On' : 'Off'}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>
                    Use filters to specify the criteria for annotations that will be used for training.
                </Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <Grid
                    columns={['size-3000', minmax('size-3400', '1fr'), 'size-400']}
                    gap={'size-300'}
                    alignItems={'center'}
                >
                    <FiltersOptions options={filterOptions} onOptionsChange={handleFilterOptionChange} />
                </Grid>
            </Accordion.Content>
        </Accordion>
    );
};
