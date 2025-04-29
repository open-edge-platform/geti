// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    createContext,
    Dispatch,
    MutableRefObject,
    SetStateAction,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState,
} from 'react';

import isNil from 'lodash/isNil';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { getCenterOfTheAnnotations } from '../../../../core/annotations/math';
import { Point } from '../../../../core/annotations/shapes.interface';
import { MissingProviderError } from '../../../../shared/missing-provider-error';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useAnnotationScene } from '../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { StateProviderProps } from '../tools.interface';
import { SelectingToolType } from './selecting-tool.enums';
import { MIN_BRUSH_SIZE } from './utils';

interface SelectingStateContextProps {
    brushSize: number;
    isBrushSizePreviewVisible: boolean;
    activeTool: SelectingToolType;
    setBrushSize: Dispatch<SetStateAction<number>>;
    foregroundMarkers: MutableRefObject<Point[][]>;
    setActiveTool: (tool: SelectingToolType) => void;
    setIsBrushSizePreviewVisible: Dispatch<SetStateAction<boolean>>;
    stampAnnotations: Annotation[];
    handleCreateStamp: (selectedAnnotations: Annotation[]) => void;
    handleCancelStamp: () => void;
    centerOfTheStampAnnotations: Point;
}

const SelectingStateContext = createContext<SelectingStateContextProps | undefined>(undefined);

const INITIAL_ACTIVE_TOOL = SelectingToolType.SelectionTool;
const INITIAL_POINT: Point = { x: 0, y: 0 };

export const SelectingStateProvider = ({ children }: StateProviderProps): JSX.Element => {
    const { getToolSettings, updateToolSettings } = useAnnotationToolContext();
    const selectionSettings = getToolSettings(ToolType.SelectTool);

    const foregroundMarkers = useRef<Point[][]>([]);
    const [brushSize, setBrushSize] = useState<number>(
        selectionSettings.brushSize !== null ? selectionSettings.brushSize : MIN_BRUSH_SIZE
    );
    const [isBrushSizePreviewVisible, setIsBrushSizePreviewVisible] = useState(false);
    const { unselectAllAnnotations } = useAnnotationScene();

    const [stampAnnotations, setStampAnnotations] = useState<Annotation[]>(
        selectionSettings.stampedAnnotation !== null ? [selectionSettings.stampedAnnotation] : []
    );

    const centerOfTheStampAnnotations = useRef<Point>(
        isNil(selectionSettings.stampedAnnotation)
            ? INITIAL_POINT
            : getCenterOfTheAnnotations([selectionSettings.stampedAnnotation.shape])
    );

    const setActiveTool = useCallback((tool: SelectingToolType) => {
        updateToolSettings(ToolType.SelectTool, { tool });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCreateStamp = useCallback((selectedAnnotations: Annotation[]): void => {
        setActiveTool(SelectingToolType.StampTool);

        centerOfTheStampAnnotations.current = getCenterOfTheAnnotations(selectedAnnotations.map(({ shape }) => shape));
        setStampAnnotations(selectedAnnotations);
        updateToolSettings(ToolType.SelectTool, { stampedAnnotation: selectedAnnotations[0] });

        unselectAllAnnotations();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCancelStamp = useCallback((): void => {
        setActiveTool(INITIAL_ACTIVE_TOOL);

        centerOfTheStampAnnotations.current = INITIAL_POINT;
        setStampAnnotations([]);
        updateToolSettings(ToolType.SelectTool, { stampedAnnotation: null });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        // If the stamp tool was active and then the selection tool type changed, we need to reset stamp config.
        if (selectionSettings.tool !== SelectingToolType.StampTool) {
            centerOfTheStampAnnotations.current = INITIAL_POINT;
            setStampAnnotations([]);
            updateToolSettings(ToolType.SelectTool, { stampedAnnotation: null });
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectionSettings.tool]);

    return (
        <SelectingStateContext.Provider
            value={{
                activeTool: selectionSettings.tool,
                brushSize,
                setActiveTool,
                setBrushSize,
                foregroundMarkers,
                isBrushSizePreviewVisible,
                setIsBrushSizePreviewVisible,

                stampAnnotations,
                handleCreateStamp,
                handleCancelStamp,
                centerOfTheStampAnnotations: centerOfTheStampAnnotations.current,
            }}
        >
            {children}
        </SelectingStateContext.Provider>
    );
};

export const useSelectingState = (): SelectingStateContextProps => {
    const context = useContext(SelectingStateContext);

    if (context === undefined) {
        throw new MissingProviderError('SelectingState', 'SelectingStateProvider');
    }

    return context;
};

export const useIsSelectionToolActive = (tool: SelectingToolType): boolean => {
    const context = useContext(SelectingStateContext);

    // in case we try to use that context when selection tool provider is not mounted, we want to return that
    // tool is not active
    if (context === undefined) {
        return false;
    }

    return context.activeTool === tool;
};
