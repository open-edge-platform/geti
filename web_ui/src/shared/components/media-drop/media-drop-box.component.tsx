// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode, SVGProps } from 'react';

import { AriaDropZone as DropZone, Flex, Text, View, type DimensionValue, type Responsive } from '@geti/ui';
import { isFirefox } from '@react-aria/utils';
import { isEmpty, isNil } from 'lodash-es';

import { MediaUpload } from '../../../assets/images';
import { useStatus } from '../../../core/status/hooks/use-status.hook';
import { isBelowTooLowFreeDiskSpace } from '../../../core/status/hooks/utils';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { ExportImportDatasetButtons } from '../../../pages/project-details/components/project-dataset/export-dataset/export-import-dataset-buttons.component';
import { AnomalyMediaHeaderInformation } from '../../../pages/project-details/components/project-media/anomaly-media-header-information.component';
import { CANT_UPLOAD_FOLDER_FIREFOX, EMPTY_FOLDER_WARNING_MESSAGE } from '../../custom-notification-messages';
import { onDropFiles } from '../../drag-and-drop/drag-and-drop.component';
import { UploadMediaButton } from '../upload-media/upload-media-button/upload-media-button.component';
import { UploadMediaLink } from '../upload-media/upload-media-link/upload-media-link.component';

import classes from './media-drop-box.module.scss';

interface DropBoxHeaderInfo {
    header: string;
    countElements: string | undefined;
    description: string;
}

interface MediaDropBoxProps {
    DropBoxIcon?: FC<SVGProps<SVGSVGElement>>;
    dropBoxIconSize?: Responsive<DimensionValue>;
    acceptedFormats: string[];
    showUploadButton?: boolean;
    showExportImportButton?: boolean;
    isVisible?: boolean;
    onDrop: (files: File[]) => void;
    UNSAFE_className?: string;
    multiple?: boolean;
    headerInfo?: DropBoxHeaderInfo;
    onCameraSelected?: () => void;
    footerInfo?: ReactNode;
    dropBoxHeader: ReactNode;
    children?: ReactNode;
    disableUploadButton?: boolean;
}

export const MediaDropBox = ({
    DropBoxIcon = MediaUpload,
    dropBoxIconSize = 'size-3000',
    acceptedFormats,
    showUploadButton,
    showExportImportButton,
    isVisible,
    onDrop,
    onCameraSelected,
    UNSAFE_className = '',
    multiple = true,
    headerInfo,
    footerInfo,
    dropBoxHeader,
    children,
    disableUploadButton = false,
}: MediaDropBoxProps): JSX.Element => {
    const { data: status } = useStatus();
    const { addNotification } = useNotification();
    const isUploadMediaDisabled = disableUploadButton || isBelowTooLowFreeDiskSpace(status?.freeSpace ?? 0);

    const dropFiles = onDropFiles((files) => {
        if (files.some((file) => !file.type || !file.type.length) && isFirefox()) {
            addNotification({ message: CANT_UPLOAD_FOLDER_FIREFOX, type: NOTIFICATION_TYPE.INFO });

            return;
        }

        if (isEmpty(files)) {
            addNotification({ message: EMPTY_FOLDER_WARNING_MESSAGE, type: NOTIFICATION_TYPE.DEFAULT });
        } else {
            onDrop(files);
        }
    });

    return (
        <DropZone
            isDisabled={isUploadMediaDisabled}
            style={{ height: '100%', display: 'flex' }}
            onDrop={isUploadMediaDisabled ? undefined : dropFiles}
        >
            {({ isDropTarget }) => {
                const isMediaDropHidden = !(isDropTarget || isVisible);

                return (
                    <>
                        <div
                            aria-label={'Media drop box'}
                            style={{
                                cursor: isDropTarget && !isMediaDropHidden ? 'grabbing' : 'inherit',
                                display: 'flex',
                                flex: '1',
                                height: '100%',
                                width: '100%',
                            }}
                        >
                            <View isHidden={!isMediaDropHidden} width='100%' height='100%'>
                                {children}
                            </View>

                            <Flex
                                isHidden={isMediaDropHidden}
                                flex={'1 1 auto'}
                                direction={'column'}
                                UNSAFE_className={`${UNSAFE_className} ${classes.dropBoxContainer}`}
                                width='100%'
                                justifyContent={'space-between'}
                            >
                                <Flex justifyContent={isNil(headerInfo) ? 'end' : 'space-between'} alignItems={'start'}>
                                    {headerInfo && (
                                        <AnomalyMediaHeaderInformation
                                            description={headerInfo?.description ?? ''}
                                            countElements={headerInfo?.countElements ?? ''}
                                            headerText={headerInfo?.header ?? ''}
                                        />
                                    )}
                                    {(showUploadButton || showExportImportButton) && (
                                        <Flex alignItems='center' gap='size-100'>
                                            {showExportImportButton && (
                                                <ExportImportDatasetButtons hasMediaItems={false} />
                                            )}
                                            {showUploadButton && (
                                                <UploadMediaButton
                                                    id={'upload-media-button-id'}
                                                    title='Upload media'
                                                    isDisabled={isUploadMediaDisabled}
                                                    acceptedFormats={acceptedFormats}
                                                    multiple={multiple}
                                                    uploadCallback={onDrop}
                                                    ariaLabel={'upload button'}
                                                    onCameraSelected={onCameraSelected}
                                                />
                                            )}
                                        </Flex>
                                    )}
                                </Flex>

                                <Flex
                                    direction='column'
                                    width='100%'
                                    alignItems='center'
                                    justifyContent='center'
                                    isHidden={isMediaDropHidden}
                                    flexGrow={1}
                                >
                                    <Flex
                                        minHeight={'size-6000'}
                                        direction='column'
                                        width='100%'
                                        alignItems='center'
                                        marginTop={'size-500'}
                                        isHidden={isMediaDropHidden}
                                        gap={'size-150'}
                                    >
                                        <Flex alignItems={'center'} direction={'column'}>
                                            {dropBoxHeader}
                                            <Text UNSAFE_className={classes.mediaDropOr}>or</Text>
                                            <UploadMediaLink
                                                text={'browse'}
                                                multiple={multiple}
                                                uploadCallback={onDrop}
                                                id={'upload-media-action-menu'}
                                                ariaLabel={'upload link'}
                                                isDisabled={isUploadMediaDisabled}
                                            />
                                        </Flex>
                                        <View width={dropBoxIconSize} height={dropBoxIconSize}>
                                            <DropBoxIcon width={'100%'} height={'100%'} />
                                        </View>
                                        <Flex gap={'size-300'} direction={'column'} alignItems={'center'}>
                                            <Text UNSAFE_className={classes.ext}>{acceptedFormats.join(', ')}</Text>
                                            {footerInfo}
                                        </Flex>
                                    </Flex>
                                </Flex>
                            </Flex>
                        </div>
                    </>
                );
            }}
        </DropZone>
    );
};
