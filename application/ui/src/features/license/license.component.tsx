// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Content, Divider, Flex, Heading, Text, View } from '@geti-ui/ui';

import { Link } from '../../platform/components/link.component';
import { useAcceptLicense } from './api/use-accept-license.hook';

import styles from './license.module.scss';

const LICENSE_LINKS = {
    intelSimplified: {
        label: 'Intel Simplified Software License',
        // eslint-disable-next-line max-len
        href: 'https://www.intel.com/content/www/us/en/content-details/749362/intel-simplified-software-license-version-october-2022.html',
    },

    dinov2: {
        label: 'DINOv3 License',
        href: 'https://github.com/facebookresearch/dinov3/blob/main/LICENSE.md',
    },
};

export const License = () => {
    const { mutate: acceptLicense, isPending: isAccepting } = useAcceptLicense();

    return (
        <View UNSAFE_className={styles.licenseBackground} height={'100vh'}>
            <Flex justifyContent={'center'} alignItems={'center'} height={'100%'}>
                <View
                    backgroundColor={'gray-50'}
                    padding={'size-400'}
                    borderRadius={'regular'}
                    maxWidth={'size-6000'}
                    width={'100%'}
                >
                    <Heading level={2}>License Agreement</Heading>
                    <Divider marginY={'size-200'} size={'S'} />
                    <Content>
                        <Text>By installing, using, or distributing this application, you acknowledge that:</Text>
                        <ul className={styles.list}>
                            <li>You have read and understood the license terms at the links below;</li>
                            <li>Confirmed the linked terms govern the contents you seek to access and use; and</li>
                            <li>Accepted and agreed to the linked license terms.</li>
                        </ul>
                        <Flex direction={'column'} marginTop={'size-200'}>
                            <Link
                                href={LICENSE_LINKS.intelSimplified.href}
                                target={'_blank'}
                                rel={'noopener noreferrer'}
                            >
                                {LICENSE_LINKS.intelSimplified.label}
                            </Link>
                            <Link href={LICENSE_LINKS.dinov2.href} target={'_blank'} rel={'noopener noreferrer'}>
                                {LICENSE_LINKS.dinov2.label}
                            </Link>
                        </Flex>
                    </Content>
                    <Flex justifyContent={'end'} marginTop={'size-300'}>
                        <Button
                            variant={'accent'}
                            onPress={() => acceptLicense(undefined)}
                            isPending={isAccepting}
                            isDisabled={isAccepting}
                        >
                            Accept and continue
                        </Button>
                    </Flex>
                </View>
            </Flex>
        </View>
    );
};
