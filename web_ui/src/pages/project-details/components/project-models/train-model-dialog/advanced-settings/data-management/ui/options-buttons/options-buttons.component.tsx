// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import clsx from 'clsx';

import { Button } from '../../../../../../../../../shared/components/button/button.component';

import styles from './options-buttons.module.scss';

interface OptionButtonProps<T extends string> {
    selectedOption: T;
    option: T;
    onOptionChange: (option: T) => void;
    className: string;
}

const OptionButton = <T extends string>({
    selectedOption,
    option,
    onOptionChange,
    className,
}: OptionButtonProps<T>) => {
    return (
        <Button
            variant={selectedOption === option ? 'accent' : 'secondary'}
            UNSAFE_className={clsx(styles.optionButton, className)}
            onPress={() => {
                onOptionChange(option);
            }}
        >
            {option}
        </Button>
    );
};

interface OptionsButtonsProps<T extends string> {
    options: T[];
    selectedOption: T;
    onOptionChange: (option: T) => void;
}

export const OptionsButtons = <T extends string>({
    options,
    selectedOption,
    onOptionChange,
}: OptionsButtonsProps<T>) => {
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
                <OptionButton
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
