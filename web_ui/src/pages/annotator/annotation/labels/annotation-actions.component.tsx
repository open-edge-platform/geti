// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import Cross from '@spectrum-icons/ui/CrossMedium';
import { motion } from 'framer-motion';

import { Edit } from '../../../../assets/icons';
import { Annotation } from '../../../../core/annotations/annotation.interface';
import { isAnomalyDomain, isClassificationDomain } from '../../../../core/projects/domains';
import { ANIMATION_PARAMETERS } from '../../../../shared/animation-parameters/animation-parameters';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { hasEqualId } from '../../../../shared/utils';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';

import classes from './labels.module.scss';

interface LabelActionsProps {
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
    setEditLabels: (editLabels: boolean) => void;
}

const useOnRemoveLabels = (annotationToolContext: AnnotationToolContext, annotation: Annotation) => {
    const { selectedTask } = useTask();
    const { roi } = useROI();
    const { removeAnnotations, removeLabels } = annotationToolContext.scene;

    if (selectedTask === null) {
        return () => removeAnnotations([annotation]);
    }

    if (isClassificationDomain(selectedTask.domain) || isAnomalyDomain(selectedTask.domain)) {
        const globalAnnotations = getGlobalAnnotations(annotationToolContext.scene.annotations, roi, selectedTask);

        if (!globalAnnotations.some(hasEqualId(annotation.id))) {
            return () => {
                removeAnnotations([annotation]);
            };
        }

        return () => {
            removeLabels([...annotation.labels], [annotation.id]);
        };
    }

    return () => {
        removeAnnotations([annotation]);
    };
};

export const AnnotationActions = ({
    annotation,
    annotationToolContext,
    setEditLabels,
}: LabelActionsProps): JSX.Element => {
    const onRemoveLabels = useOnRemoveLabels(annotationToolContext, annotation);

    const onEditLabels = () => {
        setEditLabels(true);
    };

    return (
        <motion.li
            variants={ANIMATION_PARAMETERS.FADE_ITEM}
            initial={'hidden'}
            animate={'visible'}
            exit={'hidden'}
            id={`edit`}
            className={[classes.annotationAction, classes.actionButtons].join(' ')}
        >
            <QuietActionButton onPress={onEditLabels} aria-label='Edit labels' UNSAFE_className={classes.iconWrapper}>
                <Edit />
            </QuietActionButton>

            {onRemoveLabels !== undefined && (
                <QuietActionButton
                    onPress={onRemoveLabels}
                    aria-label='Remove annotation'
                    UNSAFE_className={classes.iconWrapper}
                >
                    <Cross />
                </QuietActionButton>
            )}
        </motion.li>
    );
};
