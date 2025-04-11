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

import { Flex, Image, View } from '@adobe/react-spectrum';
import { Heading, Text } from '@react-spectrum/text';

import LearnSectionImage from '../../../../../assets/images/learn-section-image.webp';
import { useDocsUrl } from '../../../../../hooks/use-docs-url/use-docs-url.hook';
import { CustomWellClickable } from '../../../../../shared/components/custom-well/custom-well-clickable.component';
import { openNewTab } from '../../../../../shared/utils';

import classes from './no-project-area.module.scss';

export const LearnSectionCard = (): JSX.Element => {
    const url = useDocsUrl();

    const handleOnPress = (): void => {
        openNewTab(url);
    };

    return (
        <CustomWellClickable
            id={'learn-section-card-id'}
            height={'size-3400'}
            width={'size-3000'}
            margin={0}
            onPress={handleOnPress}
        >
            <Flex direction={'column'} height={'100%'}>
                <Image
                    alt={'Learn - annotated antelope'}
                    width={'100%'}
                    height={'13.5rem'}
                    objectFit={'cover'}
                    src={LearnSectionImage}
                    UNSAFE_className={classes.learnImage}
                />
                <Flex flex={1}>
                    <View padding={'size-250'}>
                        <Text>Learn using sample projects and step-by-step guidance</Text>
                        <Heading
                            margin={0}
                            level={4}
                            marginTop={'size-200'}
                            UNSAFE_className={classes.learnRedirectionText}
                        >
                            Watch tutorials
                        </Heading>
                    </View>
                </Flex>
            </Flex>
        </CustomWellClickable>
    );
};
