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

import { forwardRef } from 'react';

import { Flex, Text, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';

import { Button } from '../../../../../shared/components/button/button.component';

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
