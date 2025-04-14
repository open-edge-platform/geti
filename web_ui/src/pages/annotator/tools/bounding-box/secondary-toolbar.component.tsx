// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

export const SecondaryToolbar = (): JSX.Element => {
    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Bounding Box Tool</Text>
        </Flex>
    );
};
