// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { forwardRef } from 'react';

import { Flex, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';

import classes from './annotations-required.module.scss';

interface NoAnnotationsRequiredProps {
    id?: string;
}

export const NoAnnotationsRequired = forwardRef<HTMLDivElement, NoAnnotationsRequiredProps>((props, ref) => {
    return (
        <div ref={ref}>
            <TooltipTrigger placement={'bottom'}>
                <Flex id={props.id} alignItems='center' gap='size-100'>
                    <Text id='annotations-required-id' UNSAFE_className={classes.text}>
                        Annotations required:
                    </Text>
                    <Button isQuiet variant='primary' UNSAFE_className={classes.tooltipButton}>
                        <View
                            paddingY='size-25'
                            paddingX='size-75'
                            borderRadius='small'
                            id='training-dots-id'
                            data-testid='training-dots'
                            backgroundColor='gray-400'
                        >
                            ...
                        </View>
                    </Button>
                </Flex>
                <Tooltip>
                    The required number of annotations for the next learning cycle is being calculated. Meanwhile, keep
                    annotating to make the model more accurate.
                </Tooltip>
            </TooltipTrigger>
        </div>
    );
});
