// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ChangeEvent, useRef } from 'react';

import { Button, Flex, Text, View } from '@geti/ui';
import { DatasetImport as DatasetImportIcon } from '@geti/ui/icons';
import { Link } from 'react-router-dom';
import { useMediaQuery } from 'usehooks-ts';

import { ImportOptions } from '../../core/projects/services/project-service.interface';
import { useDocsUrl } from '../../hooks/use-docs-url/use-docs-url.hook';
import { NOTIFICATION_TYPE } from '../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../notification/notification.component';
import { mediaExtensionHandler } from '../../providers/media-upload-provider/media-upload.validator';
import { useProjectsImportProvider } from '../../providers/projects-import-provider/projects-import-provider.component';
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
    const projectImportDocsUrl = `${docsUrl}docs/user-guide/geti-fundamentals/project-management/project-export-import`;

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
