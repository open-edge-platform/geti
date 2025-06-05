// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Flex } from '@geti/ui';
import clsx from 'clsx';

import styles from './toggle-buttons.module.scss';

interface ToggleButtonProps<T extends string> {
    selectedOption: T;
    option: T;
    onOptionChange: (option: T) => void;
    className: string;
}

const ToggleButton = <T extends string>({
    selectedOption,
    option,
    onOptionChange,
    className,
}: ToggleButtonProps<T>) => {
    return (
        <Button
            data-activated={selectedOption === option}
            variant={selectedOption === option ? 'accent' : 'secondary'}
            UNSAFE_className={clsx(styles.toggleButton, className)}
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
    const getClassNames = (index: number) => {
        if (index === 0) {
            return styles.firstOptionButton;
        }
        if (index === options.length - 1) {
            return styles.lastOptionButton;
        }
        return styles.middleButton;
    };

    return (
        <Flex>
            {options.map((option, index) => (
                <ToggleButton
                    key={option}
                    selectedOption={selectedOption}
                    option={option}
                    onOptionChange={onOptionChange}
                    className={getClassNames(index)}
                />
            ))}
        </Flex>
    );
};
