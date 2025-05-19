// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Flex } from '@adobe/react-spectrum';
import { Button } from '@geti/ui';

import { MediaItem } from '../../../../core/media/media.interface';
import { Footer } from '../../../../pages/annotator/components/footer/annotator-footer.component';
import { PreviewTitle } from '../preview-title/preview-title.component';

import classes from './media-item-annotations-preview-dialog.module.scss';

interface MediaItemAnnotationsPreviewProps {
    children: JSX.Element;
    close: () => void;
    additionalButtons?: JSX.Element[];
    title: string;
    subTitle: string;
    selectedPreviewItem?: MediaItem;
    selectedMediaItem?: MediaItem;
    datasetPreview: JSX.Element;
}

export const MediaItemAnnotationsPreviewDialog = ({
    children,
    close,
    additionalButtons,
    title,
    subTitle,
    selectedPreviewItem,
    selectedMediaItem,
    datasetPreview,
}: MediaItemAnnotationsPreviewProps): JSX.Element => {
    return (
        <DialogContainer onDismiss={close} type={'fullscreenTakeover'}>
            <Dialog onDismiss={close} UNSAFE_className={classes.previewDialog}>
                <PreviewTitle title={title} subTitle={subTitle} />

                <Content UNSAFE_className={classes.content}>
                    <Flex direction='column' height='100%' width='100%'>
                        <Flex width={'100%'} height={'100%'} UNSAFE_className={classes.previewContent}>
                            <Flex direction='column' height={'100%'} UNSAFE_className={classes.imagePreview}>
                                {children}

                                <Footer selectedItem={selectedPreviewItem ?? selectedMediaItem} />
                            </Flex>

                            <Flex UNSAFE_className={classes.datasetPreview} marginTop={{ base: 'size-600', L: '0px' }}>
                                {datasetPreview}
                            </Flex>
                        </Flex>
                    </Flex>
                </Content>

                <ButtonGroup marginBottom={'size-200'}>
                    {additionalButtons?.map((button, index) => (
                        <Fragment key={`additional-button-${index}`}>{button}</Fragment>
                    ))}
                    <Button
                        onPress={close}
                        key='close'
                        id='close-preview-modal'
                        variant='secondary'
                        aria-label='close preview modal'
                    >
                        Close
                    </Button>
                </ButtonGroup>
            </Dialog>
        </DialogContainer>
    );
};
