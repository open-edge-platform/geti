// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { Flex, Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';

import { PointSelector } from '../../../../assets/icons';
import { Annotation } from '../../../../core/annotations/annotation.interface';
import { isClassificationDomain, isSegmentationDomain } from '../../../../core/projects/domains';
import { isKeypointTask } from '../../../../core/projects/utils';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { QuietToggleButton } from '../../../../shared/components/quiet-button/quiet-toggle-button.component';
import { useSelectedAnnotations } from '../../hooks/use-selected-annotations.hook';
import { getOutputFromTask } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import PolygonSelectionToolbar from './components/polygon-selection-toolbar.component';
import { useSelectingState } from './selecting-state-provider.component';
import { SelectingToolLabel, SelectingToolType } from './selecting-tool.enums';
import { StampToolButton } from './stamp-tool/stamp-tool-button.component';
import { getSelectedPolygonAnnotations } from './utils';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { tasks, selectedTask } = useTask();
    const {
        scene: { annotations },
    } = annotationToolContext;

    const { activeTool, setActiveTool, stampAnnotations } = useSelectingState();

    const selectedAnnotations = useSelectedAnnotations();

    const isNotKeypointTask = !tasks.every(isKeypointTask);
    const isNotClassificationTask = !(selectedTask && isClassificationDomain(selectedTask.domain));

    const isStampButtonVisible =
        isNotKeypointTask && isNotClassificationTask && (!isEmpty(selectedAnnotations) || !isEmpty(stampAnnotations));

    const showSubTools =
        (selectedTask === null && tasks.some(({ domain }) => isSegmentationDomain(domain))) ||
        (selectedTask && isSegmentationDomain(selectedTask.domain));
    const polygonAnnotations = getSelectedPolygonAnnotations(
        getOutputFromTask(annotations, tasks, selectedTask) as Annotation[]
    );

    useEffect(() => {
        // Deselect brushing tool when there is more than one polygon selected
        const isBrushToolActive = activeTool === SelectingToolType.BrushTool;

        if (polygonAnnotations.length !== 1 && isBrushToolActive) {
            setActiveTool(SelectingToolType.SelectionTool);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [polygonAnnotations.length]);

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Selector</Text>
            <Divider orientation='vertical' size='S' />

            {showSubTools && (
                <>
                    <TooltipTrigger placement={'bottom'}>
                        <QuietToggleButton
                            id={SelectingToolType.SelectionTool.toString()}
                            aria-label={SelectingToolLabel.SelectionTool}
                            isSelected={activeTool === SelectingToolType.SelectionTool}
                            onPress={() => {
                                activeTool !== SelectingToolType.SelectionTool &&
                                    setActiveTool(SelectingToolType.SelectionTool);
                            }}
                        >
                            <PointSelector />
                        </QuietToggleButton>
                        <Tooltip>{SelectingToolLabel.SelectionTool}</Tooltip>
                    </TooltipTrigger>

                    <PolygonSelectionToolbar
                        polygonAnnotations={polygonAnnotations}
                        annotationToolContext={annotationToolContext}
                    />
                </>
            )}
            {showSubTools && <Divider orientation='vertical' size='S' />}
            <StampToolButton isVisible={isStampButtonVisible} selectedAnnotations={selectedAnnotations} />
        </Flex>
    );
};
