// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
