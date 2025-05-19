// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Grid, Text } from '@adobe/react-spectrum';
import { Switch } from '@geti/ui';

export interface DataAugmentationOption {
    key: string;
    name: string;
    value: boolean;
}

interface DataAugmentationOptionProps {
    option: DataAugmentationOption;
    onOptionChange: (isEnabled: boolean) => void;
}

const DataAugmentationOption: FC<DataAugmentationOptionProps> = ({ option, onOptionChange }) => {
    const { name, value } = option;
    return (
        <>
            <Text>{name}</Text>
            <Switch isEmphasized isSelected={value} aria-label={`Toggle ${name}`} onChange={onOptionChange}>
                {value ? 'On' : 'Off'}
            </Switch>
        </>
    );
};

interface DataAugmentationOptionsProps {
    options: DataAugmentationOption[];
    onOptionsChange: (options: DataAugmentationOption[]) => void;
}

export const DataAugmentationOptions: FC<DataAugmentationOptionsProps> = ({ options, onOptionsChange }) => {
    return (
        <Grid columns={['max-content', 'max-content']} columnGap={'size-1000'}>
            {options.map((option) => (
                <DataAugmentationOption
                    key={option.key}
                    option={option}
                    onOptionChange={(value: boolean) => {
                        const updatedOptions = options.map((opt) => (opt.key === option.key ? { ...opt, value } : opt));
                        onOptionsChange(updatedOptions);
                    }}
                />
            ))}
        </Grid>
    );
};
