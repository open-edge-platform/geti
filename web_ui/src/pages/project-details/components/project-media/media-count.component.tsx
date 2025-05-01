// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import { ANIMATION_PARAMETERS } from '@shared/animation-parameters/animation-parameters';
import { AnimatePresence, motion } from 'framer-motion';

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
