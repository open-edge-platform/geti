// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key, useEffect } from 'react';

import { Flex } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';
import { useMediaQuery } from '@react-spectrum/utils';
import { isEmpty } from 'lodash-es';

import { filterOutExclusiveLabel } from '../../../../core/labels/utils';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { AcceptRejectButtonGroup } from '../../components/accept-reject-button-group/accept-reject-button-group.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { BrushSizeSlider } from './brush-size-slider.component';
import { LabelPicker } from './label-picker.component';
import { SensitivitySlider } from './sensitivity-slider.component';
import {
    BACKGROUND_LABEL,
    brushSizeSliderConfig,
    formatAndAddAnnotations,
    getMaxSensitivityForImage,
    SENSITIVITY_SLIDER_CONFIG,
    WATERSHED_SUPPORTED_DOMAINS,
} from './utils';
import { useWatershedState } from './watershed-state-provider.component';
import { WatershedLabel } from './watershed-tool.interface';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { tasks } = useTask();
    const { setIsDrawing } = useAnnotationScene();
    const { image } = useROI();
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const { shapes, setShapes, undoRedoActions, rejectAnnotation } = useWatershedState();
    const { updateToolSettings, getToolSettings, scene } = annotationToolContext;

    const taskLabels = tasks
        .filter((task) => WATERSHED_SUPPORTED_DOMAINS.includes(task.domain))
        .flatMap((task) => task.labels);

    const isAcceptButtonDisabled = isEmpty(shapes.watershedPolygons);
    const shouldShowConfirmCancel = !isAcceptButtonDisabled || !isEmpty(shapes.markers);

    const maxSensitivityForImage = getMaxSensitivityForImage(image);

    useEffect(() => {
        if (shouldShowConfirmCancel) {
            setIsDrawing(true);
        }
    }, [setIsDrawing, shouldShowConfirmCancel]);

    useEffect(() => {
        return () => {
            setIsDrawing(false);
        };
    }, [setIsDrawing]);

    const [backgroundLabel, ...availableLabels]: WatershedLabel[] = [
        { markerId: 1, label: BACKGROUND_LABEL },
        ...filterOutExclusiveLabel(taskLabels).map((label, idx) => ({
            markerId: idx + 2,
            label,
        })),
    ];

    const settings = getToolSettings(ToolType.WatershedTool);

    const handleSelectLabel = (key: Key): void => {
        const selectedLabel = [backgroundLabel, ...availableLabels].find(({ label }) => label.name === `${key}`);

        if (selectedLabel) {
            updateToolSettings(ToolType.WatershedTool, {
                label: selectedLabel,
            });
        }
    };

    const handleSelectSensitivity = (key: Key): void => {
        updateToolSettings(ToolType.WatershedTool, {
            brushSize: settings.brushSize,
            label: settings.label,
            sensitivity: Number(key) ?? SENSITIVITY_SLIDER_CONFIG.min,
        });
    };

    const updateBrushSize = (value: number): void => {
        updateToolSettings(ToolType.WatershedTool, {
            brushSize: value,
            label: settings.label,
            sensitivity: settings.sensitivity,
        });
    };

    const handleConfirmAnnotation = (): void => {
        formatAndAddAnnotations(shapes.watershedPolygons, scene.addAnnotations);

        // After we make an annotation we should reset the markers and polygons
        setShapes({ markers: [], watershedPolygons: [] });

        // Reset the undoRedo state
        undoRedoActions.reset();
        setIsDrawing(false);
    };

    const handleCancelAnnotation = async (): Promise<void> => {
        await rejectAnnotation();

        setIsDrawing(false);
    };

    useEffect(() => {
        // Update the default label on tool settings upon mount
        updateToolSettings(ToolType.WatershedTool, {
            brushSize: settings.brushSize || brushSizeSliderConfig.defaultValue,
            label: availableLabels[0],
            sensitivity: settings.sensitivity,
        });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            {isLargeSize && (
                <>
                    <Text>Object coloring</Text>
                    <Divider orientation='vertical' size='S' />
                </>
            )}

            <Flex alignItems='center' gap='size-100'>
                <LabelPicker
                    availableLabels={availableLabels}
                    backgroundLabel={backgroundLabel}
                    handleSelectLabel={handleSelectLabel}
                />
            </Flex>

            <Divider orientation='vertical' size='S' />

            <SensitivitySlider
                value={settings.sensitivity}
                max={maxSensitivityForImage}
                onSelectSensitivity={handleSelectSensitivity}
            />

            <Divider orientation='vertical' size='S' />

            <BrushSizeSlider updateBrushSize={updateBrushSize} />

            {shouldShowConfirmCancel && <Divider orientation='vertical' size='S' />}

            <AcceptRejectButtonGroup
                id={'watershed'}
                isAcceptButtonDisabled={isAcceptButtonDisabled}
                shouldShowButtons={shouldShowConfirmCancel}
                handleAcceptAnnotation={handleConfirmAnnotation}
                handleRejectAnnotation={handleCancelAnnotation}
            />
        </Flex>
    );
};
