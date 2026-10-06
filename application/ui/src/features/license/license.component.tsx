// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useId, useState } from 'react';

import { useTranslation } from '@/i18n';
import { ActionButton, Badge, Button, Checkbox, Flex, Heading, Text } from '@geti-ui/ui';
import { Checkmark, ChevronLeft, ChevronRight, DocumentIcon, LinkOut } from '@geti-ui/ui/icons';
import { clsx } from 'clsx';

import { Link } from '../../platform/components/link.component';
import { useAcceptLicense } from './api/use-accept-license.hook';
import { getLicenses } from './licenses';

import styles from './license.module.scss';

const RequirementBadge = ({ isRequired }: { isRequired: boolean }) => {
    const { t } = useTranslation();

    return (
        <Badge variant={isRequired ? 'info' : 'neutral'} UNSAFE_className={styles.badge}>
            {isRequired ? t('license.agreement.required') : t('license.agreement.optional')}
        </Badge>
    );
};

export const License = () => {
    const { t } = useTranslation();
    const titleId = useId();
    const licenses = getLicenses(t);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [agreedIds, setAgreedIds] = useState<ReadonlySet<string>>(new Set());
    const { mutate: acceptLicense, isPending: isAccepting } = useAcceptLicense();

    const current = licenses[currentIndex];
    const hasMultipleLicenses = licenses.length > 1;
    const isFirst = currentIndex === 0;
    const isLast = currentIndex === licenses.length - 1;
    const isCurrentAgreed = agreedIds.has(current.id);
    const canProceed = isCurrentAgreed || !current.isRequired;
    const firstPendingIndex = licenses.findIndex(({ id, isRequired }) => isRequired && !agreedIds.has(id));
    const areAllRequiredAgreed = firstPendingIndex === -1;
    const lastReachableIndex = areAllRequiredAgreed ? licenses.length - 1 : firstPendingIndex;

    const goToPrevious = () => setCurrentIndex((index) => Math.max(index - 1, 0));
    const goToNext = () => setCurrentIndex((index) => Math.min(index + 1, licenses.length - 1));

    const handleAgreementChange = (isSelected: boolean) => {
        setAgreedIds((previous) => {
            const next = new Set(previous);

            if (isSelected) {
                next.add(current.id);
            } else {
                next.delete(current.id);
            }

            return next;
        });
    };

    return (
        <div className={styles.licenseBackground}>
            <section className={styles.dialog} aria-labelledby={titleId}>
                <nav className={styles.sidebar} aria-label={'License steps'}>
                    <Flex alignItems={'center'} gap={'size-150'}>
                        <span className={styles.headerIcon}>
                            <DocumentIcon aria-hidden />
                        </span>
                        <Heading id={titleId} level={2} margin={0} UNSAFE_className={styles.title}>
                            {t('license.agreement.title')}
                        </Heading>
                    </Flex>
                    <Text UNSAFE_className={styles.intro}>{t('license.agreement.intro')}</Text>

                    <ol className={styles.steps}>
                        {licenses.map((license, index) => {
                            const isActive = index === currentIndex;

                            return (
                                <li key={license.id}>
                                    <button
                                        type={'button'}
                                        className={clsx(styles.step, isActive && styles.stepActive)}
                                        aria-current={isActive ? 'step' : undefined}
                                        disabled={index > lastReachableIndex}
                                        onClick={() => setCurrentIndex(index)}
                                    >
                                        <span className={styles.stepNumber}>
                                            {agreedIds.has(license.id) ? <Checkmark size={'S'} /> : index + 1}
                                        </span>
                                        <span className={styles.stepLabel}>
                                            <span>{license.name}</span>
                                            <RequirementBadge isRequired={license.isRequired} />
                                        </span>
                                        <ChevronRight className={styles.stepChevron} aria-hidden />
                                    </button>
                                </li>
                            );
                        })}
                    </ol>
                </nav>

                <div className={styles.main}>
                    <div className={styles.content}>
                        {hasMultipleLicenses && (
                            <Flex alignItems={'center'} gap={'size-50'}>
                                <ActionButton
                                    isQuiet
                                    aria-label={'Previous license'}
                                    isDisabled={isFirst}
                                    onPress={goToPrevious}
                                >
                                    <ChevronLeft />
                                </ActionButton>
                                <Text UNSAFE_className={styles.progress}>
                                    {t('license.agreement.progress', {
                                        current: currentIndex + 1,
                                        total: licenses.length,
                                    })}
                                </Text>
                            </Flex>
                        )}

                        <div aria-live={'polite'} className={styles.licenseHeader}>
                            <Heading level={3} margin={0} UNSAFE_className={styles.licenseName}>
                                {current.name}
                            </Heading>
                            <RequirementBadge isRequired={current.isRequired} />
                        </div>

                        <Text>
                            {current.isRequired
                                ? t('license.agreement.consent', { license: current.name })
                                : t('license.agreement.optionalInfo')}
                        </Text>

                        <div
                            className={styles.notice}
                            role={'region'}
                            aria-label={'License notice'}
                            // Keyboard users must be able to scroll long notices.
                            tabIndex={0}
                        >
                            <Text UNSAFE_className={styles.noticeText}>{current.notice}</Text>
                            <Link href={current.href} target={'_blank'} rel={'noopener noreferrer'}>
                                {t('license.agreement.fullLicense')}
                                <LinkOut size={'XS'} UNSAFE_className={styles.linkOut} />
                            </Link>
                        </div>

                        {current.isRequired && (
                            <Checkbox key={current.id} isSelected={isCurrentAgreed} onChange={handleAgreementChange}>
                                {t('license.agreement.agree', { license: current.name })}
                            </Checkbox>
                        )}
                    </div>

                    <Flex justifyContent={'end'} gap={'size-150'} UNSAFE_className={styles.footer}>
                        {hasMultipleLicenses && (
                            <Button variant={'secondary'} isDisabled={isFirst} onPress={goToPrevious}>
                                {t('license.agreement.previous')}
                            </Button>
                        )}
                        {isLast ? (
                            <Button
                                variant={'accent'}
                                onPress={() => acceptLicense(undefined)}
                                isPending={isAccepting}
                                isDisabled={!areAllRequiredAgreed || isAccepting}
                            >
                                {t('license.agreement.accept')}
                            </Button>
                        ) : (
                            <Button variant={'accent'} isDisabled={!canProceed} onPress={goToNext}>
                                {t('common.actions.next')}
                            </Button>
                        )}
                    </Flex>
                </div>
            </section>
        </div>
    );
};
