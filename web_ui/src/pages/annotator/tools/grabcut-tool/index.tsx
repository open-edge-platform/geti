// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QuickSelection } from '@geti/ui/icons';

import QuickSelectionImg from '../../../../assets/primary-tools/quick_selection.webp';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { ToolLabel, ToolType } from '../../core/annotation-tool-context.interface';
import { ToolProps } from '../tools.interface';
import { toolTypeToLabelMapping } from '../utils';
import { GrabcutStateProvider } from './grabcut-state-provider.component';
import { GrabcutTool as Tool } from './grabcut-tool.component';
import { SecondaryToolbar } from './secondary-toolbar.component';

export const GrabcutTool: ToolProps = {
    Tool,
    type: ToolType.GrabcutTool,
    label: ToolLabel.GrabcutTool,
    StateProvider: GrabcutStateProvider,
    supportedDomains: [DOMAIN.SEGMENTATION, DOMAIN.SEGMENTATION_INSTANCE, DOMAIN.ANOMALY_SEGMENTATION],
    tooltip: {
        img: QuickSelectionImg,
        url: 'docs/user-guide/geti-fundamentals/annotations/annotation-tools#object-selection-tool',
        title: toolTypeToLabelMapping[ToolType.GrabcutTool],
        description: `Simply draw a rectangle around the object and Intel® Geti™ will fit a 
            polygon to the shape of the object.`,
    },
    Icon: () => <QuickSelection />,
    SecondaryToolbar: ({ annotationToolContext }) => <SecondaryToolbar annotationToolContext={annotationToolContext} />,
};
