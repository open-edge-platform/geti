// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Dispatch, SetStateAction, useRef } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';
import { DimensionValue } from '@react-types/shared/src/dna';
import { Responsive } from '@react-types/shared/src/style';
import { Link } from 'react-router-dom';
import { useMediaQuery } from 'usehooks-ts';

import { DatasetImport as DatasetImportIcon } from '../../../assets/icons';
import { IMPORT_DATASET_LEARN_MORE } from '../../../core/const';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { isExtraLargeSizeQuery } from '../../../theme/queries';
import { DropZone, onDropFiles } from '../../drag-and-drop/drag-and-drop.component';
import { onValidFileList } from '../../utils';
import { Button } from '../button/button.component';

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
