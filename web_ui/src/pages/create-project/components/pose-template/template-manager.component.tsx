// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ReactNode, useEffect, useRef, useState } from 'react';

import { DimensionValue, Flex, Grid } from '@adobe/react-spectrum';
import { Responsive } from '@react-types/shared';
import isEmpty from 'lodash/isEmpty';

import { Delete } from '../../../../assets/icons';
import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { ButtonWithSpectrumTooltip } from '../../../../shared/components/button-with-tooltip/button-with-tooltip.component';
import { HoveredProvider } from '../../../annotator/providers/hovered-provider/hovered-provider.component';
import { SelectedProvider } from '../../../annotator/providers/selected-provider/selected-provider.component';
import { SyncZoomState } from '../../../annotator/zoom/sync-zoom-state.component';
import { ZoomProvider } from '../../../annotator/zoom/zoom-provider.component';
import { TransformZoom } from '../../../shared/zoom/transform-zoom.component';
import { CanvasTemplate } from './canvas/canvas-template.component';
import { EmptyPointMessage } from './empty-point-message.component';
import { useUndoRedoWithCallback } from './hooks/use-undo-redo-with-callback.hook';
import { LoadFileButton } from './sample-image/load-file-button.component';
import { SampleImage } from './sample-image/sample-image.component';
import { TemplateFooter } from './template-footer.component';
import { TemplatePrimaryToolbar } from './template-primary-toolbar/template-primary-toolbar.component';
import { TemplateSecondaryToolbar } from './template-secondary-toolbar/template-secondary-toolbar.component';
import { Templates } from './templates/templates.component';
import { createRoi, denormalizePoint, TemplateState, TemplateStateWithHistory } from './util';

export interface TemplateManagerProps {
    gap?: Responsive<DimensionValue>;
    children: ReactNode;
    isAddPointEnabled?: boolean;
    isTemplatesVisible?: boolean;
    isLabelOptionsEnabled?: boolean;
    initialNormalizedState?: TemplateState;
    onTemplateChange: (state: TemplateState & { roi: RegionOfInterest }) => void;
}

const GRID_AREAS = ['primaryToolbar secondaryToolbar', 'primaryToolbar content', 'primaryToolbar  footer'];
const GRID_COLUMNS = ['size-600', '1fr'];
const GRID_ROWS = ['size-600', 'auto', 'size-400'];
const initialState: TemplateState = { edges: [], points: [] };

export const EMPTY_POINT_MESSAGE = 'Click in an empty space to place a new node';

export const TemplateManager = ({
    gap,
    children,
    isAddPointEnabled = true,
    isTemplatesVisible = true,
    isLabelOptionsEnabled = true,
    initialNormalizedState = initialState,
    onTemplateChange,
}: TemplateManagerProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [roi, setRoi] = useState(createRoi());
    const [sampleImg, setSampleImg] = useState<string | undefined>();

    const [state, setState, undoRedoActions] = useUndoRedoWithCallback(initialState, (newState) => {
        onTemplateChange({ ...newState, roi });
    });

    useEffect(() => {
        const newRoi = createRoi(containerRef.current?.clientWidth, containerRef.current?.clientHeight);

        setRoi(newRoi);

        undoRedoActions.reset({
            ...initialNormalizedState,
            points: initialNormalizedState.points.map((point) => denormalizePoint(point, newRoi)),
        });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const hasEmptyPoints = isEmpty(state.points);
    const isEmptyPointVisible = hasEmptyPoints;

    const handleStateUpdate = ({ points, edges, skipHistory }: TemplateStateWithHistory) => {
        setState({ points, edges }, skipHistory);

        skipHistory == false && onTemplateChange({ points, edges, roi });
    };

    return (
        <ZoomProvider>
            <SelectedProvider>
                <HoveredProvider>
                    <Flex direction={'column'} height={'100%'} gap={gap}>
                        <Flex marginBottom={'size-150'} gap={'size-100'}>
                            {isTemplatesVisible && (
                                <Templates
                                    roi={roi}
                                    onAction={(template) => {
                                        handleStateUpdate({ ...template, skipHistory: false });
                                    }}
                                />
                            )}

                            <LoadFileButton onFileLoaded={setSampleImg} />
                            {sampleImg && (
                                <ButtonWithSpectrumTooltip
                                    isQuiet
                                    isClickable
                                    tooltip={'Remove sample image'}
                                    aria-label='sample image'
                                    onPress={() => setSampleImg(undefined)}
                                >
                                    <Delete />
                                </ButtonWithSpectrumTooltip>
                            )}
                        </Flex>

                        <Grid
                            areas={GRID_AREAS}
                            columns={GRID_COLUMNS}
                            rows={GRID_ROWS}
                            gap={'size-10'}
                            height={'100%'}
                            UNSAFE_style={{
                                border: '1px solid var(--spectrum-global-color-gray-50)',
                                background: 'var(--spectrum-global-color-gray-50)',
                            }}
                        >
                            <TemplatePrimaryToolbar
                                isHotKeysVisible={isAddPointEnabled}
                                undoRedoActions={undoRedoActions}
                            />

                            <TemplateSecondaryToolbar
                                state={state}
                                onStateUpdate={handleStateUpdate}
                                isDeleteNodeEnabled={isLabelOptionsEnabled}
                            />

                            <SyncZoomState />
                            <TransformZoom>
                                <div
                                    ref={containerRef}
                                    onContextMenu={(event) => event.preventDefault()}
                                    style={{ width: '100%', overflow: 'hidden', gridArea: 'content' }}
                                >
                                    {sampleImg && <SampleImage url={sampleImg} />}
                                    {isEmptyPointVisible && <EmptyPointMessage />}

                                    <CanvasTemplate
                                        roi={roi}
                                        state={state}
                                        onStateUpdate={handleStateUpdate}
                                        isAddPointEnabled={isAddPointEnabled}
                                        isLabelOptionsEnabled={isLabelOptionsEnabled}
                                    />
                                </div>
                            </TransformZoom>

                            <TemplateFooter />
                        </Grid>

                        {children}
                    </Flex>
                </HoveredProvider>
            </SelectedProvider>
        </ZoomProvider>
    );
};
