// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Slider, Tooltip } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { PointPushPull } from '../../../../../assets/icons';
import BrushImg from '../../../../../assets/primary-tools/brush.webp';
import { TooltipWithDisableButton } from '../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { QuietToggleButton } from '../../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { DrawingToolsTooltip } from '../../../components/primary-toolbar/drawing-tools-tooltip.component';
import { ToolType } from '../../../core/annotation-tool-context.interface';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { PolygonSelectionToolbarProps } from '../../tools.interface';
import { blurActiveInput } from '../../utils';
import { useSelectingState } from '../selecting-state-provider.component';
import { SelectingToolLabel, SelectingToolType } from '../selecting-tool.enums';
import { getBrushMaxSize, MIN_BRUSH_SIZE } from '../utils';

import classes from '../selecting-tool.module.scss';

const PolygonSelectionToolbar = ({
    annotationToolContext,
    polygonAnnotations,
}: PolygonSelectionToolbarProps): JSX.Element => {
    const { updateToolSettings, getToolSettings } = annotationToolContext;
    const { activeTool, brushSize, setBrushSize, setIsBrushSizePreviewVisible } = useSelectingState();
    const { roi } = useROI();
    const maxBrushSize = getBrushMaxSize(roi);
    const isBrushToolDisabled = polygonAnnotations.length > 1;
    const selectionSettings = getToolSettings(ToolType.SelectTool);

    if (isEmpty(polygonAnnotations)) return <></>;

    return (
        <>
            <TooltipWithDisableButton
                placement={'bottom'}
                disabledTooltip={'Brush tool is disabled for multi-selection mode'}
                activeTooltip={
                    <Tooltip UNSAFE_className={classes.drawingToolsTooltips}>
                        <DrawingToolsTooltip
                            img={BrushImg}
                            title='Brush tool'
                            url={`guide/annotations/annotation-tools.html#selector-tool`}
                            description='Edit selected polygon using brush by pushing vertices inwards or outwards.'
                        />
                    </Tooltip>
                }
            >
                <QuietToggleButton
                    aria-label={SelectingToolLabel.BrushTool}
                    isDisabled={isBrushToolDisabled}
                    id={SelectingToolType.BrushTool.toString()}
                    isSelected={activeTool === SelectingToolType.BrushTool}
                    onPress={() => {
                        const initialBrushSize = selectionSettings.brushSize ?? Math.round(maxBrushSize * 0.1);

                        updateToolSettings(ToolType.SelectTool, {
                            tool: SelectingToolType.BrushTool,
                            brushSize: initialBrushSize,
                        });

                        setBrushSize(initialBrushSize);
                    }}
                >
                    <PointPushPull />
                </QuietToggleButton>
            </TooltipWithDisableButton>

            {activeTool === SelectingToolType.BrushTool && (
                <Slider
                    minValue={MIN_BRUSH_SIZE}
                    value={brushSize}
                    labelPosition='side'
                    aria-label='brush-size'
                    label={'Brush size'}
                    onChange={(size) => {
                        setBrushSize(size);
                        setIsBrushSizePreviewVisible(true);
                    }}
                    onChangeEnd={(size) => {
                        setIsBrushSizePreviewVisible(false);
                        updateToolSettings(ToolType.SelectTool, {
                            tool: SelectingToolType.BrushTool,
                            brushSize: size,
                        });
                        blurActiveInput(true);
                    }}
                    maxValue={maxBrushSize}
                />
            )}
        </>
    );
};

export default PolygonSelectionToolbar;
