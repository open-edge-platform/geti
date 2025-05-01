// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Flex, NumberField, Text } from '@adobe/react-spectrum';
import { ActionButton } from '@shared/components/button/button.component';
import { Checkbox } from '@shared/components/checkbox/checkbox.component';

import { Refresh } from '../../../../../../../../assets/icons';
import { Tooltip } from '../../ui/tooltip.component';

export interface FilterOption {
    key: string;
    name: string;
    value: number;
    unlimited?: boolean;
    defaultValue: number;
    maxValue: number;
    minValue: number;
    description: string;
}

interface FilterOptionProps {
    option: FilterOption;
    onOptionChange: (option: FilterOption) => void;
}

interface FilterOptionTooltipProps {
    description: string;
}

const FilterOptionTooltip: FC<FilterOptionTooltipProps> = ({ description }) => {
    return <Tooltip>{description}</Tooltip>;
};

const FilterOption: FC<FilterOptionProps> = ({ option, onOptionChange }) => {
    const { name, defaultValue, maxValue, minValue, value, unlimited, description } = option;

    const handleRest = () => {
        onOptionChange({ ...option, value: defaultValue });
    };

    const handleFilterValueChange = (inputValue: number) => {
        const updatedOption = { ...option, value: inputValue };
        onOptionChange(updatedOption);
    };

    const handleUnlimitedChange = (isUnlimited: boolean) => {
        const updatedOption = { ...option, unlimited: isUnlimited };
        onOptionChange(updatedOption);
    };

    return (
        <>
            <Text gridColumn={'1/2'}>
                {name} <FilterOptionTooltip description={description} />
            </Text>
            <Flex gap={'size-200'} gridColumn={'2/3'}>
                <NumberField
                    minValue={minValue}
                    maxValue={maxValue}
                    step={1}
                    value={value}
                    isDisabled={unlimited}
                    defaultValue={defaultValue}
                    onChange={handleFilterValueChange}
                />
                {unlimited !== undefined && (
                    <Checkbox isEmphasized isSelected={unlimited} onChange={handleUnlimitedChange}>
                        Unlimited
                    </Checkbox>
                )}
            </Flex>
            <ActionButton gridColumn={'3/4'} isQuiet aria-label={`Reset ${name}`} onPress={handleRest}>
                <Refresh />
            </ActionButton>
        </>
    );
};

interface FiltersOptionsProps {
    options: FilterOption[];
    onOptionsChange: (options: FilterOption[]) => void;
}

export const FiltersOptions: FC<FiltersOptionsProps> = ({ options, onOptionsChange }) => {
    return (
        <>
            {options.map((option) => (
                <FilterOption
                    key={option.key}
                    option={option}
                    onOptionChange={(updatedOption) => {
                        const updatedOptions = options.map((opt) => (opt.key === option.key ? updatedOption : opt));
                        onOptionsChange(updatedOptions);
                    }}
                />
            ))}
        </>
    );
};
