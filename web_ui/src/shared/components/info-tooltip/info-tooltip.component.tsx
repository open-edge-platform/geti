// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties, ReactNode } from 'react';

import { Content, ContextualHelp, Text } from '@adobe/react-spectrum';

interface InfoTooltipProps {
    id: string;
    tooltipText: ReactNode;
    iconColor?: string | undefined;
}

export const InfoTooltip = ({ tooltipText, id, iconColor }: InfoTooltipProps): JSX.Element => {
    const style = iconColor ? ({ '--spectrum-alias-icon-color': iconColor } as CSSProperties) : {};

    return (
        <ContextualHelp variant='info' id={id} data-testid={id} UNSAFE_style={style}>
            <Content marginTop='0'>
                <Text>{tooltipText}</Text>
            </Content>
        </ContextualHelp>
    );
};
