// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { getMediaId } from '../../../media/utils';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { ToolAnnotationContextProps } from '../../tools/tools.interface';
import useActiveTool from '../../tools/use-active-tool';
import { useSelectedMediaItem } from '../selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../task-provider/task-provider.component';

interface ActiveToolProviderProps extends ToolAnnotationContextProps {
    children: ReactNode;
}

export const ActiveToolProvider = ({ children, annotationToolContext }: ActiveToolProviderProps): JSX.Element => {
    const tool = useActiveTool(annotationToolContext);
    const { selectedTask } = useTask();
    const { selectedMediaItem } = useSelectedMediaItem();
    const domain = selectedTask?.domain ?? 'all';
    const mediaId = selectedMediaItem ? getMediaId(selectedMediaItem) : '';

    const StateProvider = tool?.StateProvider;

    if (tool?.type === ToolType.SegmentAnythingTool) {
        return StateProvider ? <StateProvider>{children}</StateProvider> : <></>;
    }

    return StateProvider ? <StateProvider key={`${mediaId}-${domain}`}>{children}</StateProvider> : <>{children}</>;
};
