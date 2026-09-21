// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import type { Media } from '@/api/types';
import { Button, DialogContainer } from '@geti-ui/ui';
import { useProject } from 'hooks/api/project.hook';

import { AutoLabelDialog } from '../../auto-label/auto-label-dialog.component';

export type AnnotateButtonProps = {
    items: Media[];
    onClick?: () => void;
};

/**
 * Plain annotate action. The `.tauri.tsx` twin adds the "Annotate with ChatGPT"
 * entry, which needs the desktop shell to reach a model.
 */
export const AnnotateButton = ({ items, onClick }: AnnotateButtonProps) => {
    const { data: project } = useProject();
    const [isAutoLabelOpen, setIsAutoLabelOpen] = useState(false);

    return (
        <>
            <Button
                margin={0}
                variant={'primary'}
                onPress={(project.task.labels ?? []).length === 0 ? () => setIsAutoLabelOpen(true) : onClick}
                isDisabled={items.length === 0}
            >
                {(project.task.labels ?? []).length === 0 ? 'Auto-Label' : 'Annotate'}
            </Button>
            <DialogContainer onDismiss={() => setIsAutoLabelOpen(false)}>
                {isAutoLabelOpen && (
                    <AutoLabelDialog onClose={() => setIsAutoLabelOpen(false)} isChatGptAvailable={false} />
                )}
            </DialogContainer>
        </>
    );
};
