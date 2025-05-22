// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';

export const HotkeyLabel = (): JSX.Element => {
    return (
        <Flex direction={'column'} alignItems={'start'} justifyContent={'center'}>
            <Text UNSAFE_style={{ width: 'max-content' }}>Keyboard</Text>
            <Text UNSAFE_style={{ width: 'max-content' }}>shortcut</Text>
        </Flex>
    );
};
