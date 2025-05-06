// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { Flex, Grid } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';
import { useFocusManager } from 'react-aria';

import { Annotation } from '../../../../../core/annotations/annotation.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { MEDIA_ANNOTATION_STATUS } from '../../../../../core/media/base.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { useSetHoveredId } from '../../../../../providers/hovered-provider/hovered-provider.component';
import { Checkbox } from '../../../../../shared/components/checkbox/checkbox.component';
import { TaskLabelTreeSearchPopover } from '../../../../../shared/components/task-label-tree-search/task-label-tree-search-popover.component';
import { hasEqualId, runWhenTruthy } from '../../../../../shared/utils';
import { SelectionIndicator } from '../../../components/labels/label-search/selection-indicator.component';
import { AnnotationToolContext } from '../../../core/annotation-tool-context.interface';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { useROI } from '../../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { useTask } from '../../../providers/task-provider/task-provider.component';
import { getAvailableLabelsForAnnotation, getLabelsFromTask } from '../../labels/utils';
import { ListItemGrid } from '../../list-item-grid.component';
import { AnnotationLabelList } from '../annotation-label-list/annotation-label-list.component';
import { AnnotationListItemActions } from './annotation-list-item-actions.component';
import { AnnotationListItemMenu } from './annotation-list-item-menu.component';
import { AnnotationListItemThumbnail } from './annotation-list-item-thumbnail.component';

import classes from './annotation-list-item.module.scss';

interface AnnotationListItemContentProps {
    isLast?: boolean;
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
}

interface EditLabelsProps {
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
    close: () => void;
}

const InputThumbnail = ({
    annotation,
    annotationToolContext,
}: {
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
}) => {
    const { tasks, selectedTask } = useTask();
    const { image } = useROI();

    // Get all the labels from the current selected task or all the labels from the scene if no task is selected
    const availableLabels = getAvailableLabelsForAnnotation(
        annotationToolContext,
        annotation,
        tasks,
        selectedTask,
        image
    );

    const status = annotation.labels.some((label) => availableLabels.some(hasEqualId(label.id)))
        ? MEDIA_ANNOTATION_STATUS.ANNOTATED
        : MEDIA_ANNOTATION_STATUS.NONE;

    const { selectAnnotation, unselectAnnotation } = annotationToolContext.scene;
    const handleSelectAnnotation = (isSelected: boolean): void => {
        if (isSelected) {
            selectAnnotation(annotation.id);
        } else {
            unselectAnnotation(annotation.id);
        }
    };

    return (
        <AnnotationListItemThumbnail
            annotationId={annotation.id}
            isSelected={annotation.isSelected}
            annotationShape={annotation.shape}
            image={image}
            onSelectAnnotation={handleSelectAnnotation}
            status={status}
        />
    );
};

const EditLabels = ({ annotation, annotationToolContext, close }: EditLabelsProps) => {
    const { tasks, selectedTask } = useTask();
    const { addLabel, removeLabels } = annotationToolContext.scene;

    const onToggleLabel = runWhenTruthy((label: Label) => {
        if (annotation.labels.some(hasEqualId(label.id))) {
            removeLabels([label], [annotation.id]);
        } else {
            addLabel(label, [annotation.id]);
        }

        close();
    });

    return (
        <div style={{ minWidth: dimensionValue('size-3000') }}>
            <TaskLabelTreeSearchPopover
                isFocus
                tasks={tasks}
                id={annotation.id}
                selectedTask={selectedTask}
                onClick={onToggleLabel}
                onClose={close}
                textFieldProps={{
                    placeholder: 'Select label',
                    'aria-label': 'Select label',
                }}
                suffix={(label, state) => {
                    return (
                        <Flex marginStart={'auto'} alignItems={'center'}>
                            <SelectionIndicator
                                isHovered={state.isHovered}
                                isSelected={annotation.labels.some(({ id: labelId }) => labelId === label.id)}
                            />
                        </Flex>
                    );
                }}
            />
        </div>
    );
};

export const AnnotationListItemContent = ({
    isLast = false,
    annotation,
    annotationToolContext,
}: AnnotationListItemContentProps): JSX.Element => {
    const [selectLabel, setSelectLabel] = useState(false);

    const isSceneBusy = useIsSceneBusy();
    const focusManager = useFocusManager();
    const { isActiveLearningMode } = useAnnotatorMode();
    const { selectedTask, isTaskChainDomainSelected } = useTask();
    const setHoveredAnnotationId = useSetHoveredId();
    const { toggleLock, hideAnnotation, showAnnotation, selectAnnotation, removeAnnotations, unselectAnnotation } =
        annotationToolContext.scene;

    const isTaskChainSelectedClassification = isTaskChainDomainSelected(DOMAIN.CLASSIFICATION);
    const hasListMenu = isActiveLearningMode && !isTaskChainSelectedClassification;

    // From the current annotation, get only the labels that belong to the current selected task
    const annotationTaskLabels = getLabelsFromTask(annotation, selectedTask);
    const hasEmptyLabels = isEmpty(annotationTaskLabels);

    // Labels for the current annotation, either by task or all of them
    const labels = selectedTask ? annotationTaskLabels : annotation.labels;

    const textColor = annotation.isHidden ? classes.hiddenAnnotation : '';

    const handleSelectAnnotation = (isSelected: boolean): void => {
        if (isSelected) {
            selectAnnotation(annotation.id);
        } else {
            unselectAnnotation(annotation.id);
        }
    };

    const onChangeLock = (isLocked: boolean, annotationId: string): void => {
        toggleLock(!isLocked, annotationId);
    };

    const onFocus = (): void => {
        focusManager?.focusPrevious();
    };

    return (
        <ListItemGrid
            isLast={isLast}
            isSelected={annotation.isSelected}
            id={`annotation-list-item-${annotation.id}`}
            ariaLabel={`Annotation with id ${annotation.id}`}
            onHoverStart={() => setHoveredAnnotationId(annotation.id)}
            onHoverEnd={() => setHoveredAnnotationId(null)}
        >
            {!isTaskChainSelectedClassification && isActiveLearningMode && (
                <ListItemGrid.Checkbox>
                    <Checkbox
                        isEmphasized
                        onFocus={onFocus}
                        UNSAFE_className={textColor}
                        isSelected={annotation.isSelected}
                        isDisabled={isSceneBusy}
                        onChange={handleSelectAnnotation}
                        id={`annotation-list-checkbox-${annotation.id}`}
                        aria-label={`Select annotation ${annotation.id}`}
                    />
                </ListItemGrid.Checkbox>
            )}

            <ListItemGrid.Labels>
                <div
                    id={`annotation-list-annotation-labels-${annotation.id}`}
                    aria-label={`Labels of annotation with id ${annotation.id}`}
                    className={`${hasEmptyLabels ? classes.disabledText : textColor} ${classes.annotationLabels}`}
                    onDoubleClick={() => setSelectLabel(true)}
                    onClick={() => {
                        if (isTaskChainSelectedClassification) {
                            handleSelectAnnotation(true);
                            return;
                        }

                        if (isEmpty(annotation.labels)) {
                            setSelectLabel(true);
                        }
                    }}
                >
                    <Grid alignItems='center' gap='size-100' columns='auto 1fr'>
                        {isTaskChainSelectedClassification && (
                            <InputThumbnail annotation={annotation} annotationToolContext={annotationToolContext} />
                        )}

                        {selectLabel ? (
                            <EditLabels
                                annotation={annotation}
                                annotationToolContext={annotationToolContext}
                                close={() => setSelectLabel(false)}
                            />
                        ) : (
                            <AnnotationLabelList labels={labels} annotation={annotation} />
                        )}
                    </Grid>
                </div>
            </ListItemGrid.Labels>

            {hasListMenu && (
                <ListItemGrid.ListMenu>
                    <AnnotationListItemMenu
                        id={annotation.id}
                        isHidden={annotation.isHidden}
                        isLocked={annotation.isLocked}
                        isDisabled={isSceneBusy}
                        editLabels={() => setSelectLabel(true)}
                        show={() => showAnnotation(annotation.id)}
                        hide={() => hideAnnotation(annotation.id)}
                        remove={() => removeAnnotations([annotation])}
                        toggleLock={() => onChangeLock(annotation.isLocked, annotation.id)}
                    />
                </ListItemGrid.ListMenu>
            )}

            {!isTaskChainSelectedClassification && (
                <ListItemGrid.ActionsMenu>
                    <AnnotationListItemActions
                        textColor={textColor}
                        changeLock={onChangeLock}
                        isDisabled={isSceneBusy}
                        annotationId={annotation.id}
                        isHidden={annotation.isHidden}
                        isLocked={annotation.isLocked}
                        showAnnotation={showAnnotation}
                    />
                </ListItemGrid.ActionsMenu>
            )}
        </ListItemGrid>
    );
};
