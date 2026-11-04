// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';
import { ActionButton, Flex, Text } from '@geti-ui/ui';
import { Back } from '@geti-ui/ui/icons';

interface EditSinkHeaderProps {
    onBack: () => void;
}

export const EditSinkHeader = ({ onBack }: EditSinkHeaderProps) => {
    const { t } = useTranslation();

    return (
        <Flex gap={'size-100'} alignItems={'center'} marginTop={0}>
            <ActionButton isQuiet onPress={onBack}>
                <Back />
            </ActionButton>

            <Text>{t('inference.sinks.edit.title')}</Text>
        </Flex>
    );
};
