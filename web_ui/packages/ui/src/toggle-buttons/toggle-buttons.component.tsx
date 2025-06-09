// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Flex } from '@adobe/react-spectrum';

import styles from './toggle-buttons.module.scss';

interface ToggleButtonProps<T extends string> {
    selectedOption: T;
    option: T;
    onOptionChange: (option: T) => void;
}

const ToggleButton = <T extends string>({ selectedOption, option, onOptionChange }: ToggleButtonProps<T>) => {
    return (
        <Button
            data-activated={selectedOption === option}
            variant={selectedOption === option ? 'accent' : 'secondary'}
            UNSAFE_className={styles.toggleButton}
            onPress={() => {
                onOptionChange(option);
            }}
        >
            {option}
        </Button>
    );
};

interface ToggleButtonsProps<T extends string> {
    options: T[];
    selectedOption: T;
    onOptionChange: (option: T) => void;
}

export const ToggleButtons = <T extends string>({ options, selectedOption, onOptionChange }: ToggleButtonsProps<T>) => {
    return (
        <Flex>
            {options.map((option) => (
                <ToggleButton
                    key={option}
                    selectedOption={selectedOption}
                    option={option}
                    onOptionChange={onOptionChange}
                />
            ))}
        </Flex>
    );
};
