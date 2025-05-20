// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Text, View } from '@geti/ui';

import classes from './hotkey.module.scss';

interface HotkeyProps {
    hotkey: string;
}

export const Hotkey = ({ hotkey }: HotkeyProps): JSX.Element => {
    return (
        <View backgroundColor={'gray-200'} paddingX={'size-100'} paddingY={'size-50'}>
            <Text UNSAFE_className={classes.hotkeyText}>{hotkey.toLocaleUpperCase()}</Text>
        </View>
    );
};
