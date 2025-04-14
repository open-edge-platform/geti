// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Provider } from '@adobe/react-spectrum';
import { Flex } from '@react-spectrum/layout';
import { View } from '@react-spectrum/view';
import partition from 'lodash/partition';

import { Divider } from '../../../../shared/components/divider/divider.component';
import { HelpActions } from '../../../../shared/components/header/header-actions/help-actions/help-actions.component';
import { isNonEmptyArray } from '../../../../shared/utils';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { ToolAnnotationContextProps } from '../../tools/tools.interface';
import { ActionButtons } from './action-buttons.component';
import { DrawingToolButtons } from './drawing-tool-buttons.component';
import { SelectToolButton } from './select-tool-button.component';
import { UndoRedoButtons } from './undo-redo-buttons.component';
import { useDisabledTools, useDrawingTools } from './utils';

import classes from './primaryToolBar.module.scss';

const BASE_TOOLS = [
    ToolType.BoxTool,
    ToolType.CircleTool,
    ToolType.PolygonTool,
    ToolType.RotatedBoxTool,
    ToolType.KeypointTool,
];

const AnnotationTools = ({ annotationToolContext }: ToolAnnotationContextProps) => {
    const isSceneBusy = useIsSceneBusy();
    const { activeDomains } = useTask();
    const drawingTools = useDrawingTools(activeDomains);

    const { tool, toggleTool } = annotationToolContext;
    const disabledTools = useDisabledTools(annotationToolContext) || isSceneBusy;
    const [baseTool, otherTools] = partition(drawingTools, ({ type }) => BASE_TOOLS.includes(type));

    return (
        <>
            <View>
                <SelectToolButton activeTool={tool} setActiveTool={toggleTool} />
            </View>
            <Divider size='S' marginY='size-100' />

            {isNonEmptyArray(baseTool) && (
                <>
                    <DrawingToolButtons
                        id='base'
                        activeTool={tool}
                        setActiveTool={toggleTool}
                        drawingTools={baseTool}
                        isDisabled={disabledTools}
                    />
                    <Divider size='S' marginY='size-100' />
                </>
            )}

            {isNonEmptyArray(otherTools) && (
                <>
                    <DrawingToolButtons
                        id='smart'
                        activeTool={tool}
                        setActiveTool={toggleTool}
                        drawingTools={otherTools}
                        isDisabled={disabledTools}
                    />
                    <Divider size='S' marginY='size-100' />
                </>
            )}

            <UndoRedoButtons isDisabled={disabledTools} />
            <Divider size='S' marginY='size-100' />
        </>
    );
};

export const PrimaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps): JSX.Element => {
    const { isActiveLearningMode } = useAnnotatorMode();

    return (
        <View
            id={'annotator-toolbar'}
            padding={'size-100'}
            gridArea={'primaryToolbar'}
            backgroundColor={'gray-200'}
            overflow={'hidden auto'}
        >
            <Provider isQuiet>
                <Flex
                    height='100%'
                    direction='column'
                    alignItems='center'
                    justify-content='center'
                    UNSAFE_className={classes.primaryToolBar}
                >
                    {isActiveLearningMode && <AnnotationTools annotationToolContext={annotationToolContext} />}

                    <ActionButtons annotationToolContext={annotationToolContext} />
                    <View marginTop={'auto'}>
                        <HelpActions key='docs-actions' isDarkMode />
                    </View>
                </Flex>
            </Provider>
        </View>
    );
};
