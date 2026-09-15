// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { Button } from '@geti-ui/ui';

export type AnnotateButtonProps = {
    items: Media[];
    onClick?: () => void;
};

/**
 * Plain annotate action. The `.tauri.tsx` twin adds the "Annotate with ChatGPT"
 * entry, which needs the desktop shell to reach a model.
 */
export const AnnotateButton = ({ items, onClick }: AnnotateButtonProps) => {
    return (
        <Button margin={0} variant={'primary'} onPress={onClick} isDisabled={items.length === 0}>
            Annotate
        </Button>
    );
};
