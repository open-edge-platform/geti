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
