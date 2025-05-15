// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

interface CPSelectableItemProps<T extends string | number> {
    id: string;
    value: T;
    selectedOption: T;
    handleOptionChange: (selectedOption: T) => void;
}

export const CPSelectableItem = <T extends string | number>(props: CPSelectableItemProps<T>): JSX.Element => {
    const { id, value, handleOptionChange, selectedOption } = props;

    const { pressProps } = usePress({
        onPress: () => {
            handleOptionChange(value);
        },
    });

    return (
        <div {...pressProps}>
            <View
                id={id}
                borderColor={'gray-400'}
                borderRadius={'small'}
                borderWidth={'thin'}
                paddingX={'size-150'}
                paddingY={'size-65'}
                backgroundColor={selectedOption === value ? 'gray-200' : 'gray-50'}
                UNSAFE_style={{ cursor: 'pointer' }}
            >
                {value}
            </View>
        </div>
    );
};
