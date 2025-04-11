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

import { Flex, Text } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { LoadingIndicator } from '../../../../../shared/components/loading/loading-indicator.component';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';

import classes from './quick-inference.module.scss';

interface WaitingInferenceProps {
    isVisible: boolean;
    dismiss: () => void;
}

export const WaitingInference = ({ isVisible, dismiss }: WaitingInferenceProps) => {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    role='alert'
                    exit='hidden'
                    initial='hidden'
                    animate='visible'
                    variants={ANIMATION_PARAMETERS.FADE_ITEM}
                >
                    <Flex
                        gap={'size-200'}
                        alignItems={'center'}
                        position={'relative'}
                        UNSAFE_className={classes.waitingWraper}
                    >
                        <LoadingIndicator size={'S'} marginEnd={'size-200'} />
                        <Text>Retrieving inference results may take some time</Text>
                        <QuietActionButton UNSAFE_className={classes.cancelInference} onPress={dismiss}>
                            Dismiss
                        </QuietActionButton>
                    </Flex>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
