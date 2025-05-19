// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@geti/ui';
import { usePress } from 'react-aria';

import { Label } from '../../../../../core/labels/label.interface';
import { LabelTag } from '../label-tag/label-tag.component';

import classes from './selectable-label-tag.module.scss';

interface SelectableLabelTagProps {
    label: Label;
    value: string;
    selectedOption: string;
    handleOptionChange: (selectedOption: string) => void;
}

export const SelectableLabelTag = ({
    selectedOption,
    value,
    label,
    handleOptionChange,
}: SelectableLabelTagProps): JSX.Element => {
    const onPress = () => handleOptionChange(value);
    const { pressProps } = usePress({ onPress });

    const isSelectedOption = selectedOption === value;

    return (
        <div {...pressProps}>
            <View
                id={label.id}
                borderRadius={'regular'}
                borderColor={'gray-400'}
                borderWidth={isSelectedOption ? 'thick' : 'thin'}
                paddingX={'size-65'}
                paddingY={'size-25'}
                UNSAFE_className={isSelectedOption ? classes.selected : undefined}
            >
                <LabelTag label={label} onClick={onPress} />
            </View>
        </div>
    );
};
