// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps } from 'react';

import { Content, Heading, InlineAlert } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';

import { ANIMATION_PARAMETERS } from '../../animation-parameters/animation-parameters';
import { CustomerSupportLink } from '../customer-support-link/customer-support-link.component';

interface InvalidTokenAlertProps {
    isVisible: boolean;
    message: string;
    styles?: Omit<ComponentProps<typeof InlineAlert>, 'variant' | 'width' | 'children'>;
}

export const InvalidTokenAlert = ({ isVisible, message, styles }: InvalidTokenAlertProps): JSX.Element => {
    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                    <InlineAlert variant='negative' width={'100%'} {...styles}>
                        <Heading>{message}</Heading>
                        <Content>
                            Please contact <CustomerSupportLink /> to request a new invitation.
                        </Content>
                    </InlineAlert>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
