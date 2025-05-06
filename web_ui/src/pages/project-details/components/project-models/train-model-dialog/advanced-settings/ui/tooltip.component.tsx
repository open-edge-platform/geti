// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { Content, ContextualHelp, Text } from '@adobe/react-spectrum';

export const Tooltip: FC<{ children: ReactNode }> = ({ children }) => {
    return (
        <ContextualHelp variant='info'>
            <Content>
                <Text>{children}</Text>
            </Content>
        </ContextualHelp>
    );
};
