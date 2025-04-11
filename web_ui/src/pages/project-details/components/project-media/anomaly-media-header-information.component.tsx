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

import { Divider, Flex, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import classes from './anomaly-media-header-information.module.scss';

interface AnomalyMediaHeaderInformationProps {
    headerText: string;
    countElements: string | undefined;
    description: string;
}

export const AnomalyMediaHeaderInformation = ({
    countElements,
    description,
    headerText,
}: AnomalyMediaHeaderInformationProps): JSX.Element => {
    return (
        <Flex direction={'column'} flex={1}>
            <Flex gap='size-100' alignItems='center'>
                <Text UNSAFE_className={classes.header}>{headerText}</Text>

                {!isEmpty(countElements) && (
                    <>
                        <Divider orientation='vertical' size='S' />
                        <Text id='count-message-id' data-testid='count-message-id'>
                            {countElements}
                        </Text>
                    </>
                )}
            </Flex>
            <Text UNSAFE_className={classes.description}>{description}</Text>
        </Flex>
    );
};
