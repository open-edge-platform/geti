// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { MoreMenu } from '../../../assets/icons';
import { DATASET_NAME_MAX_WIDTH } from '../../../pages/project-details/components/project-dataset/utils';
import { ANIMATION_PARAMETERS } from '../../animation-parameters/animation-parameters';
import { TruncatedText } from '../truncated-text/truncated-text.component';

import classes from './custom-tab-item.module.scss';

export interface CustomTabItemProps {
    name: string;
    isMoreIconVisible: boolean;
}

export const CustomTabItem = ({ name, isMoreIconVisible }: CustomTabItemProps): JSX.Element => {
    return (
        <Flex
            alignItems={'center'}
            gap={'size-50'}
            UNSAFE_className={!isMoreIconVisible ? classes.customTabItemContainer : undefined}
        >
            <View maxWidth={DATASET_NAME_MAX_WIDTH}>
                <TruncatedText
                    aria-label={name}
                    data-testid='dataset-name'
                    UNSAFE_className={isMoreIconVisible ? classes.customTabItemName : undefined}
                >
                    {name}
                </TruncatedText>
            </View>
            <View width={'size-200'} height={'size-200'}>
                <AnimatePresence>
                    {isMoreIconVisible && (
                        <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} animate={'visible'} initial={'hidden'}>
                            <MoreMenu />
                        </motion.div>
                    )}
                </AnimatePresence>
            </View>
        </Flex>
    );
};
