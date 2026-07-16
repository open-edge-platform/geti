// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Flex, Heading } from '@geti-ui/ui';

import { ReactComponent as EmptyDatasetImage } from '../../../assets/empty-dataset.svg';
import { useImportDatasetDialogState } from '../providers/export-import-dataset-dialog-provider.component';
import { MediaUpload } from './toolbar/media-upload.component';

const ImportDatasetButton = () => {
    const { datasetImportDialogState } = useImportDatasetDialogState();

    return (
        <Button variant={'secondary'} onPress={() => datasetImportDialogState.open()}>
            Import dataset
        </Button>
    );
};

type EmptyDatasetProps = {
    hasActiveFilter: boolean;
};
export const EmptyDataset = ({ hasActiveFilter }: EmptyDatasetProps) => {
    return (
        <Flex direction={'column'} gap={'size-200'} alignItems={'center'} justifyContent={'center'} height={'100%'}>
            <EmptyDatasetImage />
            <Heading level={2} UNSAFE_style={{ textAlign: 'center' }}>
                {hasActiveFilter ? (
                    <>
                        No media items match your filter.
                        <br />
                        Remove or select a new filter.
                    </>
                ) : (
                    <>
                        Your dataset is empty.
                        <br />
                        Upload your first media item to get started.
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
