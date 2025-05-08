// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useState } from 'react';

import { Grid, repeat, Tooltip, TooltipTrigger, View } from '@adobe/react-spectrum';
import { AnimatePresence, motion } from 'framer-motion';
import { isEmpty } from 'lodash-es';

import { Delete } from '../../../../../assets/icons';
import { ANIMATION_PARAMETERS } from '../../../../../shared/animation-parameters/animation-parameters';
import { Checkbox } from '../../../../../shared/components/checkbox/checkbox.component';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { hasEqualId, hasEqualSize } from '../../../../../shared/utils';
import { useAnnotatorMode } from '../../../hooks/use-annotator-mode';
import { useIsSceneBusy } from '../../../hooks/use-annotator-scene-interaction-state.hook';
import { useLocalAnnotations } from '../../../hooks/use-local-annotations.hooks';
import { useDeleteKeyboardShortcut } from '../../../hot-keys/use-delete-keyboard-shortcut/use-delete-keyboard-shortcut';
import { useToggleSelectAllKeyboardShortcut } from '../../../hot-keys/use-toggle-select-all-keyboard-shortcut/use-toggle-select-all-keyboard-shortcut';
import { useAnnotationScene } from '../../../providers/annotation-scene-provider/annotation-scene-provider.component';
import { useAnnotationToolContext } from '../../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { blurActiveInput } from '../../../tools/utils';
import { ToggleLockButton } from '../../toggle-lock-button/toggle-lock-button.component';
import { ToggleVisibilityButton } from '../../toggle-visibility-button/toggle-visibility-button.component';
import { BulkAssignLabel } from './bulk-assign-labels.component';

export const AnnotationListActions = (): JSX.Element => {
    const {
        removeAnnotations,
        setSelectedAnnotations,
        setHiddenAnnotations,
        setLockedAnnotations,
        hasShapePointSelected,
    } = useAnnotationScene();

    const isSceneBusy = useIsSceneBusy();
    const annotations = useLocalAnnotations();
    const annotationToolContext = useAnnotationToolContext();
    const { isActiveLearningMode } = useAnnotatorMode();

    const [isHidden, setIsHidden] = useState<boolean>(false);
    const [isLocked, setIsLocked] = useState<boolean>(false);

    const hasNoAnnotations = isEmpty(annotations);
    const selectedAnnotations = annotations.filter(({ isSelected }) => isSelected);
    const hasSelectedAnnotations = !isEmpty(selectedAnnotations);
    const allAnnotationsSelected = useMemo(
        () => hasEqualSize(selectedAnnotations, annotations),
        [selectedAnnotations, annotations]
    );

    const selectAllAnnotationsAriaLabel = `
        ${selectedAnnotations.length} out of ${annotations.length} annotations selected
    `;

    const removeSelectedAnnotations = () => {
        removeAnnotations(selectedAnnotations);
    };

    const changeVisibility = (): void => {
        setHiddenAnnotations((annotation) => {
            if (selectedAnnotations.some(hasEqualId(annotation.id))) {
                return !isHidden;
            }

            return annotation.isHidden;
        });
    };

    const changeLock = (): void => {
        setLockedAnnotations((annotation) => {
            if (selectedAnnotations.some(hasEqualId(annotation.id))) {
                return !isLocked;
            }

            return annotation.isLocked;
        });
    };

    const setOutputAnnotationSelection = (isSelected: boolean): void => {
        setSelectedAnnotations((annotation) => {
            if (annotations.some(hasEqualId(annotation.id))) {
                return isSelected;
            }

            return annotation.isSelected;
        });
    };

    useEffect(() => {
        if (!isEmpty(selectedAnnotations)) {
            setIsHidden(selectedAnnotations.some((annotation) => annotation.isHidden));
            setIsLocked(selectedAnnotations.some((annotation) => annotation.isLocked));
        }
    }, [selectedAnnotations]);

    useToggleSelectAllKeyboardShortcut(setOutputAnnotationSelection);
    useDeleteKeyboardShortcut(removeAnnotations, hasShapePointSelected, selectedAnnotations);

    return (
        <>
            <TooltipTrigger placement={'bottom'}>
                <Checkbox
                    isEmphasized
                    key='select-annotations'
                    UNSAFE_style={{ padding: 0 }}
                    onFocusChange={blurActiveInput}
                    id={'annotations-list-select-all'}
                    data-testid={'annotations-list-select-all'}
                    aria-label={selectAllAnnotationsAriaLabel}
                    isSelected={hasSelectedAnnotations}
                    isDisabled={hasNoAnnotations || isSceneBusy || !isActiveLearningMode}
                    onChange={setOutputAnnotationSelection}
                    isIndeterminate={!allAnnotationsSelected && hasSelectedAnnotations}
                />
                <Tooltip>Select all annotations</Tooltip>
            </TooltipTrigger>

            <AnimatePresence>
                {hasSelectedAnnotations && (
                    <View width={'100%'}>
                        <motion.div variants={ANIMATION_PARAMETERS.FADE_ITEM} initial={'hidden'} animate={'visible'}>
                            <Grid
                                gap='size-100'
                                autoRows='size-400'
                                height={'fit-content'}
                                columns={repeat('auto-fit', 'size-400')}
                                justifyContent={'end'}
                            >
                                <TooltipTrigger placement={'bottom'}>
                                    <BulkAssignLabel
                                        key='assign-label'
                                        selectedAnnotations={selectedAnnotations}
                                        annotationToolContext={annotationToolContext}
                                        isDisabled={isSceneBusy}
                                    />
                                    <Tooltip>Assign label</Tooltip>
                                </TooltipTrigger>

                                <TooltipTrigger placement={'bottom'}>
                                    <ToggleVisibilityButton
                                        key='toggle-visibility'
                                        onPress={changeVisibility}
                                        isHidden={isHidden}
                                        isDisabled={isSceneBusy}
                                        id={'selected-annotations'}
                                    />
                                    <Tooltip>Toggle visibility</Tooltip>
                                </TooltipTrigger>

                                <TooltipTrigger placement={'bottom'}>
                                    <QuietActionButton
                                        key='delete-annotations'
                                        onPress={removeSelectedAnnotations}
                                        isDisabled={isSceneBusy}
                                        id={'annotations-list-delete-selected'}
                                        data-testid={'annotations-list-delete-selected'}
                                        aria-label='Delete selected annotations'
                                    >
                                        <Delete />
                                    </QuietActionButton>
                                    <Tooltip>Delete annotations</Tooltip>
                                </TooltipTrigger>

                                <TooltipTrigger placement={'bottom'}>
                                    <ToggleLockButton
                                        key='lock-annotations'
                                        id={'selected-annotations'}
                                        onPress={changeLock}
                                        isLocked={isLocked}
                                        isDisabled={isSceneBusy}
                                    />
                                    <Tooltip>Lock annotations</Tooltip>
                                </TooltipTrigger>
                            </Grid>
                        </motion.div>
                    </View>
                )}
            </AnimatePresence>
        </>
    );
};
