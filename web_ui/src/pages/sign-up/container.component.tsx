// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { FC, ReactNode } from 'react';

import { Flex, Header, Heading, View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../shared/animation-parameters/animation-parameters';

import classes from './container.module.scss';

interface ContainerProps {
    children: ReactNode;
    title: string;
    isOpen: boolean;
}

export const Container: FC<ContainerProps> = ({ children, title, isOpen }) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                    <Flex alignItems={'center'} justifyContent={'center'} height={'100vh'}>
                        <View minWidth={'50vh'} width={'640px'} borderRadius={'medium'} overflow={'hidden'}>
                            <Header UNSAFE_className={classes.header} height={'size-1250'}>
                                <Flex alignItems={'center'} justifyContent={'center'} height={'100%'}>
                                    <Heading level={1} margin={0}>
                                        {title}
                                    </Heading>
                                </Flex>
                            </Header>
                            <View backgroundColor={'gray-100'} padding={'size-800'}>
                                {children}
                            </View>
                        </View>
                    </Flex>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
