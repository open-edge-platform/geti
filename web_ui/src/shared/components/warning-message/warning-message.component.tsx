// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, ReactNode } from 'react';

import { Flex, Text } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { Alert } from '../../../assets/icons';
import { ANIMATION_PARAMETERS } from '../../animation-parameters/animation-parameters';

import classes from './warning-message.module.scss';

interface WarningMessageProps extends Omit<ComponentProps<typeof Flex>, 'children'> {
    isVisible: boolean;
    message: ReactNode;
    id?: string;
}

export const WarningMessage = ({ isVisible, message, id, ...flexProps }: WarningMessageProps): JSX.Element => {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    variants={ANIMATION_PARAMETERS.FADE_ITEM}
                    initial={'hidden'}
                    animate={'visible'}
                    role='alert'
                >
                    <Flex id={id} alignItems={'center'} gap={'size-100'} {...flexProps}>
                        <Alert aria-label='Notification Alert' className={classes.warningIcon} />
                        <Text UNSAFE_className={classes.warningText} id={'test-dialog-warning-message'}>
                            {message}
                        </Text>
                    </Flex>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
