// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { toast } from '@/components/toast/toast.component';
import { useZoom } from '@/components/zoom/zoom.provider';
import { useTranslation } from '@/i18n';
import { useProjectLabels } from 'hooks/use-project-labels.hook';
import { useProjectTask } from 'hooks/use-project-task.hook';
import { useHotkeys } from 'react-hotkeys-hook';

import { HOTKEYS } from '../../../shared/hotkeys-definition';
import { getMediaItemKey } from '../../../shared/media-item-utils';
import { isClassificationTask } from '../../../shared/task-type-guards';
import {
    useAnnotationCommands,
    useAnnotations,
    useIsAnnotatorReadOnly,
} from '../annotation-document-provider.component';
import { useIsAnnotatorSceneBusy } from '../hooks/use-is-annotator-scene-busy';
import { useSelectedAnnotations } from '../select-annotation-provider.component';
import { useSelectedMediaItem } from '../selected-media-item-provider.component';
import { useAnnotationsClipboard } from './annotations-clipboard-provider.component';
import { getCascadeStep, getCenterOfShape, getTranslateVector, preparePaste, toClipboardAnnotations } from './utils';

export const useCopyPasteAnnotations = () => {
    const { t } = useTranslation();
    const taskType = useProjectTask();
    const projectLabels = useProjectLabels();
    const isReadOnly = useIsAnnotatorReadOnly();
    const isSceneBusy = useIsAnnotatorSceneBusy();
    const { mediaItem, roi } = useSelectedMediaItem();
    const { annotations } = useAnnotations();
    const { addLabeledAnnotations } = useAnnotationCommands();
    const { selectedAnnotations, setSelectedAnnotations } = useSelectedAnnotations();
    const { scale } = useZoom();
    const { clipboard, setClipboard, pastedAnnotationGroups, setPastedAnnotationGroups } = useAnnotationsClipboard();

    const enabled = !isClassificationTask(taskType) && !isReadOnly && !isSceneBusy;
    const mediaKey = getMediaItemKey(mediaItem);

    useHotkeys(
        HOTKEYS.copyAnnotations,
        (event) => {
            const copied = toClipboardAnnotations(annotations.filter(({ id }) => selectedAnnotations.has(id)));

            if (copied.length === 0) return;

            event.preventDefault();
            setClipboard({ annotations: copied, sourceMediaKey: mediaKey });
            setPastedAnnotationGroups([]);
            toast({ type: 'info', message: t('annotator.copyPaste.copied', { count: copied.length }) });
        },
        { enabled, enableOnFormTags: ['option'] }
    );

    useHotkeys(
        HOTKEYS.pasteAnnotations,
        (event) => {
            if (clipboard === null) return;

            event.preventDefault();

            // Groups whose annotations are all gone (undone or deleted) no longer count towards the cascade.
            const existingIds = new Set(annotations.map(({ id }) => id));
            const sameMediaGroups = pastedAnnotationGroups.filter((group) => group.mediaKey === mediaKey);
            const cascade = sameMediaGroups.filter((group) => group.ids.some((id) => existingIds.has(id))).length;

            const step = (cascade + (clipboard.sourceMediaKey === mediaKey ? 1 : 0)) * getCascadeStep(scale);

            const { annotations: prepared, skipped } = preparePaste({
                clipboard: clipboard.annotations,
                validLabelIds: projectLabels.map(({ id }) => id),
                roi,
                offset: (shape) => {
                    const center = getCenterOfShape(shape);

                    return getTranslateVector(center, roi.width, roi.height, step);
                },
            });

            if (prepared.length > 0) {
                const ids = addLabeledAnnotations(prepared);

                setSelectedAnnotations(new Set(ids));
                setPastedAnnotationGroups([...sameMediaGroups, { mediaKey, ids }]);
            }

            const skippedCount = skipped.labelMissing + skipped.outsideImage;

            if (skippedCount > 0) {
                const reasons = [
                    skipped.labelMissing > 0 && t('annotator.copyPaste.labelMissing', { count: skipped.labelMissing }),
                    skipped.outsideImage > 0 && t('annotator.copyPaste.outsideImage', { count: skipped.outsideImage }),
                ].filter(Boolean);

                toast({
                    type: 'warning',
                    message: t('annotator.copyPaste.skippedSummary', {
                        pasted: prepared.length,
                        skipped: skippedCount,
                        reasons: reasons.join(', '),
                    }),
                });
            }
        },
        { enabled, enableOnFormTags: ['option'] }
    );
};
