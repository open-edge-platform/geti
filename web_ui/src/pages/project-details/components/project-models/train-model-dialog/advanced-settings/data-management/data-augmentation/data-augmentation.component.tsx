// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, useState } from 'react';

import { Accordion } from '../../ui/accordion/accordion.component';
import { DataAugmentationOption, DataAugmentationOptions } from './data-augmentation-options.component';

const OPTIONS: DataAugmentationOption[] = [
    {
        key: 'horizontal_flip',
        name: 'Horizontal flip',
        value: false,
    },
    {
        key: 'vertical_flip',
        name: 'Vertical flip',
        value: false,
    },
    {
        key: 'gaussian_blur',
        name: 'Gaussian blur',
        value: false,
    },
    {
        key: 'hue_saturation_value',
        name: 'Hue saturation value',
        value: false,
    },
    {
        key: 'random_rotate',
        name: 'Random rotate',
        value: false,
    },
];

export const DataAugmentation: FC = () => {
    const [options, setOptions] = useState<DataAugmentationOption[]>(OPTIONS);

    const isAnyOptionEnabled = options.some((option) => option.value);

    return (
        <Accordion>
            <Accordion.Title>
                Data Augmentation<Accordion.Tag>{isAnyOptionEnabled ? 'Yes' : 'No'}</Accordion.Tag>
            </Accordion.Title>
            <Accordion.Content>
                <Accordion.Description>
                    Choose data augmentation transformations to enhance the diversity of available data for training
                    models.
                </Accordion.Description>
                <Accordion.Divider marginY={'size-250'} />
                <DataAugmentationOptions options={options} onOptionsChange={setOptions} />
            </Accordion.Content>
        </Accordion>
    );
};
