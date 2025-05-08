// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useMemo } from 'react';

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { isEmpty } from 'lodash-es';
import { useLocalStorage } from 'usehooks-ts';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { isAnomalous, isEmptyLabel, isExclusive, isGlobal, isLocal } from '../../../../../core/labels/utils';
import { isAnomalyDomain } from '../../../../../core/projects/domains';
import { useProjectIdentifier } from '../../../../../hooks/use-project-identifier/use-project-identifier';
import { LOCAL_STORAGE_KEYS } from '../../../../../shared/local-storage-keys';
import { getId, getIds, hasEqualId } from '../../../../../shared/utils';
import { AnnotationToolContext, ToolSettings, ToolType } from '../../../core/annotation-tool-context.interface';
import { getOutputFromTask } from '../../../providers/task-chain-provider/utils';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { LabelsHotkeys } from '../../labels/labels-hotkeys/labels-hotkeys.component';
import { LabelShortcutItem } from './label-shortcut-item/label-shortcut-item.component';
import { LabelsShortcutsPopover } from './labels-shortcuts-popover.component';

interface LabelsShortcutsProps {
    labels: Label[];
    isDisabled?: boolean;
    annotationToolContext: AnnotationToolContext;
}

const DEFAULT_SHORTCUT_NUMBER = 5;
const isSmartTool = (tool: ToolType) =>
    [ToolType.GrabcutTool, ToolType.RITMTool, ToolType.SSIMTool, ToolType.SegmentAnythingTool].includes(tool);

const isNotAnomalousNorExclusive = (label: Label) => !isAnomalous(label) && !isExclusive(label);

const hasNotAnomalousNorLocalLabels = (annotation: Annotation) =>
    annotation.labels.every((label) => !isAnomalous(label) && !isLocal(label));

export const LabelsShortcuts = ({
    labels,
    annotationToolContext,
    isDisabled = false,
}: LabelsShortcutsProps): JSX.Element => {
    const { selectedTask, tasks, setDefaultLabel } = useTask();
    const { projectId } = useProjectIdentifier();
    const {
        isDrawing,
        annotations: annotationsScene,
        addLabel,
        removeLabels,
        removeAnnotations,
    } = annotationToolContext.scene;
    const annotations = getOutputFromTask(annotationsScene, tasks, selectedTask);
    const pinningAllowed = labels.length > DEFAULT_SHORTCUT_NUMBER;
    const isDrawingSmartTool = isSmartTool(annotationToolContext.tool) && isDrawing;

    const [pinnedLabelsIds, setPinnedLabelsIds] = useLocalStorage<string[]>(
        `${LOCAL_STORAGE_KEYS.PINNED_LABELS}_${projectId}_${selectedTask?.domain || LOCAL_STORAGE_KEYS.ALL}`,
        labels.slice(0, DEFAULT_SHORTCUT_NUMBER).map(getId)
    );

    const pinnedLabels = pinnedLabelsIds
        .map((id) => labels.find(hasEqualId(id)))
        .filter((label): label is Label => label !== undefined);

    const smartToolHandler = (label: Label): void => {
        if (isLocal(label) || label.parentLabelId !== null) {
            setDefaultLabel(label);
        }

        annotationToolContext?.updateToolSettings(annotationToolContext.tool as keyof ToolSettings, {
            selectedLabel: label,
        });
    };

    const selectedAnnotations = useMemo(() => {
        return annotations.filter((annotation: Annotation) => annotation.isSelected);
    }, [annotations]);

    const clickHandler = useCallback(
        (label: Label): void => {
            const annotationsIds = getIds(selectedAnnotations);

            if (isLocal(label) || label.parentLabelId !== null) {
                setDefaultLabel(label);
            }

            if (isEmpty(selectedAnnotations)) {
                isGlobal(label) && addLabel(label, []);
                return;
            }

            const aSelectedAnnotationDoesNotHaveLabel = selectedAnnotations.some(
                (annotation) => !annotation.labels.some(hasEqualId(label.id))
            );

            if (aSelectedAnnotationDoesNotHaveLabel) {
                addLabel(label, annotationsIds);
            } else if (isEmptyLabel(label) && selectedAnnotations.every(hasNotAnomalousNorLocalLabels)) {
                removeAnnotations(selectedAnnotations);
            } else if (isEmptyLabel(label) || isNotAnomalousNorExclusive(label)) {
                removeLabels([label], annotationsIds);
            }
        },
        [addLabel, removeAnnotations, removeLabels, selectedAnnotations, setDefaultLabel]
    );

    const handleSelectLabelShortcut = (label: Label): void => {
        const isAnomaly = selectedTask?.domain && isAnomalyDomain(selectedTask?.domain);

        if (isAnomaly) {
            return clickHandler(label);
        }

        return isDrawingSmartTool ? smartToolHandler(label) : clickHandler(label);
    };

    return (
        <div aria-label='Label shortcuts' role='list'>
            {!isDisabled && (
                <LabelsHotkeys
                    labels={labels}
                    hotkeyHandler={handleSelectLabelShortcut}
                    annotationToolContext={annotationToolContext}
                />
            )}

            <Flex id='canvas-labels' gap='size-100' marginX='size-150'>
                <Flex minWidth={0} UNSAFE_style={{ overflow: 'auto' }} gap='size-100'>
                    {pinnedLabels.map((label, index, array) => (
                        <TooltipTrigger placement={'bottom'} key={label.id}>
                            <LabelShortcutItem
                                label={label}
                                onClick={handleSelectLabelShortcut}
                                isLast={index === array.length - 1}
                                isDisabled={isDisabled}
                            />
                            <Tooltip>
                                {`${label.name} ${label.hotkey ? `(${label.hotkey.toUpperCase()})` : ''}`}
                            </Tooltip>
                        </TooltipTrigger>
                    ))}
                </Flex>
                {pinningAllowed && (
                    <LabelsShortcutsPopover
                        onLabelClick={clickHandler}
                        pinnedLabelsIds={pinnedLabelsIds}
                        setPinnedLabelsIds={setPinnedLabelsIds}
                    />
                )}
            </Flex>
        </div>
    );
};
