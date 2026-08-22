// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Flex, Heading } from '@geti-ui/ui';
import { useTranslation } from 'react-i18next';

import { ReactComponent as EmptyDatasetImage } from '../../../assets/empty-dataset.svg';
import { useImportDatasetDialogState } from '../providers/export-import-dataset-dialog-provider.component';
import { MediaUpload } from './toolbar/media-upload.component';

const ImportDatasetButton = () => {
    const { datasetImportDialogState } = useImportDatasetDialogState();

    const { t } = useTranslation();

    return (
        <Button variant={'secondary'} onPress={() => datasetImportDialogState.open()}>
            {t('dataset.importDatasetButton')}
        </Button>
    );
};

type EmptyDatasetProps = {
    hasActiveFilter: boolean;
};
export const EmptyDataset = ({ hasActiveFilter }: EmptyDatasetProps) => {
    const { t } = useTranslation();

    return (
        <Flex direction={'column'} gap={'size-200'} alignItems={'center'} justifyContent={'center'} height={'100%'}>
            <EmptyDatasetImage />
            <Heading level={2} UNSAFE_style={{ textAlign: 'center' }}>
                {hasActiveFilter ? (
                    <>
                        {t('dataset.emptyWithFilterLine1')}
                        <br />
                        {t('dataset.emptyWithFilterLine2')}
                    </>
                ) : (
                    <>
                        {t('dataset.emptyLine1')}
                        <br />
                        {t('dataset.emptyLine2')}
                    </>
                )}
            </Heading>
            {!hasActiveFilter && (
                <Flex gap={'size-100'}>
                    <MediaUpload />
                    <ImportDatasetButton />
                </Flex>
            )}
        </Flex>
    );
};
