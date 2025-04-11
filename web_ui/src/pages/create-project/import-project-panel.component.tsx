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

import { ChangeEvent, useRef } from 'react';

import { Flex, Text, View } from '@adobe/react-spectrum';
import { Link } from 'react-router-dom';
import { useMediaQuery } from 'usehooks-ts';

import { DatasetImport as DatasetImportIcon } from '../../assets/icons';
import { ImportOptions } from '../../core/projects/services/project-service.interface';
import { useDocsUrl } from '../../hooks/use-docs-url/use-docs-url.hook';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { mediaExtensionHandler } from '../../providers/media-upload-provider/media-upload.validator';
import { useProjectsImportProvider } from '../../providers/projects-import-provider/projects-import-provider.component';
import { Button } from '../../shared/components/button/button.component';
import { DropZone, onDropFiles } from '../../shared/drag-and-drop/drag-and-drop.component';
import { isValidFileExtension } from '../../shared/media-utils';
import { isExtraLargeSizeQuery } from '../../theme/queries';

import classes from './import-project-panel.module.scss';

const VALID_EXTENSIONS = ['zip'];

export const ProjectImportPanel = ({
    options,
    onImportProject,
}: {
    options: ImportOptions;
    onImportProject: () => void;
}): JSX.Element => {
    const { addNotification } = useNotification();
    const { importProject } = useProjectsImportProvider();
    const docsUrl = useDocsUrl();

    const fileInputRef = useRef<HTMLInputElement>({} as HTMLInputElement);
    const isExtraLarge = useMediaQuery(isExtraLargeSizeQuery);
    const projectImportDocsUrl = `${docsUrl}/guide/project-management/project-management.html#export-import-project'`;

    const handleDropProject = (file?: File) => {
        if (file && !isValidFileExtension(file, VALID_EXTENSIONS)) {
            addNotification({ message: 'Invalid file extension, please try again', type: NOTIFICATION_TYPE.ERROR });
            return;
        }

        importProject(file as File, options);
        onImportProject();
    };

    const onFileInputChange = (event: ChangeEvent<HTMLInputElement>): void => {
        const file = event?.target.files?.[0];

        handleDropProject(file);

        event.target.value = '';
    };

    const dropFiles = onDropFiles((files) => {
        handleDropProject(files[0]);
    });

    return (
        <DropZone id='project-import-dnd' onDrop={dropFiles} aria-label='project-import-dnd' height={'100%'}>
            <View height='100%'>
                <Flex height='100%' direction='column' alignItems='center' justifyContent='center' gap='size-250'>
                    <View>
                        <DatasetImportIcon height={!isExtraLarge ? 64 : 124} width={!isExtraLarge ? 64 : 124} />
                    </View>
                    <View>
                        <Flex direction='column' alignItems='center' gap='size-200'>
                            <Text id='project-import-dnd-action-description'>Drop the project .zip file here</Text>
                            <Button
                                id='project-import-dnd-upload-button'
                                variant='accent'
                                onPress={() => fileInputRef.current.click()}
                            >
                                Upload
                            </Button>
                            <input
                                hidden
                                type='file'
                                multiple={false}
                                ref={fileInputRef}
                                id={'upload-project-file-id'}
                                accept={mediaExtensionHandler(['zip'])}
                                onChange={onFileInputChange}
                                aria-label='upload-media-input'
                                style={{ pointerEvents: 'all' }}
                            />
                            <Link
                                to={projectImportDocsUrl}
                                target={'_blank'}
                                rel={'noopener noreferrer'}
                                className={classes.learnMore}
                            >
                                Learn more
                            </Link>
                        </Flex>
                    </View>
                </Flex>
            </View>
        </DropZone>
    );
};
