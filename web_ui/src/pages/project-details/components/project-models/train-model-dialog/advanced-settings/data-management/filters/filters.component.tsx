// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Grid, minmax, Switch, Text } from '@geti/ui';

import { Accordion } from '../../ui/accordion/accordion.component';
import { FilterOption, FiltersOptions } from './filters-options.component';

const OPTIONS: FilterOption[] = [
    {
        key: 'min_pixel_area_for_objects',
        name: 'Min pixel area for objects',
        value: 1,
        minValue: 1,
        maxValue: 1000,
        defaultValue: 1,
        description: 'Minimum pixel area for objects',
    },
    {
        key: 'max_pixel_area_for_objects',
        name: 'Max pixel area for objects',
        value: 2,
        unlimited: true,
        description: 'Maximum pixel area for objects',
        minValue: 1,
        maxValue: 1000,
        defaultValue: 2,
    },
    {
        key: 'min_number_of_objects_per_label',
        name: 'Min number of objects per label',
        value: 1,
        minValue: 1,
        maxValue: 1000,
        description: 'Minimum number of objects per label',
        defaultValue: 1,
    },
    {
        key: 'max_number_of_objects_per_label',
        name: 'Max number of objects per label',
        value: 1,
        minValue: 1,
        maxValue: 1000,
        description: 'Max number of objects per label',
        defaultValue: 1,
        unlimited: false,
    },
];

export const Filters: FC = () => {
    const [areFiltersEnabled, setAreFiltersEnabled] = useState<boolean>(false);
    const [options, setOptions] = useState<FilterOption[]>(OPTIONS);

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
                    columns={['size-2400', minmax('size-3400', '1fr'), 'size-400']}
                    gap={'size-300'}
                    alignItems={'center'}
                >
                    <Text gridColumn={'1/2'}>Filters</Text>
                    <Switch
                        gridColumn={'2/3'}
                        isEmphasized
                        isSelected={areFiltersEnabled}
                        onChange={setAreFiltersEnabled}
                        aria-label={`${areFiltersEnabled ? 'Enabled' : 'Disabled'} filters`}
                    >
                        {areFiltersEnabled ? 'On' : 'Off'}
                    </Switch>
                    {areFiltersEnabled && <FiltersOptions options={options} onOptionsChange={setOptions} />}
                </Grid>
            </Accordion.Content>
        </Accordion>
    );
};
