// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';

interface MediaCountProps {
    selectedItems: number;
    countMessage: string;
}

export const MediaCount = ({ selectedItems, countMessage }: MediaCountProps): JSX.Element => {
    const hasSelectedItems = selectedItems > 0;

    return (
        <Flex gap='size-200' flex={1} alignSelf={'center'} justifyContent={'end'}>
            <AnimatePresence>
                {hasSelectedItems && (
                    <>
                        <motion.div
                            data-testid={'selected-items-count-id'}
                            variants={ANIMATION_PARAMETERS.FADE_ITEM}
                            initial={'hidden'}
                            animate={'visible'}
                        >
                            <Text>Selected: {selectedItems}</Text> <Divider orientation='vertical' size='S' />
                        </motion.div>
                        <Divider orientation='vertical' size='S' />
                    </>
                )}
            </AnimatePresence>
            <motion.span
                data-testid={'count-message-id'}
                variants={ANIMATION_PARAMETERS.FADE_ITEM}
                initial={'hidden'}
                animate={'visible'}
            >
                {countMessage}
            </motion.span>
            {!hasSelectedItems && <Divider orientation='vertical' size='S' />}
        </Flex>
    );
};
