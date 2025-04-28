// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { PressableElement } from '../../../../../shared/components/action-element/action-element.component';

interface VideoItemDataIndicatorProps {
    children: ReactNode;
    tooltip?: string;
    id: string;
}

export const VideoItemDataIndicator = ({ children, tooltip, id }: VideoItemDataIndicatorProps): JSX.Element => {
    return (
        <View
            id={id}
            data-testid={id}
            paddingX={'size-50'}
            borderColor={'gray-400'}
            borderWidth={'thin'}
            borderRadius={'regular'}
        >
            <TooltipTrigger placement={'bottom'}>
                <PressableElement>
                    <Text>{children}</Text>
                </PressableElement>
                <Tooltip>{tooltip}</Tooltip>
            </TooltipTrigger>
        </View>
    );
};
