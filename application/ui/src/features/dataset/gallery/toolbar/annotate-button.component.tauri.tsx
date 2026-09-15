// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useMemo, useState } from 'react';

import type { Media } from '@/api/types';
import { Button, Item, Key, Menu, MenuTrigger } from '@geti-ui/ui';
import { ChevronDownSmall } from '@geti-ui/ui/icons';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { isImage } from '../../../../shared/media-item-utils';
import { getMediaDownloadUrl } from '../../../../shared/media-url.utils';
import { AssistantDrawer } from '../../../ai-assistant/components/assistant-drawer.component';
import type { MediaAttachmentSource } from '../../../ai-assistant/media-attachment';
import { isAssistantAvailable } from '../../../ai-assistant/platform';

import classes from './annotate-button.module.scss';

/** Cap on the images offered as chat attachments; videos cannot be sent. */
const MAX_ATTACHMENT_SOURCES = 25;

type AnnotateButtonProps = {
    items: Media[];
    onClick?: () => void;
};

export const AnnotateButton = ({ items, onClick }: AnnotateButtonProps) => {
    const projectId = useProjectIdentifier();
    const [isAssistantOpen, setIsAssistantOpen] = useState(false);

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

    const annotate = (
        <Button margin={0} variant={'primary'} onPress={onClick} isDisabled={items.length === 0}>
            Annotate
        </Button>
    );

    // The desktop bundle is shared by every operating system; the assistant is
    // part of the Windows application only.
    if (!isAssistantAvailable()) {
        return annotate;
    }

    const handleMenuAction = (option: Key) => {
        if (option === 'chatgpt') {
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
                    <Menu onAction={handleMenuAction}>
                        <Item key={'chatgpt'}>Annotate with ChatGPT</Item>
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
        </>
    );
};
