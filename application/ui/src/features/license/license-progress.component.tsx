// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Text } from '@geti-ui/ui';
import { ChevronLeft } from '@geti-ui/ui/icons';

type LicenseProgressProps = {
    current: number;
    total: number;
    isFirst: boolean;
    onPrevious: () => void;
};

export const LicenseProgress = ({ current, total, isFirst, onPrevious }: LicenseProgressProps) => {
    const { t } = useTranslation();

    return (
        <Flex alignItems={'center'} gap={'size-50'}>
            <ActionButton isQuiet aria-label={'Previous license'} isDisabled={isFirst} onPress={onPrevious}>
                <ChevronLeft />
            </ActionButton>
            <Text>{t('license.agreement.progress', { current, total })}</Text>
        </Flex>
    );
};
