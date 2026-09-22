// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useEffect, useReducer, useRef } from 'react';

import { removeToast, toast } from '@/components/toast/toast.component';
import { useTranslation, type TranslateFn } from '@/i18n';
import { Button, Flex, Loading, Text } from '@geti-ui/ui';

import { UploadDetailsDialog } from '../gallery/upload-details-dialog/upload-details-dialog.component';
import { IsUploadingContext, MediaUploadDispatchContext, MediaUploadStateContext } from './media-upload-context';
import { computeSummary, INITIAL_STATE, reducer } from './media-upload-reducer';

const UPLOAD_TOAST_ID = 'upload-progress-notification';
const UPLOAD_TOAST_FONT_SIZE = 'var(--spectrum-global-dimension-font-size-75)';

// Sonner re-renders the toaster synchronously (flushSync) on every update, so refreshing the
// toast for each of a few thousand files would stall the page for no visible benefit.
const TOAST_UPDATE_INTERVAL_MS = 300;

const buildProgressDetail = (succeeded: number, failed: number, t: TranslateFn): string => {
    const parts = [
        succeeded > 0 ? t('dataset.upload.inProgressSucceededPart', { count: succeeded }) : null,
        failed > 0 ? t('dataset.upload.inProgressFailedPart', { count: failed }) : null,
    ].filter(Boolean);

    return parts.length === 0 ? '' : `(${parts.join(', ')})`;
};

const ShowDetailsButton = ({ onPress }: { onPress: () => void }) => {
    const { t } = useTranslation();

    return (
        <Button variant={'secondary'} style={'fill'} onPress={onPress}>
            {t('dataset.upload.showDetails')}
        </Button>
    );
};

const InProgressMessage = ({
    total,
    succeeded,
    failed,
}: {
    total: number;
    succeeded: number;
    failed: number;
}): ReactNode => {
    const { t } = useTranslation();
    const detail = buildProgressDetail(succeeded, failed, t);

    return (
        <Flex alignItems={'center'} gap={'size-100'} UNSAFE_style={{ fontSize: UPLOAD_TOAST_FONT_SIZE }}>
            <Loading mode={'inline'} size={'S'} />
            <Text>{`${t('dataset.upload.inProgressToast', { count: total })} ${detail}`.trim()}</Text>
        </Flex>
    );
};

const showInProgressToast = (total: number, succeeded: number, failed: number, openDialog: () => void): void => {
    toast({
        id: UPLOAD_TOAST_ID,
        type: 'neutral',
        message: <InProgressMessage total={total} succeeded={succeeded} failed={failed} />,
        actionButtons: [<ShowDetailsButton key={'show-details'} onPress={openDialog} />],
        duration: Infinity,
    });
};

const showFinalToast = (succeeded: number, failed: number, openDialog: () => void, t: TranslateFn): void => {
    let text: string;

    if (failed === 0) {
        text = t('dataset.upload.uploadedSummary', { count: succeeded });
    } else if (succeeded === 0) {
        text = t('dataset.upload.failedSummary', { count: failed });
    } else {
        text = t('dataset.upload.mixedSummary', { count: succeeded, uploaded: succeeded, failed });
    }

    toast({
        id: UPLOAD_TOAST_ID,
        type: 'neutral',
        message: <span style={{ fontSize: UPLOAD_TOAST_FONT_SIZE }}>{text}</span>,
        actionButtons: [<ShowDetailsButton key={'show-details'} onPress={openDialog} />],
        duration: 5000,
    });
};

export const MediaUploadProvider = ({ children }: { children: ReactNode }) => {
    const { t } = useTranslation();
    const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
    const lastToastUpdateRef = useRef(0);

    useEffect(() => {
        return () => removeToast(UPLOAD_TOAST_ID);
    }, []);

    useEffect(() => {
        if (state.items.length === 0) return;

        const openDialog = () => dispatch({ type: 'OPEN_DIALOG' });
        const summary = computeSummary(state.items);

        if (!state.isUploading) {
            lastToastUpdateRef.current = 0;
            showFinalToast(summary.succeeded, summary.failed, openDialog, t);

            return;
        }

        const showProgress = () => {
            lastToastUpdateRef.current = Date.now();
            showInProgressToast(summary.total, summary.succeeded, summary.failed, openDialog);
        };

        const timeoutId = setTimeout(
            showProgress,
            Math.max(0, TOAST_UPDATE_INTERVAL_MS - (Date.now() - lastToastUpdateRef.current))
        );

        return () => clearTimeout(timeoutId);
    }, [state.items, state.isUploading, t]);

    return (
        <MediaUploadDispatchContext.Provider value={dispatch}>
            <IsUploadingContext.Provider value={state.isUploading}>
                <MediaUploadStateContext.Provider value={state}>
                    {children}
                    <UploadDetailsDialog />
                </MediaUploadStateContext.Provider>
            </IsUploadingContext.Provider>
        </MediaUploadDispatchContext.Provider>
    );
};
