// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Flex, Loading, Text } from '@geti/ui';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';

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
                        <Loading mode='inline' size={'S'} marginEnd={'size-200'} />
                        <Text>Retrieving inference results may take some time</Text>
                        <ActionButton isQuiet UNSAFE_className={classes.cancelInference} onPress={dismiss}>
                            Dismiss
                        </ActionButton>
                    </Flex>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
