// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction, useRef } from 'react';

import { Button, Flex, Text, View, type DimensionValue, type Responsive } from '@geti/ui';
import { DatasetImport as DatasetImportIcon } from '@geti/ui/icons';
import { Link } from 'react-router-dom';
import { useMediaQuery } from 'usehooks-ts';

import { isExtraLargeSizeQuery } from '../../../../packages/ui/theme/queries';
import { IMPORT_DATASET_LEARN_MORE } from '../../../core/const';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { DropZone, onDropFiles } from '../../drag-and-drop/drag-and-drop.component';
import { onValidFileList } from '../../utils';

import classes from './dataset-import-dnd.module.scss';

const FILE_FORMAT_ERROR_MESSAGE = 'Only zip files are allowed for upload';

interface DatasetImportDndProps {
    setUploadItem: (file: File) => string | undefined;
    setActiveUploadId: Dispatch<SetStateAction<string | undefined>>;
    paddingX?: Responsive<DimensionValue> | number;
    paddingY?: Responsive<DimensionValue> | number;
    background?: boolean;
    isAnomaly?: boolean;
}

export const DatasetImportDnd = ({
    setUploadItem,
    setActiveUploadId,
    background = true,
    isAnomaly = false,
    paddingX = 0,
    paddingY = 0,
}: DatasetImportDndProps): JSX.Element => {
    const { addNotification } = useNotification();
    const fileInputRef = useRef<HTMLInputElement>({} as HTMLInputElement);
    const isExtraLarge = useMediaQuery(isExtraLargeSizeQuery);

    const onProcessUploadFile = onValidFileList(([file]: File[]) => {
        try {
            setActiveUploadId(setUploadItem(file));
        } catch (_error: unknown) {
            addNotification({ message: FILE_FORMAT_ERROR_MESSAGE, type: NOTIFICATION_TYPE.ERROR });
        } finally {
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    });

    const dropFiles = onDropFiles(onProcessUploadFile);

    return (
        <DropZone
            onDrop={dropFiles}
            background={background}
            id={'dataset-import-dnd'}
            aria-label={'dataset-import-dnd'}
            height={'100%'}
        >
            <View height='100%' paddingX={paddingX} paddingY={paddingY}>
                <Flex height='100%' direction='column' alignItems='center' justifyContent='center' gap='size-250'>
                    <View>
                        <DatasetImportIcon height={!isExtraLarge ? 64 : 124} width={!isExtraLarge ? 64 : 124} />
                    </View>
                    <View>
                        <Flex direction='column' alignItems='center' gap='size-200'>
                            <Text id='dataset-import-dnd-action-description'>Drop the dataset .zip file here</Text>
                            <Button
                                id='dataset-import-dnd-upload-button'
                                variant='accent'
                                onPress={() => fileInputRef.current.click()}
                            >
                                Upload
                            </Button>
                            <input
                                type='file'
                                hidden
                                id={'upload-dataset-file-id'}
                                ref={fileInputRef}
                                onChange={({ target }) => onProcessUploadFile(target.files)}
                                onClick={() => (fileInputRef.current.value = '')}
                                style={{ pointerEvents: 'all' }}
                                accept='.zip'
                            />
                            <Text id='dataset-import-dnd-available-formats' UNSAFE_className={classes.extensions}>
                                {`(${!isAnomaly ? 'COCO, YOLO, VOC, ' : ''}Datumaro) .zip`}
                            </Text>
                        </Flex>
                        <Flex justifyContent='center'>
                            <Link
                                id='dataset-import-dnd-available-formats-docs'
                                to={IMPORT_DATASET_LEARN_MORE}
                                target={'_blank'}
                                rel={'noopener noreferrer'}
                                className={classes.learnMore}
                            >
                                Learn more...
                            </Link>
                        </Flex>
                    </View>
                </Flex>
            </View>
        </DropZone>
    );
};
