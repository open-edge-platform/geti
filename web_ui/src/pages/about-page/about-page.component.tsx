// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, Heading, Link as SpectrumLink, Text, View } from '@geti/ui';
import { Link } from 'react-router-dom';

import { COOKIES_NOTICE, PRIVACY_NOTICE, TERMS_OF_USE_GETI, TERMS_OF_USE_INTEL } from '../../core/const';
import { usePlatformUtils } from '../../core/platform-utils/hooks/use-platform-utils.hook';
import { useIsSaasEnv } from '../../hooks/use-is-saas-env/use-is-saas-env.hook';
import { LicenseModal } from '../../shared/components/license-modal/license-modal.component';
import { PageLayout } from '../../shared/components/page-layout/page-layout.component';
import { QuietActionButton } from '../../shared/components/quiet-button/quiet-action-button.component';

import classes from './about-page.module.scss';

const AboutPage = (): JSX.Element => {
    const { useProductInfo } = usePlatformUtils();
    const { isPending, data } = useProductInfo();
    const isSaasEnvironment = useIsSaasEnv();

    const [forceOpenLicenseModal, setForceOpenLicenseModal] = useState(false);

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

                    <>
                        <Heading level={3} UNSAFE_className={classes.heading}>
                            Geti
                        </Heading>
                        {isSaasEnvironment ? (
                            <SpectrumLink UNSAFE_className={classes.link}>
                                <a href={TERMS_OF_USE_GETI} target={'_blank'} rel={'noopener noreferrer'}>
                                    Terms of use & Privacy
                                </a>
                            </SpectrumLink>
                        ) : (
                            <QuietActionButton
                                UNSAFE_className={classes.licenceButton}
                                onPress={() => setForceOpenLicenseModal(true)}
                            >
                                License
                            </QuietActionButton>
                        )}
                    </>

                    {!isSaasEnvironment && data?.buildVersion && (
                        <Text marginTop={'size-400'} id={'build-version-id'}>
                            Build: {isPending ? '-- ' : data?.buildVersion}
                        </Text>
                    )}

                    {!isSaasEnvironment && (
                        <LicenseModal
                            forceOpen={forceOpenLicenseModal}
                            onClose={() => setForceOpenLicenseModal(false)}
                        />
                    )}
                </Flex>
            </>
        </PageLayout>
    );
};

export default AboutPage;
