// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Suspense } from 'react';

import {
    ActionButton,
    Button,
    ButtonGroup,
    Content,
    Dialog,
    DialogTrigger,
    Divider,
    Heading,
    Loading,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
import { GraphChart } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { DatasetStatisticsContent } from './dataset-statistics-content.component';

export const DatasetStatistics = () => {
    const { t } = useTranslation();

    return (
        <DialogTrigger>
            <TooltipTrigger>
                <ActionButton isQuiet aria-label={t('dataset.statisticsAriaLabel')}>
                    <GraphChart />
                </ActionButton>
                <Tooltip>{t('dataset.statisticsTooltip')}</Tooltip>
            </TooltipTrigger>
            {(close) => (
                <Dialog width={{ base: '90vw', L: '70vw' }}>
                    <Heading>{t('dataset.statisticsHeading')}</Heading>
                    <Divider />
                    <Content>
                        <Suspense fallback={<Loading size='M' />}>
                            <DatasetStatisticsContent />
                        </Suspense>
                    </Content>
                    <ButtonGroup>
                        <Button variant='secondary' onPress={close}>
                            {t('dataset.closeButton')}
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogTrigger>
    );
};
