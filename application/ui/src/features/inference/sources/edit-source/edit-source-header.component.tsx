// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Text } from '@geti-ui/ui';
import { Back } from '@geti-ui/ui/icons';

interface EditSourceHeaderProps {
    onBack: () => void;
}

export const EditSourceHeader = ({ onBack }: EditSourceHeaderProps) => {
    const { t } = useTranslation();

    return (
        <Flex gap={'size-100'} alignItems={'center'} marginTop={'0px'}>
            <ActionButton isQuiet onPress={onBack}>
                <Back />
            </ActionButton>

            <Text>{t('inference.sources.edit.title')}</Text>
        </Flex>
    );
};
