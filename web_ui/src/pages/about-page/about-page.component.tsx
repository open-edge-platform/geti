// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Heading, Link as SpectrumLink, Text, View } from '@adobe/react-spectrum';
import { Link } from 'react-router-dom';

import { COOKIES_NOTICE, PRIVACY_NOTICE, TERMS_OF_USE_GETI, TERMS_OF_USE_INTEL } from '../../core/const';
import { usePlatformUtils } from '../../core/platform-utils/hooks/use-platform-utils.hook';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { PageLayout } from '../../shared/components/page-layout/page-layout.component';

import classes from './about-page.module.scss';

const AboutPage = (): JSX.Element => {
    const { useProductInfo } = usePlatformUtils();
    const { isPending, data } = useProductInfo();
    const isSaasEnvironment = useIsSaasEnv();

    return (
        <PageLayout breadcrumbs={[{ id: 'about-id', breadcrumb: 'About' }]}>
            <>
                <View>
                    <Text UNSAFE_className={classes.productTitle} id={'product-version-id'}>
                        Intel® Geti™ {!isSaasEnvironment && `- ${isPending ? ' -- --' : data?.productVersion}`}
                    </Text>
                </View>
                <Text UNSAFE_className={classes.productDescription} marginY={'size-250'}>
                    The Intel® Geti™ platform enables enterprise teams to rapidly build Computer Vision AI models.
                    Through an intuitive graphical interface, users add image or video data, make annotations, train,
                    retrain, export, and optimize AI models for deployment. Equipped with state-of-the-art technology
                    such as active learning, task chaining, and smart annotations, the Intel® Geti™ platform reduces
                    labor-intensive tasks, enables collaborative model development, and speeds up model creation.
                </Text>
                <Flex direction={'column'} UNSAFE_className={classes.legalInformation}>
                    <Heading level={3}>©{new Date().getFullYear()} Intel Corporation</Heading>
                    <SpectrumLink UNSAFE_className={classes.link}>
                        <Link to={TERMS_OF_USE_INTEL} target={'_blank'} rel={'noopener noreferrer'}>
                            Terms of use
                        </Link>
                    </SpectrumLink>
                    <SpectrumLink UNSAFE_className={classes.link}>
                        <Link to={COOKIES_NOTICE} target={'_blank'} rel={'noopener noreferrer'}>
                            Cookies
                        </Link>
                    </SpectrumLink>
                    <SpectrumLink UNSAFE_className={classes.link}>
                        <Link to={PRIVACY_NOTICE} target={'_blank'} rel={'noopener noreferrer'}>
                            Privacy
                        </Link>
                    </SpectrumLink>

                    {isSaasEnvironment && (
                        <>
                            <Heading level={3} UNSAFE_className={classes.heading}>
                                Geti
                            </Heading>
                            <SpectrumLink UNSAFE_className={classes.link}>
                                <a href={TERMS_OF_USE_GETI} target={'_blank'} rel={'noopener noreferrer'}>
                                    Terms of use & Privacy
                                </a>
                            </SpectrumLink>
                        </>
                    )}

                    {!isSaasEnvironment && data?.buildVersion && (
                        <Text marginTop={'size-400'} id={'build-version-id'}>
                            Build: {isPending ? '-- ' : data?.buildVersion}
                        </Text>
                    )}
                </Flex>
            </>
        </PageLayout>
    );
};

export default AboutPage;
