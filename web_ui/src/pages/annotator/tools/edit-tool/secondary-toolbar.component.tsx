// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text } from '@geti/ui';

import { ToolAnnotationContextProps } from '../tools.interface';

export const SecondaryToolbar = (_annotationToolContext: ToolAnnotationContextProps): JSX.Element => {
    return (
        <Flex>
            <Text>Edit</Text>
        </Flex>
    );
};
