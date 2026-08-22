// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode } from 'react';

import {
    ActionButton,
    Button,
    ButtonGroup,
    Cell,
    Column,
    Content,
    Dialog,
    DialogContainer,
    DialogTrigger,
    Divider,
    Flex,
    Heading,
    Loading,
    Row,
    TableBody,
    TableHeader,
    TableView,
    Text,
    Tooltip,
    TooltipTrigger,
} from '@geti-ui/ui';
import { AcceptCircle, CrossCircle, Pending } from '@geti-ui/ui/icons';
import { useTranslation } from 'react-i18next';

import { formatBytes } from '../../../../shared/util';
import { useMediaUploadContext } from '../../providers/media-upload-provider.component';
import { computeSummary, type UploadFileItem, type UploadItemStatus } from '../../providers/media-upload-reducer';

import classes from './upload-details-dialog.module.scss';

const STATUS_LABEL_KEYS: Record<UploadItemStatus, string> = {
    queued: 'dataset.queuedStatus',
    uploading: 'dataset.statusUploading',
    uploaded: 'dataset.uploadedStatus',
    failed: 'dataset.failedStatus',
};

const StatusIcon = ({ status }: { status: UploadItemStatus }): ReactNode => {
    const { t } = useTranslation();

    switch (status) {
        case 'queued':
            return <Pending aria-label={t('dataset.queuedStatus')} size={'S'} />;
        case 'uploading':
            return <Loading mode={'inline'} size={'S'} />;
        case 'uploaded':
            return (
                <AcceptCircle
                    aria-label={t('dataset.uploadedStatus')}
                    width={16}
                    height={16}
                    style={{ fill: 'var(--brand-moss)' }}
                />
            );
        case 'failed':
            return (
                <CrossCircle
                    aria-label={t('dataset.failedStatus')}
                    width={16}
                    height={16}
                    style={{ fill: 'var(--brand-coral-cobalt)' }}
                />
            );
    }
};

const StatusCell = ({ item }: { item: UploadFileItem }) => {
    const { t } = useTranslation();
    const statusContent = (
        <Flex alignItems={'center'} gap={'size-100'}>
            <StatusIcon status={item.status} />
            <Text>{t(STATUS_LABEL_KEYS[item.status])}</Text>
        </Flex>
    );

    if (item.status === 'failed' && item.errorMessage) {
        return (
            <Flex alignItems={'center'} gap={'size-100'}>
                {statusContent}
                <DialogTrigger type={'popover'}>
                    <ActionButton
                        isQuiet
                        aria-label={t('dataset.errorDetailsAriaLabel')}
                        UNSAFE_className={classes.error}
                    >
                        {t('dataset.errorLabel')}
                    </ActionButton>
                    <Dialog>
                        <Heading>{t('dataset.uploadErrorHeading')}</Heading>
                        <Divider />
                        <Content>
                            <Text>{item.errorMessage}</Text>
                        </Content>
                    </Dialog>
                </DialogTrigger>
            </Flex>
        );
    }

    return statusContent;
};

const UploadDetailsDialogContent = ({ onClose }: { onClose: () => void }) => {
    const { state } = useMediaUploadContext();
    const { t } = useTranslation();
    const summary = computeSummary(state.items, state.isUploading);
    const items = state.items;

    const separator = t('dataset.commaSeparator');

    let subheader: string;
    if (summary.isUploading) {
        const parts = [
            t('dataset.partUploaded', { count: summary.succeeded }),
            summary.failed > 0 ? t('dataset.partFailed', { count: summary.failed }) : null,
        ]
            .filter(Boolean)
            .join(separator);

        subheader = `${t('dataset.summaryUploading', { count: summary.total })} — ${parts}`;
    } else if (summary.failed === 0) {
        subheader = t('dataset.summaryUploaded', { count: summary.succeeded });
    } else if (summary.succeeded === 0) {
        subheader = t('dataset.summaryFailed', { count: summary.failed });
    } else {
        subheader = [
            t('dataset.summaryUploaded', { count: summary.succeeded }),
            t('dataset.partFailed', { count: summary.failed }),
        ].join(separator);
    }

    return (
        <Dialog size={'L'}>
            <Heading>{t('dataset.uploadDetailsHeading')}</Heading>
            <Divider />
            <Content>
                <Flex direction={'column'} gap={'size-200'}>
                    <Text>{subheader}</Text>
                    <TableView
                        aria-label={t('dataset.uploadDetailsAriaLabel')}
                        overflowMode={'truncate'}
                        density={'compact'}
                        maxHeight={'60vh'}
                        isQuiet
                    >
                        <TableHeader>
                            <Column isRowHeader>{t('dataset.fileNameColumn')}</Column>
                            <Column width={160}>{t('dataset.statusColumn')}</Column>
                            <Column width={120} align={'end'}>
                                {t('dataset.sizeColumn')}
                            </Column>
                        </TableHeader>
                        <TableBody items={items}>
                            {(item) => (
                                <Row key={item.id}>
                                    <Cell>
                                        <TooltipTrigger>
                                            <Text>{item.name}</Text>
                                            <Tooltip>{item.name}</Tooltip>
                                        </TooltipTrigger>
                                    </Cell>
                                    <Cell>
                                        <StatusCell item={item} />
                                    </Cell>
                                    <Cell>{formatBytes(item.size)}</Cell>
                                </Row>
                            )}
                        </TableBody>
                    </TableView>
                </Flex>
            </Content>
            <ButtonGroup>
                <Button variant={'primary'} onPress={onClose}>
                    Close
                </Button>
            </ButtonGroup>
        </Dialog>
    );
};

export const UploadDetailsDialog = () => {
    const { state, dispatch } = useMediaUploadContext();
    const close = () => dispatch({ type: 'CLOSE_DIALOG' });

    return (
        <DialogContainer onDismiss={close}>
            {state.isDetailsDialogOpen && <UploadDetailsDialogContent onClose={close} />}
        </DialogContainer>
    );
};
