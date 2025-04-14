// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Item, Key, Picker, View } from '@adobe/react-spectrum';

import { SearchRuleValue } from '../../../../core/media/media-filter.interface';
import { MEDIA_TYPE_OPTIONS } from '../../utils';

interface MediaFilterValueTypeProps {
    value: SearchRuleValue;
    isDisabled?: boolean;
    onSelectionChange: (key: SearchRuleValue) => void;
}

export const MediaFilterValueType = ({
    value = '',
    isDisabled = false,
    onSelectionChange,
}: MediaFilterValueTypeProps): JSX.Element => {
    const handleSelectionChange = (key: Key) => {
        onSelectionChange(key);
    };

    return (
        <View position='relative'>
            <Picker
                isQuiet
                isDisabled={isDisabled}
                items={MEDIA_TYPE_OPTIONS}
                id='media-filter-media-type'
                aria-label='media-filter-media-type'
                selectedKey={MEDIA_TYPE_OPTIONS.find((option) => option.text === value)?.key}
                onSelectionChange={handleSelectionChange}
            >
                {(item) => (
                    <Item key={item.key} aria-label={`option-${item.key}`}>
                        {item.text}
                    </Item>
                )}
            </Picker>
        </View>
    );
};
