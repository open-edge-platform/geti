// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
