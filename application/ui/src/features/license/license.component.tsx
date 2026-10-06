// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { Flex, Grid, View } from '@geti-ui/ui';

import { useAcceptLicense } from './api/use-accept-license.hook';
import { LicenseDetails } from './license-details.component';
import { LicenseFooter } from './license-footer.component';
import { LicenseProgress } from './license-progress.component';
import { LicenseSteps } from './license-steps.component';
import { getLicenses } from './licenses';
import { useLicenseSteps } from './use-license-steps.hook';

import styles from './license.module.scss';

export const License = () => {
    const { t } = useTranslation();
    const licenses = getLicenses(t);
    const steps = useLicenseSteps(licenses);
    const { mutate: acceptLicense, isPending: isAccepting } = useAcceptLicense();
    const hasMultipleLicenses = licenses.length > 1;

    return (
        <View height={'100vh'} padding={'size-300'} UNSAFE_className={styles.licenseBackground}>
            <Flex justifyContent={'center'} alignItems={'center'} height={'100%'}>
                <View
                    backgroundColor={'gray-50'}
                    borderRadius={'medium'}
                    overflow={'hidden'}
                    width={'100%'}
                    maxWidth={'1000px'}
                    height={'100%'}
                    maxHeight={'660px'}
                    UNSAFE_className={styles.dialog}
                >
                    <Grid columns={['minmax(240px, 30%)', '1fr']} height={'100%'}>
                        <LicenseSteps
                            licenses={licenses}
                            currentIndex={steps.currentIndex}
                            agreedIds={steps.agreedIds}
                            lastReachableIndex={steps.lastReachableIndex}
                            onSelect={steps.goTo}
                        />

                        <Flex direction={'column'} minWidth={0} minHeight={0}>
                            <View flex padding={'size-300'} overflow={'auto'} minHeight={0}>
                                <Flex direction={'column'} gap={'size-200'} height={'100%'}>
                                    {hasMultipleLicenses && (
                                        <LicenseProgress
                                            current={steps.currentIndex + 1}
                                            total={licenses.length}
                                            isFirst={steps.isFirst}
                                            onPrevious={steps.goToPrevious}
                                        />
                                    )}
                                    <LicenseDetails
                                        license={steps.current}
                                        isAgreed={steps.isCurrentAgreed}
                                        onAgreedChange={steps.setCurrentAgreed}
                                    />
                                </Flex>
                            </View>

                            <LicenseFooter
                                showPrevious={hasMultipleLicenses}
                                isFirst={steps.isFirst}
                                isLast={steps.isLast}
                                canProceed={steps.canProceed}
                                canAccept={steps.areAllRequiredAgreed}
                                isAccepting={isAccepting}
                                onPrevious={steps.goToPrevious}
                                onNext={steps.goToNext}
                                onAccept={() => acceptLicense(undefined)}
                            />
                        </Flex>
                    </Grid>
                </View>
            </Flex>
        </View>
    );
};
