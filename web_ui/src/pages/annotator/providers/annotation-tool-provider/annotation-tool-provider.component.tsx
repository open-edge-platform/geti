// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';

import { Task } from '../../../../core/projects/task.interface';
import { AnnotationScene } from '../../core/annotation-scene.interface';
import {
    AnnotationToolContext as AnnotationToolContextProps,
    TaskMode,
    ToolSettings,
    ToolSpecificSettings,
    ToolsSettingsPerTask,
    ToolType,
    UpdateToolSettings,
} from '../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../hooks/use-annotator-mode';
import { SelectingToolType } from '../../tools/selecting-tool/selecting-tool.enums';
import { useAnnotationScene } from '../annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotator } from '../annotator-provider/annotator-provider.component';
import { defaultToolForProject } from '../annotator-provider/utils';
import { useTask } from '../task-provider/task-provider.component';
import { DEFAULT_TOOLS_SETTINGS } from './tools-settings';

type LastUsedTool = Record<TaskMode, ToolType>;

interface AnnotationToolProviderProps {
    children: ReactNode;
}

const AnnotationToolContext = createContext<AnnotationToolContextProps | undefined>(undefined);

const useToolsSettings = (activeDomain: TaskMode) => {
    const [toolsSettings, setToolsSettings] = useState<ToolsSettingsPerTask>(() => {
        return {
            [activeDomain]: new Map(DEFAULT_TOOLS_SETTINGS),
        } as ToolsSettingsPerTask;
    });

    const getToolSettings = useCallback(
        <T extends keyof ToolSettings>(type: T): ToolSpecificSettings<T> => {
            const settings = toolsSettings[activeDomain] ?? toolsSettings['All'];

            return settings.get(type) as ToolSpecificSettings<T>;
        },
        [toolsSettings, activeDomain]
    );

    const updateToolSettings = useCallback(
        <T extends keyof ToolSettings>(type: T, settings: UpdateToolSettings<T>): void => {
            setToolsSettings((prevToolsSettings) => {
                const prevSettings = prevToolsSettings[activeDomain]
                    ? prevToolsSettings[activeDomain].get(type)
                    : undefined;

                if (prevSettings === undefined) {
                    return prevToolsSettings;
                }

                return {
                    ...prevToolsSettings,
                    [activeDomain]: new Map(
                        prevToolsSettings[activeDomain].set(type, { ...prevSettings, ...settings })
                    ),
                };
            });
        },
        [activeDomain]
    );

    return {
        toolsSettings,
        setToolsSettings,
        getToolSettings,
        updateToolSettings,
    };
};

const getDomain = (newSelectedTask: Task | null): TaskMode => newSelectedTask?.domain ?? 'All';

export const useActiveTool = () => {
    const { isActiveLearningMode } = useAnnotatorMode();
    const { activeTool, setActiveTool } = useAnnotator();

    const { tasks, selectedTask } = useTask();
    const activeDomain = useMemo(() => getDomain(selectedTask), [selectedTask]);

    const lastUsedTool = useRef<LastUsedTool>({} as LastUsedTool);
    const toolsSettingsContext = useToolsSettings(activeDomain);

    const updateLastUsedTool = (domain: TaskMode, tool: ToolType): void => {
        lastUsedTool.current = { ...lastUsedTool.current, [domain]: tool };
    };

    const resetSelectionTool = () => {
        toolsSettingsContext.updateToolSettings(ToolType.SelectTool, {
            tool: SelectingToolType.SelectionTool,
            stampedAnnotation: null,
        });
    };

    const handleSetActiveTool = (domain: TaskMode, tool: ToolType, updateLastTool = true) => {
        updateLastTool && updateLastUsedTool(domain, tool);

        setActiveTool(tool);
    };

    const toggleTool = useCallback(
        (tool: ToolType, updateLastTool = true): void => {
            if (tool === ToolType.SelectTool) {
                resetSelectionTool();
            }

            handleSetActiveTool(getDomain(selectedTask), tool, updateLastTool);
        },

        // eslint-disable-next-line react-hooks/exhaustive-deps
        [setActiveTool, selectedTask]
    );

    const toggleToolOnTaskChange = (newSelectedTask: Task | null): void => {
        const newSelectedDomain = getDomain(newSelectedTask);
        const newActiveDomains =
            newSelectedTask === null ? tasks.map(({ domain }) => domain) : [newSelectedTask.domain];

        const tool = lastUsedTool.current[newSelectedDomain] ?? defaultToolForProject(newActiveDomains);

        if (toolsSettingsContext.toolsSettings[newSelectedDomain] === undefined) {
            toolsSettingsContext.setToolsSettings((prevToolsSettings) => ({
                ...prevToolsSettings,
                [newSelectedDomain]: DEFAULT_TOOLS_SETTINGS,
            }));
        }

        handleSetActiveTool(
            newSelectedDomain,
            isActiveLearningMode ? tool : ToolType.Explanation,
            isActiveLearningMode
        );
    };

    useEffect(() => {
        // NOTE: We initialize active tool in the AnnotatorProvider. Therefore, we need to update lastUsedTool after
        // initialization. The future goal is to move active tool initialization to AnnotationToolProvider (here).
        // Once it's done we can remove this effect.

        isActiveLearningMode && updateLastUsedTool(getDomain(selectedTask), activeTool);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return [activeTool, toggleTool, toggleToolOnTaskChange, toolsSettingsContext] as const;
};

export const AnnotationToolProvider = ({ children }: AnnotationToolProviderProps): JSX.Element => {
    const scene: AnnotationScene = useAnnotationScene();

    const [activeTool, toggleTool, toggleToolOnTaskChange, { toolsSettings, getToolSettings, updateToolSettings }] =
        useActiveTool();

    const value: AnnotationToolContextProps = {
        scene,
        toolsSettings,
        tool: activeTool,
        toggleTool,
        toggleToolOnTaskChange,
        getToolSettings,
        updateToolSettings,
    };

    return <AnnotationToolContext.Provider value={value}>{children}</AnnotationToolContext.Provider>;
};

export const useAnnotationToolContext = (): AnnotationToolContextProps => {
    const context = useContext(AnnotationToolContext);

    if (context === undefined) {
        throw new MissingProviderError('useAnnotationToolContext', 'AnnotationToolProvider');
    }

    return context;
};
