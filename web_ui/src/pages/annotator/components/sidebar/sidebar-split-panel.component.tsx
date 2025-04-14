// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { View } from '@adobe/react-spectrum';
import { Allotment } from 'allotment';

import { SelectedMediaItem } from '../../providers/selected-media-item-provider/selected-media-item.interface';
import { AnnotationListAccordion } from './annotations/annotation-list-accordion.component';
import { AnnotationListCounting } from './annotations/annotation-list-counting.component';
import { DatasetAccordion } from './dataset/dataset-accordion.component';
import { SidebarCommonProps } from './sidebar.interface';

import 'allotment/dist/style.css';

/*
    Outer pane = Top list section + Bottom dataset section
    Inner pane = Within the outer pane, holds all the accordions and lists

    * Panes (inner and outer) have different minHeights depending on how much space needs to be allocated
    * If we only render 2 elements, we only need one split pane
    * If we render more than 3 elements, we need 2 split panes, and to adjust their height to split space equally

    * On annotation mode we can:
        * Show only dataset (no splitpane)
        * Show only annotation list (normal splitpane, list + dataset)
        * Show only counting list (normal splitpane, counting + dataset)
        * Show both annotation list and counting list (outer splitpane and inner splitpane with annotation/counting)
    
    * On prediction mode we can:
        * Show counting list (outer splitpane and inner splitpane with counting/prediction)
        * Show only prediction list (normal splitpane, list + dataset)
*/

interface SidebarSplitPanelProps extends SidebarCommonProps {
    selectedMediaItem: SelectedMediaItem | undefined;
}

export const SidebarSplitPanel = ({
    showDatasetPanel,
    selectedMediaItem,
    showCountingPanel,
    showAnnotationPanel,
    annotationToolContext,
    setDatasetViewMode,
    datasetViewMode,
}: SidebarSplitPanelProps) => {
    return (
        <View
            height='100%'
            width='size-4600'
            position='relative'
            backgroundColor='gray-200'
            data-testid='sidebar-split-panel'
        >
            <Allotment vertical>
                {selectedMediaItem !== undefined && showCountingPanel && (
                    <Allotment.Pane snap>
                        <AnnotationListCounting annotationToolContext={annotationToolContext} />
                    </Allotment.Pane>
                )}

                {selectedMediaItem !== undefined && showAnnotationPanel && <AnnotationListAccordion />}

                {showDatasetPanel && (
                    <Allotment.Pane snap>
                        <DatasetAccordion viewMode={datasetViewMode} setViewMode={setDatasetViewMode} />
                    </Allotment.Pane>
                )}
            </Allotment>
        </View>
    );
};
