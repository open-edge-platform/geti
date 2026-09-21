// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useState } from 'react';

import type { Media } from '@/api/types';
import { Button, DialogContainer, Item, Key, Menu, MenuTrigger } from '@geti-ui/ui';
import { ChevronDownSmall } from '@geti-ui/ui/icons';
import { useProject } from 'hooks/api/project.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';
import { useLocation, useNavigate } from 'react-router-dom';

import { paths } from '../../../../constants/paths';
import { isImage } from '../../../../shared/media-item-utils';
import { getMediaDownloadUrl } from '../../../../shared/media-url.utils';
import { AssistantDrawer } from '../../../ai-assistant/components/assistant-drawer.component';
import type { MediaAttachmentSource } from '../../../ai-assistant/media-attachment';
import { isAssistantAvailable } from '../../../ai-assistant/platform';
import { AutoLabelDialog } from '../../auto-label/auto-label-dialog.component';
import { useAnnotatorMode } from '../../media-preview/utils';

import classes from './annotate-button.module.scss';

/** Cap on the images offered as chat attachments; videos cannot be sent. */
const MAX_ATTACHMENT_SOURCES = 25;

type AnnotateButtonProps = {
    items: Media[];
    onClick?: () => void;
};

export const AnnotateButton = ({ items, onClick }: AnnotateButtonProps) => {
    const projectId = useProjectIdentifier();
    const navigate = useNavigate();
    const { search } = useLocation();
    const [, changeMode] = useAnnotatorMode();
    const { data: project } = useProject();
    const [isAssistantOpen, setIsAssistantOpen] = useState(false);
    const [isAutoLabelOpen, setIsAutoLabelOpen] = useState(false);

    const attachmentSources = useMemo<MediaAttachmentSource[]>(
        () =>
            items
                .filter(isImage)
                .slice(0, MAX_ATTACHMENT_SOURCES)
                .map((item) => ({
                    id: item.id,
                    name: `${item.name}.${item.format}`,
                    url: getMediaDownloadUrl(projectId, item.id),
                })),
        [items, projectId]
    );

    const openChatGptAnnotator = () => {
        const image = items.find(isImage);
        if (image === undefined) return;
        changeMode('annotation');
        navigate(
            { pathname: paths.project.dataset.item.index({ projectId, datasetItemId: image.id }), search },
            { state: { annotateWithChatGpt: image.id, autoLabelDataset: true } }
        );
    };

    const annotate = (
        <Button
            margin={0}
            variant={'primary'}
            onPress={(project.task.labels ?? []).length === 0 ? () => setIsAutoLabelOpen(true) : onClick}
            isDisabled={items.length === 0}
        >
            {(project.task.labels ?? []).length === 0 ? 'Auto-Label' : 'Annotate'}
        </Button>
    );

    // The desktop bundle is shared by every operating system; the assistant is
    // part of the Windows application only.
    if (!isAssistantAvailable()) {
        return annotate;
    }

    const handleMenuAction = (option: Key) => {
        if (option === 'chatgpt') {
            openChatGptAnnotator();
        } else if (option === 'auto-label') {
            setIsAutoLabelOpen(true);
        } else if (option === 'assistant') {
            setIsAssistantOpen(true);
        }
    };

    return (
        <>
            <div className={classes.splitButton}>
                {annotate}

                <MenuTrigger align={'end'}>
                    <Button margin={0} variant={'primary'} aria-label={'More annotate options'}>
                        <ChevronDownSmall />
                    </Button>
                    <Menu onAction={handleMenuAction} disabledKeys={items.some(isImage) ? [] : ['chatgpt']}>
                        <Item key={'auto-label'}>Auto-Label</Item>
                        <Item key={'chatgpt'}>Annotate with ChatGPT</Item>
                        <Item key={'assistant'}>Ask ChatGPT about this project</Item>
                    </Menu>
                </MenuTrigger>
            </div>

            {isAssistantOpen && (
                <AssistantDrawer
                    projectId={projectId}
                    attachmentSources={attachmentSources}
                    onClose={() => setIsAssistantOpen(false)}
                />
            )}
            <DialogContainer onDismiss={() => setIsAutoLabelOpen(false)}>
                {isAutoLabelOpen && (
                    <AutoLabelDialog
                        onClose={() => setIsAutoLabelOpen(false)}
                        isChatGptAvailable={isAssistantAvailable()}
                    />
                )}
            </DialogContainer>
        </>
    );
};
