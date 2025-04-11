// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Text, View } from '@adobe/react-spectrum';

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
